from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from agents.debugger_agent import apply_patch_batch
from agents.exporter_agent import build_final_manifest, export_project
from agents.runtime import AgentRuntime
from contracts.export import ExportRequest, ExportResult, ExportTarget
from contracts.manifest import FinalManifest
from contracts.godot_patch import PatchBatch
from contracts.run_state import OrchestrationNode, RunMode, RunState, RunStatus
from contracts.validation import ValidationIssue, ValidationReport, ValidationSeverity, ValidationStage
from orchestration._compat import model_copy_compat


REQUIRED_PROJECT_FILES: tuple[str, ...] = (
    "project.godot",
    "scenes/Main.tscn",
    "scripts/main.gd",
)


@dataclass(frozen=True)
class GameCreationResult:
    run_id: str
    project_dir: Path
    status: RunStatus
    retry_count: int
    validation_report: ValidationReport
    export_result: Optional[ExportResult]
    final_manifest_path: Optional[Path]
    run_bundle_path: Path


class GameCreationEngine:
    def __init__(self, workspace_root: Path | str, runtime: AgentRuntime | None = None) -> None:
        self.workspace_root = Path(workspace_root)
        self.runtime = runtime or AgentRuntime()

    def create_from_prompt(
        self,
        prompt: str,
        mode: RunMode = RunMode.STANDALONE,
        *,
        enable_export: bool = False,
        strict_export: bool = False,
        godot_exe: str | None = None,
    ) -> GameCreationResult:
        spec, task_graph, _ = self.runtime.invoke_project_manager(prompt)
        run_id = self._build_run_id()

        spec = model_copy_compat(spec, update={"run_id": run_id, "mode": mode})
        task_graph = model_copy_compat(task_graph, update={"run_id": run_id})

        project_dir = self._bootstrap_project(spec.selected_template, run_id)
        state = RunState(
            run_id=run_id,
            prompt=prompt,
            mode=mode,
            workspace_dir=str(project_dir),
            current_node=OrchestrationNode.INTAKE,
            status=RunStatus.INTAKE,
            max_retries=3,
        )

        state, _ = self.runtime.invoke_coordinator(state, task_graph)
        state, _ = self.runtime.invoke_coordinator(state, task_graph)

        patch_batch, _ = self.runtime.invoke_coding_agent(task_graph)
        last_report: ValidationReport | None = None
        applied_batches: list[PatchBatch] = []

        while True:
            apply_patch_batch(str(project_dir), patch_batch)
            applied_batches.append(patch_batch)
            attempt = state.retry_count + 1
            last_report = self._validate_project_structure(run_id=run_id, attempt=attempt, project_dir=project_dir)
            state, _ = self.runtime.invoke_coordinator(state, task_graph, validation_report=last_report)

            if state.status == RunStatus.COMPLETED:
                break

            if state.status in {RunStatus.NEEDS_HUMAN, RunStatus.FAILED}:
                break

            if state.status != RunStatus.DEBUGGING:
                raise RuntimeError(f"Unexpected run status after validation: {state.status}")

            state, _ = self.runtime.invoke_coordinator(state, task_graph)
            patch_batch = state.proposed_patch_batch or patch_batch

        if last_report is None:
            raise RuntimeError("No validation report produced")

        export_result: Optional[ExportResult] = None
        final_manifest_path: Optional[Path] = None
        if enable_export and state.status == RunStatus.COMPLETED and mode != RunMode.PROJECT_ONLY:
            export_result = self._export_project(
                run_id=run_id,
                project_dir=project_dir,
                godot_exe=godot_exe,
            )
            if export_result.success:
                final_manifest_path = self._write_final_manifest(
                    run_id=run_id,
                    prompt=prompt,
                    mode=mode,
                    spec=spec,
                    validation_report=last_report,
                    export_result=export_result,
                    applied_batches=applied_batches,
                    run_id_dir=project_dir.parent,
                )
            elif strict_export:
                state = model_copy_compat(
                    state,
                    update={
                        "status": RunStatus.FAILED,
                        "failure_reason": f"export_failed: {export_result.error_summary}",
                    },
                )

        run_bundle_path = self._write_run_bundle(
            run_id=run_id,
            prompt=prompt,
            project_dir=project_dir,
            state=state,
            project_spec=spec,
            validation_report=last_report,
            export_result=export_result,
            final_manifest_path=final_manifest_path,
        )

        return GameCreationResult(
            run_id=run_id,
            project_dir=project_dir,
            status=state.status,
            retry_count=state.retry_count,
            validation_report=last_report,
            export_result=export_result,
            final_manifest_path=final_manifest_path,
            run_bundle_path=run_bundle_path,
        )

    def _export_project(self, run_id: str, project_dir: Path, godot_exe: str | None) -> ExportResult:
        export_dir = project_dir / "export"
        export_dir.mkdir(parents=True, exist_ok=True)
        request = ExportRequest(
            run_id=run_id,
            project_dir=str(project_dir),
            preset_name="Windows Desktop",
            target=ExportTarget.WINDOWS,
            output_path=str(export_dir / "game.exe"),
        )
        resolved_godot_exe = godot_exe or os.getenv("GODOT_EXPORT_EXE", "godot4")
        return export_project(request=request, godot_exe=resolved_godot_exe)

    def _write_final_manifest(
        self,
        *,
        run_id: str,
        prompt: str,
        mode: RunMode,
        spec: Any,
        validation_report: ValidationReport,
        export_result: ExportResult,
        applied_batches: list[PatchBatch],
        run_id_dir: Path,
    ) -> Path:
        all_patches = []
        for batch in applied_batches:
            all_patches.extend(batch.patches)

        manifest: FinalManifest = build_final_manifest(
            run_id=run_id,
            prompt=prompt,
            mode=mode,
            project_spec=spec,
            validation_report=validation_report,
            export_result=export_result,
            applied_patches=all_patches,
        )

        manifest_path = run_id_dir / "final_manifest.json"
        if hasattr(manifest, "model_dump_json"):
            content = manifest.model_dump_json(indent=2)
        else:
            content = manifest.json(indent=2)
        manifest_path.write_text(content, encoding="utf-8")
        return manifest_path

    def _bootstrap_project(self, selected_template: str, run_id: str) -> Path:
        source_dir = self.workspace_root / selected_template
        if not source_dir.exists():
            raise FileNotFoundError(f"Template not found: {source_dir}")

        project_dir = self.workspace_root / "runs" / run_id / "project"
        project_dir.parent.mkdir(parents=True, exist_ok=True)

        shutil.copytree(
            source_dir,
            project_dir,
            ignore=shutil.ignore_patterns(".godot", ".vibe", "export"),
            dirs_exist_ok=False,
        )

        return project_dir

    def _validate_project_structure(self, run_id: str, attempt: int, project_dir: Path) -> ValidationReport:
        issues: list[ValidationIssue] = []
        stage_log = project_dir / ".vibe" / "validation" / f"structure_attempt_{attempt}.log"
        stage_log.parent.mkdir(parents=True, exist_ok=True)

        missing_files: list[str] = []
        for relative_path in REQUIRED_PROJECT_FILES:
            candidate = project_dir / relative_path
            if not candidate.exists():
                missing_files.append(relative_path)
                issues.append(
                    ValidationIssue(
                        stage=ValidationStage.CHECK,
                        severity=ValidationSeverity.FATAL,
                        message=f"Cannot open file: res://{relative_path}",
                        file_path=str(candidate),
                        matched_pattern="missing_file",
                    )
                )

        main_script = project_dir / "scripts" / "main.gd"
        if main_script.exists():
            content = main_script.read_text(encoding="utf-8", errors="replace")
            if "extends" not in content:
                issues.append(
                    ValidationIssue(
                        stage=ValidationStage.CHECK,
                        severity=ValidationSeverity.FATAL,
                        message="Parse Error at res://scripts/main.gd",
                        file_path=str(main_script),
                        matched_pattern="parse_error",
                    )
                )

        fatal_count = sum(1 for item in issues if item.severity == ValidationSeverity.FATAL)
        error_count = sum(1 for item in issues if item.severity == ValidationSeverity.ERROR)
        warning_count = sum(1 for item in issues if item.severity == ValidationSeverity.WARNING)

        lines = [
            f"attempt={attempt}",
            f"missing_files={len(missing_files)}",
            f"fatal={fatal_count}",
            f"error={error_count}",
            f"warning={warning_count}",
        ]
        if missing_files:
            lines.extend(f"missing:{item}" for item in missing_files)

        stage_log.write_text("\n".join(lines) + "\n", encoding="utf-8")

        success = fatal_count == 0 and error_count == 0
        summary = "project_structure_ok" if success else f"project_structure_failed: fatal={fatal_count}, error={error_count}"

        return ValidationReport(
            run_id=run_id,
            attempt=attempt,
            success=success,
            timed_out=False,
            stage_logs=[str(stage_log)],
            issues=issues,
            fatal_count=fatal_count,
            error_count=error_count,
            warning_count=warning_count,
            summary=summary,
        )

    def _write_run_bundle(
        self,
        *,
        run_id: str,
        prompt: str,
        project_dir: Path,
        state: RunState,
        project_spec: Any,
        validation_report: ValidationReport,
        export_result: Optional[ExportResult],
        final_manifest_path: Optional[Path],
    ) -> Path:
        bundle = {
            "run_id": run_id,
            "prompt": prompt,
            "project_dir": str(project_dir),
            "status": state.status.value,
            "retry_count": state.retry_count,
            "project_spec": self._model_dump_compat(project_spec),
            "validation_report": self._model_dump_compat(validation_report),
            "export_result": self._model_dump_compat(export_result) if export_result is not None else None,
            "final_manifest_path": str(final_manifest_path) if final_manifest_path is not None else None,
            "state": self._model_dump_compat(state),
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
        }

        output_path = project_dir.parent / "run_bundle.json"
        output_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
        return output_path

    @staticmethod
    def _build_run_id() -> str:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return f"run-{stamp}"

    @staticmethod
    def _model_dump_compat(model: Any) -> dict[str, Any]:
        if hasattr(model, "model_dump"):
            return model.model_dump()
        return model.dict()
