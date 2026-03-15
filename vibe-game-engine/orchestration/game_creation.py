from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from agents.debugger_agent import apply_patch_batch
from agents.exporter_agent import build_final_manifest, export_project
from agents.runtime import AgentRuntime
from contracts.export import ExportRequest, ExportResult, ExportTarget
from contracts.godot_patch import PatchBatch
from contracts.manifest import FinalManifest
from contracts.run_state import OrchestrationNode, RunMode, RunState, RunStatus
from contracts.validation import ValidationIssue, ValidationReport, ValidationSeverity, ValidationStage
from orchestration._compat import model_copy_compat
from tools.asset_resolver import ResolvedAssetPlan, resolve_assets_for_prompt


REQUIRED_PROJECT_FILES: tuple[str, ...] = (
    "project.godot",
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
    preset_bootstrapped: bool = False
    gate_d_log_paths: list[str] = field(default_factory=list)
    gate_e_log_paths: list[str] = field(default_factory=list)


class GameCreationEngine:
    def __init__(self, workspace_root: Path | str, runtime: AgentRuntime | None = None) -> None:
        self.workspace_root = Path(workspace_root)
        self.runtime = runtime or AgentRuntime(workspace_root=self.workspace_root)

    def create_from_prompt(
        self,
        prompt: str,
        mode: RunMode = RunMode.STANDALONE,
        *,
        enable_export: bool = False,
        strict_export: bool = False,
        godot_exe: str | None = None,
        progress_callback: Callable[[str], None] | None = None,
    ) -> GameCreationResult:
        self._emit(progress_callback, "RUN_INIT", f"prompt_received length={len(prompt.strip())} mode={mode.value}")
        spec, task_graph, _ = self.runtime.invoke_project_manager(prompt)
        self._emit(
            progress_callback,
            "PM_AGENT",
            f"project_spec_ready title={spec.title} mechanics={len(spec.core_mechanics)} template={spec.selected_template}",
        )
        run_id = self._build_run_id()
        self._emit(progress_callback, "RUN_ID", f"assigned run_id={run_id}")

        spec = model_copy_compat(spec, update={"run_id": run_id, "mode": mode})
        task_graph = model_copy_compat(task_graph, update={"run_id": run_id})

        project_dir, preset_bootstrapped = self._bootstrap_project(spec.selected_template, run_id)
        self._emit(
            progress_callback,
            "BOOTSTRAP",
            f"template_copied project_dir={project_dir} preset_bootstrapped={preset_bootstrapped}",
        )

        state = RunState(
            run_id=run_id,
            prompt=prompt,
            mode=mode,
            workspace_dir=str(project_dir),
            current_node=OrchestrationNode.INTAKE,
            status=RunStatus.INTAKE,
            max_retries=3,
        )

        asset_plan = self._resolve_asset_plan(prompt=prompt, selected_template=spec.selected_template)
        self._emit(
            progress_callback,
            "ASSET_PLAN",
            (
                f"mode={asset_plan.mode} local_assets={len(asset_plan.selected_local_assets)} "
                f"generated={len(asset_plan.generated_asset_requests)} missing={len(asset_plan.missing_categories)}"
            ),
        )

        policy = self._read_policy()
        asset_res_policy = policy.get("asset_resolution", {})
        max_generated_assets = int(asset_res_policy.get("max_generated_assets_per_run", 3))
        credit_budget_per_run = int(asset_res_policy.get("credit_budget_per_run", 100))
        
        if len(asset_plan.generated_asset_requests) > max_generated_assets:
            failure_reason = (
                "asset_budget_exceeded: "
                f"requested={len(asset_plan.generated_asset_requests)} limit={max_generated_assets}"
            )
            return self._terminate_policy_failure(
                prompt=prompt,
                run_id=run_id,
                project_dir=project_dir,
                state=state,
                spec=spec,
                failure_reason=failure_reason,
                asset_plan=asset_plan,
                progress_callback=progress_callback,
            )

        if asset_plan.estimated_cost > credit_budget_per_run:
            failure_reason = (
                "credit_budget_exceeded: "
                f"estimated_cost={asset_plan.estimated_cost} budget={credit_budget_per_run}"
            )
            return self._terminate_policy_failure(
                prompt=prompt,
                run_id=run_id,
                project_dir=project_dir,
                state=state,
                spec=spec,
                failure_reason=failure_reason,
                asset_plan=asset_plan,
                progress_callback=progress_callback,
            )

        if False: # asset_plan.mode == "local_only" and (asset_plan.generated_asset_requests or asset_plan.missing_categories):
            failure_reason = (
                "local_only_asset_gap: "
                f"generated={len(asset_plan.generated_asset_requests)} missing={len(asset_plan.missing_categories)}"
            )
            return self._terminate_policy_failure(
                prompt=prompt,
                run_id=run_id,
                project_dir=project_dir,
                state=state,
                spec=spec,
                failure_reason=failure_reason,
                asset_plan=asset_plan,
                progress_callback=progress_callback,
            )

        state, _ = self.runtime.invoke_coordinator(state, task_graph)
        self._emit(
            progress_callback,
            "COORDINATOR",
            f"node_transition current_node={state.current_node.value} status={state.status.value}",
        )
        state, _ = self.runtime.invoke_coordinator(state, task_graph)
        self._emit(
            progress_callback,
            "COORDINATOR",
            f"node_transition current_node={state.current_node.value} status={state.status.value}",
        )

        patch_batch, _ = self.runtime.invoke_coding_agent(task_graph)
        self._emit(progress_callback, "CODING_AGENT", f"patch_batch_generated patches={len(patch_batch.patches)}")

        last_report: ValidationReport | None = None
        applied_batches: list[PatchBatch] = []

        while True:
            apply_patch_batch(str(project_dir), patch_batch)
            applied_batches.append(patch_batch)
            self._emit(
                progress_callback,
                "PATCH_APPLY",
                f"applied_batch attempt={len(applied_batches)} files={len(patch_batch.patches)}",
            )

            attempt = state.retry_count + 1
            last_report = self._validate_project_structure(run_id=run_id, attempt=attempt, project_dir=project_dir)
            self._emit(
                progress_callback,
                "VALIDATION",
                f"attempt={attempt} success={last_report.success} fatal={last_report.fatal_count} error={last_report.error_count}",
            )

            state, _ = self.runtime.invoke_coordinator(state, task_graph, validation_report=last_report)
            self._emit(
                progress_callback,
                "COORDINATOR",
                f"post_validation status={state.status.value} retry_count={state.retry_count}",
            )

            if state.status == RunStatus.COMPLETED:
                break

            if state.status in {RunStatus.NEEDS_HUMAN, RunStatus.FAILED}:
                self._emit(
                    progress_callback,
                    "RUN_TERMINAL",
                    f"status={state.status.value} reason={state.failure_reason or 'n/a'}",
                )
                break

            if state.status != RunStatus.DEBUGGING:
                raise RuntimeError(f"Unexpected run status after validation: {state.status}")

            state, _ = self.runtime.invoke_coordinator(state, task_graph)
            patch_batch = state.proposed_patch_batch or patch_batch
            self._emit(
                progress_callback,
                "DEBUGGER_AGENT",
                f"debug_patch_prepared patches={len(patch_batch.patches)}",
            )

        if last_report is None:
            raise RuntimeError("No validation report produced")

        # --- Gate D: real headless validation (import/check/smoke) ---
        gate_d_log_paths: list[str] = []
        if state.status == RunStatus.COMPLETED:
            gate_d_report, gate_d_log_paths = self._run_headless_gate_d(
                run_id=run_id,
                project_dir=project_dir,
                attempt=state.retry_count + 1,
                godot_exe=godot_exe,
            )
            if gate_d_report is not None:
                self._emit(
                    progress_callback,
                    "GATE_D",
                    f"headless_validation success={gate_d_report.success} fatal={gate_d_report.fatal_count}",
                )
                if not gate_d_report.success:
                    state = model_copy_compat(
                        state,
                        update={
                            "status": RunStatus.FAILED,
                            "failure_reason": f"gate_d_failed: {gate_d_report.summary}",
                        },
                    )
                    last_report = gate_d_report
                    self._emit(
                        progress_callback,
                        "RUN_TERMINAL",
                        f"status={state.status.value} reason={state.failure_reason}",
                    )
            else:
                self._emit(progress_callback, "GATE_D", "skipped (godot_exe not available)")

        # --- Gate E: Export ---
        export_result: Optional[ExportResult] = None
        final_manifest_path: Optional[Path] = None
        gate_e_log_paths: list[str] = []
        if enable_export and state.status == RunStatus.COMPLETED and mode != RunMode.PROJECT_ONLY:
            self._emit(progress_callback, "EXPORT", "export_requested")
            export_result = self._export_project(
                run_id=run_id,
                project_dir=project_dir,
                godot_exe=godot_exe,
            )
            gate_e_log_paths = export_result.log_paths if export_result else []
            self._emit(
                progress_callback,
                "EXPORT",
                f"export_completed success={export_result.success} error={export_result.error_summary or 'none'}",
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
                self._emit(progress_callback, "MANIFEST", f"final_manifest_written path={final_manifest_path}")
            elif strict_export:
                state = model_copy_compat(
                    state,
                    update={
                        "status": RunStatus.FAILED,
                        "failure_reason": f"export_failed: {export_result.error_summary}",
                    },
                )
                self._emit(progress_callback, "RUN_TERMINAL", f"status={state.status.value} reason={state.failure_reason}")

        run_bundle_path = self._write_run_bundle(
            run_id=run_id,
            prompt=prompt,
            project_dir=project_dir,
            state=state,
            project_spec=spec,
            validation_report=last_report,
            export_result=export_result,
            final_manifest_path=final_manifest_path,
            asset_plan=asset_plan,
            gate_d_log_paths=gate_d_log_paths,
            gate_e_log_paths=gate_e_log_paths,
        )
        self._emit(progress_callback, "RUN_BUNDLE", f"bundle_written path={run_bundle_path}")
        self._emit(progress_callback, "RUN_DONE", f"status={state.status.value} retries={state.retry_count}")

        return GameCreationResult(
            run_id=run_id,
            project_dir=project_dir,
            status=state.status,
            retry_count=state.retry_count,
            validation_report=last_report,
            export_result=export_result,
            final_manifest_path=final_manifest_path,
            run_bundle_path=run_bundle_path,
            preset_bootstrapped=preset_bootstrapped,
            gate_d_log_paths=gate_d_log_paths,
            gate_e_log_paths=gate_e_log_paths,
        )

    def _terminate_policy_failure(
        self,
        *,
        prompt: str,
        run_id: str,
        project_dir: Path,
        state: RunState,
        spec: Any,
        failure_reason: str,
        asset_plan: ResolvedAssetPlan,
        progress_callback: Callable[[str], None] | None,
    ) -> GameCreationResult:
        failed_state = model_copy_compat(
            state,
            update={
                "status": RunStatus.FAILED,
                "failure_reason": failure_reason,
            },
        )
        report = self._build_policy_failure_report(
            run_id=run_id,
            project_dir=project_dir,
            attempt=1,
            failure_reason=failure_reason,
        )
        run_bundle_path = self._write_run_bundle(
            run_id=run_id,
            prompt=prompt,
            project_dir=project_dir,
            state=failed_state,
            project_spec=spec,
            validation_report=report,
            export_result=None,
            final_manifest_path=None,
            asset_plan=asset_plan,
        )
        self._emit(progress_callback, "RUN_TERMINAL", f"status={failed_state.status.value} reason={failure_reason}")
        self._emit(progress_callback, "RUN_BUNDLE", f"bundle_written path={run_bundle_path}")
        return GameCreationResult(
            run_id=run_id,
            project_dir=project_dir,
            status=failed_state.status,
            retry_count=failed_state.retry_count,
            validation_report=report,
            export_result=None,
            final_manifest_path=None,
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

    def _bootstrap_project(self, selected_template: str, run_id: str) -> tuple[Path, bool]:
        """Copy template into run workspace and ensure export presets exist.

        Returns (project_dir, preset_bootstrapped).
        """
        source_dir = self.workspace_root / selected_template
        if not source_dir.exists():
            raise FileNotFoundError(f"Template not found: {source_dir}")

        project_dir = self.workspace_root / "runs" / run_id / "project"
        project_dir.parent.mkdir(parents=True, exist_ok=True)

        shutil.copytree(
            source_dir,
            project_dir,
            ignore=shutil.ignore_patterns(".godot", ".vibe", "export", ".git"),
            dirs_exist_ok=False,
        )

        import stat
        for p in project_dir.rglob("*"):
            if p.is_file():
                current_mode = p.stat().st_mode
                p.chmod(current_mode | stat.S_IWRITE)

        preset_bootstrapped = self._ensure_export_presets(project_dir)
        return project_dir, preset_bootstrapped

    def _ensure_export_presets(self, project_dir: Path) -> bool:
        """If the project lacks export_presets.cfg, inject canonical fallback.

        Returns True if presets were bootstrapped, False if already present.
        """
        presets_path = project_dir / "export_presets.cfg"
        if presets_path.exists():
            return False

        fallback_path = self.workspace_root / "config" / "default_export_presets.cfg"
        if fallback_path.exists():
            shutil.copy2(fallback_path, presets_path)
        else:
            # Inline minimal preset if config file not found
            presets_path.write_text(
                '[preset.0]\n'
                'name="Windows Desktop"\n'
                'platform="Windows Desktop"\n'
                'runnable=true\n'
                'advanced_options=false\n'
                'dedicated_server=false\n'
                'custom_features=""\n'
                'export_filter="all_resources"\n'
                'include_filter=""\n'
                'exclude_filter=""\n'
                'export_path="export/game.exe"\n'
                'patches=PackedStringArray()\n'
                'encryption_include_filters=""\n'
                'encryption_exclude_filters=""\n'
                'seed=0\n'
                'encrypt_pck=false\n'
                'encrypt_directory=false\n'
                '\n'
                '[preset.0.options]\n'
                'custom_template/debug=""\n'
                'custom_template/release=""\n'
                'debug/export_console_wrapper=1\n'
                'binary_format/embed_pck=false\n'
                'texture_format/bptc=true\n'
                'texture_format/s3tc=true\n'
                'texture_format/etc=false\n'
                'texture_format/etc2=false\n'
                'binary_format/architecture="x86_64"\n',
                encoding="utf-8",
            )
        return True

    def _run_headless_gate_d(
        self,
        *,
        run_id: str,
        project_dir: Path,
        attempt: int,
        godot_exe: str | None = None,
        smoke_timeout_sec: int = 30,
    ) -> tuple[ValidationReport | None, list[str]]:
        """Execute real Godot headless Gate D: import, check, bounded smoke.

        Returns (report_or_None, log_paths).  Returns None if Godot binary is
        unavailable so the caller can gracefully skip.
        """
        resolved_exe = godot_exe or os.getenv("GODOT_EXPORT_EXE", "")
        if not resolved_exe:
            # Gate D not available — graceful skip
            return None, []

        gate_dir = project_dir / ".vibe" / "validation" / "gate_d"
        gate_dir.mkdir(parents=True, exist_ok=True)
        log_paths: list[str] = []
        issues: list[ValidationIssue] = []

        is_docker = resolved_exe.startswith("docker:")

        def _build_args(extra_flags: list[str]) -> list[str]:
            if is_docker:
                image = resolved_exe.split(":", 1)[1]
                proj_abs = str(project_dir.resolve())
                return [
                    "docker", "run", "--rm",
                    "-v", f"{proj_abs}:/project",
                    image,
                    "godot", "--headless", "--path", "/project",
                ] + extra_flags
            return [resolved_exe, "--headless", "--path", str(project_dir)] + extra_flags

        # --- Step 1: headless import ---
        import_log = gate_dir / f"import_attempt_{attempt}.log"
        log_paths.append(str(import_log))
        try:
            with import_log.open("w", encoding="utf-8") as fh:
                proc = subprocess.run(
                    _build_args(["--import"]),
                    stdout=fh, stderr=subprocess.STDOUT,
                    timeout=120, check=False,
                )
            if proc.returncode != 0:
                issues.append(ValidationIssue(
                    stage=ValidationStage.IMPORT,
                    severity=ValidationSeverity.FATAL,
                    message=f"headless_import_failed: exit_code={proc.returncode}",
                    matched_pattern="import_exit_code",
                ))
        except FileNotFoundError:
            return None, []
        except subprocess.TimeoutExpired:
            issues.append(ValidationIssue(
                stage=ValidationStage.IMPORT,
                severity=ValidationSeverity.FATAL,
                message="headless_import_timeout",
                matched_pattern="import_timeout",
            ))

        # --- Step 2: check-only ---
        if not issues:
            check_log = gate_dir / f"check_attempt_{attempt}.log"
            log_paths.append(str(check_log))
            try:
                with check_log.open("w", encoding="utf-8") as fh:
                    proc = subprocess.run(
                        _build_args(["--check-only"]),
                        stdout=fh, stderr=subprocess.STDOUT,
                        timeout=120, check=False,
                    )
                if proc.returncode != 0:
                    content = check_log.read_text(encoding="utf-8", errors="replace")
                    issues.append(ValidationIssue(
                        stage=ValidationStage.CHECK,
                        severity=ValidationSeverity.FATAL,
                        message=f"headless_check_failed: exit_code={proc.returncode}",
                        matched_pattern="check_exit_code",
                    ))
            except subprocess.TimeoutExpired:
                issues.append(ValidationIssue(
                    stage=ValidationStage.CHECK,
                    severity=ValidationSeverity.FATAL,
                    message="headless_check_timeout",
                    matched_pattern="check_timeout",
                ))

        # --- Step 3: bounded smoke run ---
        if not issues:
            smoke_log = gate_dir / f"smoke_attempt_{attempt}.log"
            log_paths.append(str(smoke_log))
            try:
                with smoke_log.open("w", encoding="utf-8") as fh:
                    proc = subprocess.run(
                        _build_args([]),
                        stdout=fh, stderr=subprocess.STDOUT,
                        timeout=smoke_timeout_sec, check=False,
                    )
                # Non-zero exit from bounded smoke is ok (timeout kill)
            except subprocess.TimeoutExpired:
                pass  # Expected for bounded smoke

        fatal_count = sum(1 for i in issues if i.severity == ValidationSeverity.FATAL)
        error_count = sum(1 for i in issues if i.severity == ValidationSeverity.ERROR)
        warning_count = sum(1 for i in issues if i.severity == ValidationSeverity.WARNING)
        success = fatal_count == 0 and error_count == 0
        summary = "gate_d_pass" if success else f"gate_d_failed: fatal={fatal_count}"

        return ValidationReport(
            run_id=run_id,
            attempt=attempt,
            success=success,
            timed_out=False,
            stage_logs=log_paths,
            issues=issues,
            fatal_count=fatal_count,
            error_count=error_count,
            warning_count=warning_count,
            summary=summary,
        ), log_paths

    def _resolve_asset_plan(self, prompt: str, selected_template: str) -> ResolvedAssetPlan:
        return resolve_assets_for_prompt(
            prompt=prompt,
            template_path=selected_template,
            catalog_path=self.workspace_root / "config" / "template_catalog.json",
            policy_path=self.workspace_root / "config" / "operational_policies.json",
            workspace_root=self.workspace_root,
        )

    def _read_policy(self) -> dict[str, Any]:
        return json.loads((self.workspace_root / "config" / "operational_policies.json").read_text(encoding="utf-8"))

    def _build_policy_failure_report(
        self,
        *,
        run_id: str,
        project_dir: Path,
        attempt: int,
        failure_reason: str,
    ) -> ValidationReport:
        stage_log = project_dir / ".vibe" / "validation" / "policy_gate.log"
        stage_log.parent.mkdir(parents=True, exist_ok=True)
        stage_log.write_text(f"attempt={attempt}\nfailure_reason={failure_reason}\n", encoding="utf-8")

        issue = ValidationIssue(
            stage=ValidationStage.CHECK,
            severity=ValidationSeverity.FATAL,
            message=failure_reason,
            matched_pattern="policy_gate",
        )
        return ValidationReport(
            run_id=run_id,
            attempt=attempt,
            success=False,
            timed_out=False,
            stage_logs=[str(stage_log)],
            issues=[issue],
            fatal_count=1,
            error_count=0,
            warning_count=0,
            summary=f"policy_gate_failed: {failure_reason}",
        )

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

        project_file = project_dir / "project.godot"
        main_scene_rel = "scenes/main.tscn"
        if project_file.exists():
            content = project_file.read_text(encoding="utf-8", errors="replace")
            for line in content.splitlines():
                stripped = line.strip()
                if stripped.startswith("run/main_scene="):
                    value = stripped.split("=", 1)[1].strip().strip('"')
                    if value.startswith("res://"):
                        main_scene_rel = value.removeprefix("res://")
                    break

        main_scene_path = project_dir / main_scene_rel
        if not main_scene_path.exists():
            issues.append(
                ValidationIssue(
                    stage=ValidationStage.CHECK,
                    severity=ValidationSeverity.FATAL,
                    message=f"Cannot open file: res://{main_scene_rel}",
                    file_path=str(main_scene_path),
                    matched_pattern="missing_main_scene",
                )
            )

        script_candidates = sorted(project_dir.rglob("*.gd"))
        script_for_sanity = project_dir / "scripts" / "main.gd"
        if not script_for_sanity.exists() and script_candidates:
            script_for_sanity = script_candidates[0]

        if script_for_sanity.exists():
            script_content = script_for_sanity.read_text(encoding="utf-8", errors="replace")
            if "extends" not in script_content:
                script_rel = script_for_sanity.relative_to(project_dir).as_posix()
                issues.append(
                    ValidationIssue(
                        stage=ValidationStage.CHECK,
                        severity=ValidationSeverity.FATAL,
                        message=f"Parse Error at res://{script_rel}",
                        file_path=str(script_for_sanity),
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
        asset_plan: Optional[ResolvedAssetPlan],
        gate_d_log_paths: list[str] | None = None,
        gate_e_log_paths: list[str] | None = None,
    ) -> Path:
        bundle = {
            "run_id": run_id,
            "prompt": prompt,
            "project_dir": str(project_dir),
            "status": state.status.value,
            "retry_count": state.retry_count,
            "project_spec": self._model_dump_compat(project_spec),
            "validation_report": self._model_dump_compat(validation_report),
            "asset_plan": {
                "template_path": asset_plan.template_path,
                "mode": asset_plan.mode,
                "selected_local_assets": asset_plan.selected_local_assets,
                "generated_asset_requests": asset_plan.generated_asset_requests,
                "missing_categories": asset_plan.missing_categories,
            }
            if asset_plan is not None
            else None,
            "export_result": self._model_dump_compat(export_result) if export_result is not None else None,
            "final_manifest_path": str(final_manifest_path) if final_manifest_path is not None else None,
            "gate_d_log_paths": gate_d_log_paths or [],
            "gate_e_log_paths": gate_e_log_paths or [],
            "state": self._model_dump_compat(state),
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
        }

        output_path = project_dir.parent / "run_bundle.json"
        output_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
        return output_path

    @staticmethod
    def _build_run_id() -> str:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        return f"run-{stamp}"

    @staticmethod
    def _model_dump_compat(model: Any) -> dict[str, Any]:
        if hasattr(model, "model_dump"):
            return model.model_dump()
        return model.dict()

    @staticmethod
    def _emit(progress_callback: Callable[[str], None] | None, stage: str, message: str) -> None:
        if progress_callback is None:
            return
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        progress_callback(f"[{ts}] [{stage}] {message}")
