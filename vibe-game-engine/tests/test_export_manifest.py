from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.exporter_agent import build_final_manifest, export_project
from agents.project_manager import build_project_spec
from contracts.export import ExportRequest, ExportTarget
from contracts.run_state import RunMode
from contracts.validation import ValidationReport


def test_build_final_manifest_after_successful_export(tmp_path, monkeypatch) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir(parents=True, exist_ok=True)

    def _fake_run(args, stdout, stderr, check):
        output_path = Path(args[4])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake-binary")

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr("agents.exporter_agent.subprocess.run", _fake_run)

    request = ExportRequest(
        run_id="run-manifest",
        project_dir=str(project_dir),
        preset_name="Windows Desktop",
        target=ExportTarget.WINDOWS,
        output_path=str(project_dir / "export" / "game.exe"),
    )
    export_result = export_project(request, godot_exe="godot4")
    assert export_result.success is True

    validation_report = ValidationReport(
        run_id="run-manifest",
        attempt=1,
        success=True,
        timed_out=False,
        stage_logs=["validation.log"],
        issues=[],
        fatal_count=0,
        error_count=0,
        warning_count=0,
        summary="ok",
    )

    spec = build_project_spec("A tiny platformer")
    manifest = build_final_manifest(
        run_id="run-manifest",
        prompt="A tiny platformer",
        mode=RunMode.STANDALONE,
        project_spec=spec,
        validation_report=validation_report,
        export_result=export_result,
        applied_patches=[],
    )

    assert manifest.run_id == "run-manifest"
    assert manifest.export_result.success is True
    assert manifest.validation_report.success is True
    assert manifest.artifact_checksums == [export_result.artifacts[0].sha256]
    assert manifest.export_log_paths == export_result.log_paths