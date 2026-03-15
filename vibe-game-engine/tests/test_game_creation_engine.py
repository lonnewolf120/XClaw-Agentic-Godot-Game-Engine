from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import agents.runtime as runtime_module
import agents.exporter_agent as exporter_module
from contracts.godot_patch import GodotFilePatch, PatchBatch, PatchOp
from contracts.run_state import RunStatus
from orchestration.game_creation import GameCreationEngine


def _write_base_template(root: Path) -> None:
    template = root / "templates" / "base_2d_platformer"
    (template / "scenes").mkdir(parents=True, exist_ok=True)
    (template / "scripts").mkdir(parents=True, exist_ok=True)
    (template / "project.godot").write_text("[application]\n", encoding="utf-8")
    (template / "export_presets.cfg").write_text(
        "[preset.0]\n"
        "name=\"Windows Desktop\"\n"
        "platform=\"Windows Desktop\"\n"
        "runnable=true\n",
        encoding="utf-8",
    )
    (template / "scenes" / "Main.tscn").write_text("[gd_scene]\n", encoding="utf-8")
    (template / "scripts" / "main.gd").write_text(
        "extends Node2D\n\nfunc _ready() -> void:\n    pass\n",
        encoding="utf-8",
    )


def test_create_game_from_prompt_happy_path(tmp_path: Path) -> None:
    _write_base_template(tmp_path)
    engine = GameCreationEngine(workspace_root=tmp_path)

    result = engine.create_from_prompt("Create a tiny platformer with jump")

    assert result.status == RunStatus.COMPLETED
    assert result.project_dir.exists()
    assert (result.project_dir / "project.godot").exists()
    assert (result.project_dir / "scripts" / "main.gd").exists()
    assert result.run_bundle_path.exists()


def test_create_game_retries_and_recovers_with_debug_patch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_base_template(tmp_path)

    def _bad_generate(task_graph):
        return PatchBatch(
            run_id=task_graph.run_id,
            attempt=1,
            patches=[
                GodotFilePatch(
                    patch_id="bad-main",
                    op=PatchOp.UPDATE,
                    file_path="res://scripts/main.gd",
                    language="gdscript",
                    reason="Inject invalid starter script",
                    full_content="func _ready() -> void:\n    pass\n",
                    hunks=[],
                    creates_backup=True,
                )
            ],
        )

    monkeypatch.setattr(runtime_module, "generate_patches", _bad_generate)

    engine = GameCreationEngine(workspace_root=tmp_path)
    result = engine.create_from_prompt("Create a tiny platformer with jump")

    assert result.status == RunStatus.COMPLETED
    assert result.retry_count == 1
    content = (result.project_dir / "scripts" / "main.gd").read_text(encoding="utf-8")
    assert "extends" in content


def test_create_game_fails_when_template_missing(tmp_path: Path) -> None:
    engine = GameCreationEngine(workspace_root=tmp_path)
    with pytest.raises(FileNotFoundError):
        engine.create_from_prompt("Create a tiny platformer")


def test_create_game_with_export_and_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_base_template(tmp_path)

    def _fake_run(args, stdout, stderr, check):
        output_path = Path(args[4])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake-binary")

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr(exporter_module.subprocess, "run", _fake_run)

    engine = GameCreationEngine(workspace_root=tmp_path)
    result = engine.create_from_prompt(
        "Create a tiny platformer with jump",
        enable_export=True,
        godot_exe="godot4",
    )

    assert result.status == RunStatus.COMPLETED
    assert result.export_result is not None
    assert result.export_result.success is True
    assert result.final_manifest_path is not None
    assert result.final_manifest_path.exists()


def test_create_game_strict_export_failure_marks_run_failed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_base_template(tmp_path)

    def _missing_binary(args, stdout, stderr, check):
        raise FileNotFoundError("godot4")

    monkeypatch.setattr(exporter_module.subprocess, "run", _missing_binary)

    engine = GameCreationEngine(workspace_root=tmp_path)
    result = engine.create_from_prompt(
        "Create a tiny platformer with jump",
        enable_export=True,
        strict_export=True,
        godot_exe="godot4",
    )

    assert result.status == RunStatus.FAILED
    assert result.export_result is not None
    assert result.export_result.success is False
