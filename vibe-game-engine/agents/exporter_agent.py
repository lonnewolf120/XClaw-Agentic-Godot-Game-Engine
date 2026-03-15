"""Exporter agent stub for milestone 2.

This module provides a minimal interface to export a Godot project using a headless Godot binary.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import subprocess
from pathlib import Path
from typing import Optional

from contracts.export import ExportArtifact, ExportRequest, ExportResult
from contracts.godot_patch import GodotFilePatch
from contracts.manifest import FinalManifest
from contracts.project_spec import ProjectSpec
from contracts.run_state import RunMode
from contracts.validation import ValidationReport


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def export_project(request: ExportRequest, godot_exe: Optional[str] = None) -> ExportResult:
    """Export the Godot project using a preset name and return structured result."""
    godot_exe = godot_exe or "godot4"
    output_path = Path(request.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    log_path = Path(request.project_dir) / ".vibe" / "export" / "export.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    args: list[str]
    if godot_exe.startswith("docker:"):
        image = godot_exe.split(":", 1)[1]
        project_root = Path(request.project_dir).resolve()
        output_abs = Path(request.output_path).resolve()
        project_abs = str(project_root)
        try:
            output_rel = output_abs.relative_to(project_root)
            output_in_container = f"/project/{output_rel.as_posix()}"
        except ValueError:
            output_in_container = f"/project/{output_abs.name}"
        args = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{project_abs}:/project",
            image,
            "godot",
            "--headless",
            "--path",
            "/project",
            "--export-release",
            request.preset_name,
            output_in_container,
        ]
    else:
        args = [
            godot_exe,
            "--headless",
            "--export-release",
            request.preset_name,
            str(output_path),
            "--path",
            request.project_dir,
        ]

    command = " ".join(args)

    try:
        with log_path.open("w", encoding="utf-8") as handle:
            proc = subprocess.run(args, stdout=handle, stderr=subprocess.STDOUT, check=False)
    except FileNotFoundError:
        return ExportResult(
            run_id=request.run_id,
            success=False,
            command=command,
            log_paths=[str(log_path)],
            artifacts=[],
            error_summary=f"export_binary_not_found: {godot_exe}",
        )

    if proc.returncode != 0:
        return ExportResult(
            run_id=request.run_id,
            success=False,
            command=command,
            log_paths=[str(log_path)],
            artifacts=[],
            error_summary=f"export_command_failed: code={proc.returncode}",
        )

    artifacts: list[ExportArtifact] = []
    if output_path.exists():
        artifacts.append(
            ExportArtifact(
                target=request.target,
                artifact_path=str(output_path),
                size_bytes=output_path.stat().st_size,
                sha256=_sha256(output_path),
            )
        )

    return ExportResult(
        run_id=request.run_id,
        success=bool(artifacts),
        command=command,
        log_paths=[str(log_path)],
        artifacts=artifacts,
        error_summary="" if artifacts else "export_completed_without_artifact",
    )


def build_final_manifest(
    *,
    run_id: str,
    prompt: str,
    mode: RunMode,
    project_spec: ProjectSpec,
    validation_report: ValidationReport,
    export_result: ExportResult,
    applied_patches: list[GodotFilePatch] | None = None,
) -> FinalManifest:
    if not export_result.success or not export_result.artifacts:
        raise ValueError("cannot build final manifest from unsuccessful export")

    artifact_checksums: list[str] = []
    for artifact in export_result.artifacts:
        artifact_path = Path(artifact.artifact_path)
        if not artifact_path.exists():
            raise ValueError(f"export artifact does not exist: {artifact_path}")
        real_checksum = _sha256(artifact_path)
        if real_checksum != artifact.sha256:
            raise ValueError(f"artifact checksum mismatch: {artifact_path}")
        artifact_checksums.append(real_checksum)

    patches = applied_patches or []
    files_changed = [patch.file_path for patch in patches]

    return FinalManifest(
        run_id=run_id,
        prompt=prompt,
        mode=mode,
        created_at_utc=datetime.now(timezone.utc).isoformat(),
        project_spec=project_spec,
        files_changed=files_changed,
        applied_patches=patches,
        validation_report=validation_report,
        export_result=export_result,
        validation_log_paths=validation_report.stage_logs,
        export_log_paths=export_result.log_paths,
        artifact_checksums=artifact_checksums,
    )
