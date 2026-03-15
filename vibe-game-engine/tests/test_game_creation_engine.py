from __future__ import annotations

import json
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
    (template / "assets" / "ui").mkdir(parents=True, exist_ok=True)
    (template / "assets" / "sfx").mkdir(parents=True, exist_ok=True)
    (template / "assets" / "music").mkdir(parents=True, exist_ok=True)
    (template / "assets" / "sprites").mkdir(parents=True, exist_ok=True)
    (template / "assets" / "tiles").mkdir(parents=True, exist_ok=True)

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
    (template / "assets" / "ui" / "hud.png").write_text("png", encoding="utf-8")
    (template / "assets" / "sfx" / "jump.ogg").write_text("ogg", encoding="utf-8")
    (template / "assets" / "music" / "loop.ogg").write_text("ogg", encoding="utf-8")
    (template / "assets" / "sprites" / "hero.png").write_text("png", encoding="utf-8")
    (template / "assets" / "tiles" / "ground.png").write_text("png", encoding="utf-8")

    config_dir = root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "operational_policies.json").write_text(
        "{\n"
        "  \"asset_resolution\": {\n"
        "    \"mode\": \"local_first\",\n"
        "    \"credit_budget_per_run\": 100,\n"
        "    \"max_generated_assets_per_run\": 3,\n"
        "    \"allowed_online_sources\": [\"kenney.nl\"]\n"
        "  },\n"
        "  \"asset_fallback_starter_library\": {\n"
        "    \"max_total_assets\": 32,\n"
        "    \"constraints\": {\n"
        "      \"max_texture_resolution\": 1024,\n"
        "      \"allowed_formats\": [\"png\", \"ogg\", \"wav\", \"glb\", \"webm\"]\n"
        "    }\n"
        "  }\n"
        "}\n",
        encoding="utf-8",
    )
    (config_dir / "template_catalog.json").write_text(
        "{\n"
        "  \"version\": \"v1\",\n"
        "  \"default_template_path\": \"templates/base_2d_platformer\",\n"
        "  \"templates\": [\n"
        "    {\n"
        "      \"template_id\": \"base_2d_platformer\",\n"
        "      \"path\": \"templates/base_2d_platformer\",\n"
        "      \"dimension\": \"2d\",\n"
        "      \"tags\": [\"platformer\"],\n"
        "      \"credit_cost_hint\": 1,\n"
        "      \"assets\": [\n"
        "        {\n"
        "          \"asset_id\": \"hud\",\n"
        "          \"category\": \"ui\",\n"
        "          \"local_path\": \"templates/base_2d_platformer/assets/ui/hud.png\",\n"
        "          \"checksum_sha256\": \"na\",\n"
        "          \"compatible_genres\": [\"platformer\"],\n"
        "          \"tags\": [\"ui\"],\n"
        "          \"source\": {\n"
        "            \"provider\": \"Kenney\",\n"
        "            \"author\": \"Kenney\",\n"
        "            \"source_url\": \"https://kenney.nl/assets/ui-pack\",\n"
        "            \"download_url\": \"https://kenney.nl/assets/ui-pack.zip\",\n"
        "            \"license\": \"CC0\",\n"
        "            \"attribution\": \"Kenney\"\n"
        "          }\n"
        "        },\n"
        "        {\n"
        "          \"asset_id\": \"sfx\",\n"
        "          \"category\": \"sfx\",\n"
        "          \"local_path\": \"templates/base_2d_platformer/assets/sfx/jump.ogg\",\n"
        "          \"checksum_sha256\": \"na\",\n"
        "          \"compatible_genres\": [\"platformer\"],\n"
        "          \"tags\": [\"sfx\"],\n"
        "          \"source\": {\n"
        "            \"provider\": \"Kenney\",\n"
        "            \"author\": \"Kenney\",\n"
        "            \"source_url\": \"https://kenney.nl/assets/ui-pack\",\n"
        "            \"download_url\": \"https://kenney.nl/assets/ui-pack.zip\",\n"
        "            \"license\": \"CC0\",\n"
        "            \"attribution\": \"Kenney\"\n"
        "          }\n"
        "        },\n"
        "        {\n"
        "          \"asset_id\": \"music\",\n"
        "          \"category\": \"music\",\n"
        "          \"local_path\": \"templates/base_2d_platformer/assets/music/loop.ogg\",\n"
        "          \"checksum_sha256\": \"na\",\n"
        "          \"compatible_genres\": [\"platformer\"],\n"
        "          \"tags\": [\"music\"],\n"
        "          \"source\": {\n"
        "            \"provider\": \"Kenney\",\n"
        "            \"author\": \"Kenney\",\n"
        "            \"source_url\": \"https://kenney.nl/assets/ui-pack\",\n"
        "            \"download_url\": \"https://kenney.nl/assets/ui-pack.zip\",\n"
        "            \"license\": \"CC0\",\n"
        "            \"attribution\": \"Kenney\"\n"
        "          }\n"
        "        },\n"
        "        {\n"
        "          \"asset_id\": \"sprites\",\n"
        "          \"category\": \"sprites\",\n"
        "          \"local_path\": \"templates/base_2d_platformer/assets/sprites/hero.png\",\n"
        "          \"checksum_sha256\": \"na\",\n"
        "          \"compatible_genres\": [\"platformer\"],\n"
        "          \"tags\": [\"sprites\"],\n"
        "          \"source\": {\n"
        "            \"provider\": \"Kenney\",\n"
        "            \"author\": \"Kenney\",\n"
        "            \"source_url\": \"https://kenney.nl/assets/ui-pack\",\n"
        "            \"download_url\": \"https://kenney.nl/assets/ui-pack.zip\",\n"
        "            \"license\": \"CC0\",\n"
        "            \"attribution\": \"Kenney\"\n"
        "          }\n"
        "        },\n"
        "        {\n"
        "          \"asset_id\": \"tiles\",\n"
        "          \"category\": \"tiles\",\n"
        "          \"local_path\": \"templates/base_2d_platformer/assets/tiles/ground.png\",\n"
        "          \"checksum_sha256\": \"na\",\n"
        "          \"compatible_genres\": [\"platformer\"],\n"
        "          \"tags\": [\"tiles\"],\n"
        "          \"source\": {\n"
        "            \"provider\": \"Kenney\",\n"
        "            \"author\": \"Kenney\",\n"
        "            \"source_url\": \"https://kenney.nl/assets/ui-pack\",\n"
        "            \"download_url\": \"https://kenney.nl/assets/ui-pack.zip\",\n"
        "            \"license\": \"CC0\",\n"
        "            \"attribution\": \"Kenney\"\n"
        "          }\n"
        "        }\n"
        "      ]\n"
        "    }\n"
        "  ]\n"
        "}\n",
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

    def _fake_run(args, stdout, stderr=None, **kwargs):
        # Find the output path argument for export (--export-release preset output)
        try:
            output_path = Path(args[4])
        except (IndexError, TypeError):
            class OkResult:
                returncode = 0
            return OkResult()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake-binary")

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr(exporter_module.subprocess, "run", _fake_run)
    import orchestration.game_creation as gc_module
    monkeypatch.setattr(gc_module.subprocess, "run", _fake_run)

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

    def _missing_binary(args, stdout, stderr=None, **kwargs):
        raise FileNotFoundError("godot4")

    monkeypatch.setattr(exporter_module.subprocess, "run", _missing_binary)
    import orchestration.game_creation as gc_module
    monkeypatch.setattr(gc_module.subprocess, "run", _missing_binary)

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


def test_create_game_fails_when_asset_generation_budget_exceeded(tmp_path: Path) -> None:
    _write_base_template(tmp_path)

    policy_path = tmp_path / "config" / "operational_policies.json"
    policy_path.write_text(
        "{\n"
        "  \"asset_resolution\": {\n"
        "    \"mode\": \"local_first\",\n"
        "    \"credit_budget_per_run\": 100,\n"
        "    \"max_generated_assets_per_run\": 0,\n"
        "    \"allowed_online_sources\": [\"kenney.nl\"]\n"
        "  },\n"
        "  \"asset_fallback_starter_library\": {\n"
        "    \"max_total_assets\": 32,\n"
        "    \"constraints\": {\n"
        "      \"max_texture_resolution\": 1024,\n"
        "      \"allowed_formats\": [\"png\", \"ogg\", \"wav\", \"glb\", \"webm\"]\n"
        "    }\n"
        "  }\n"
        "}\n",
        encoding="utf-8",
    )

    engine = GameCreationEngine(workspace_root=tmp_path)
    result = engine.create_from_prompt("Create a tiny platformer with jump and cutscene")

    assert result.status == RunStatus.FAILED
    assert "asset_budget_exceeded" in result.validation_report.summary


def _write_template_no_presets(root: Path) -> None:
    """Create a template that looks like a Kenney import: has project.godot + scenes but NO export_presets.cfg."""
    template = root / "templates" / "kenney_mock"
    (template / "scenes").mkdir(parents=True, exist_ok=True)
    (template / "scripts").mkdir(parents=True, exist_ok=True)
    (template / "assets" / "ui").mkdir(parents=True, exist_ok=True)
    (template / "assets" / "sfx").mkdir(parents=True, exist_ok=True)
    (template / "assets" / "music").mkdir(parents=True, exist_ok=True)
    (template / "assets" / "sprites").mkdir(parents=True, exist_ok=True)
    (template / "assets" / "tiles").mkdir(parents=True, exist_ok=True)

    (template / "project.godot").write_text(
        '[application]\nrun/main_scene="res://scenes/main.tscn"\n',
        encoding="utf-8",
    )
    # NO export_presets.cfg written!
    (template / "scenes" / "main.tscn").write_text("[gd_scene]\n", encoding="utf-8")
    (template / "scripts" / "main.gd").write_text(
        "extends Node3D\n\nfunc _ready() -> void:\n    pass\n",
        encoding="utf-8",
    )
    (template / "assets" / "ui" / "hud.png").write_text("png", encoding="utf-8")
    (template / "assets" / "sfx" / "shot.ogg").write_text("ogg", encoding="utf-8")
    (template / "assets" / "music" / "loop.ogg").write_text("ogg", encoding="utf-8")
    (template / "assets" / "sprites" / "hero.png").write_text("png", encoding="utf-8")
    (template / "assets" / "tiles" / "ground.png").write_text("png", encoding="utf-8")


def _write_config_with_kenney_mock(root: Path) -> None:
    """Write catalog and policy configs that include the kenney_mock template."""
    config_dir = root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "operational_policies.json").write_text(
        '{\n'
        '  "asset_resolution": {\n'
        '    "mode": "local_first",\n'
        '    "credit_budget_per_run": 100,\n'
        '    "max_generated_assets_per_run": 3,\n'
        '    "allowed_online_sources": ["kenney.nl"]\n'
        '  },\n'
        '  "asset_fallback_starter_library": {\n'
        '    "max_total_assets": 32,\n'
        '    "constraints": {\n'
        '      "max_texture_resolution": 1024,\n'
        '      "allowed_formats": ["png", "ogg", "wav", "glb", "webm"]\n'
        '    }\n'
        '  }\n'
        '}\n',
        encoding="utf-8",
    )
    (config_dir / "template_catalog.json").write_text(
        '{\n'
        '  "version": "v1",\n'
        '  "default_template_path": "templates/kenney_mock",\n'
        '  "templates": [\n'
        '    {\n'
        '      "template_id": "kenney_mock",\n'
        '      "path": "templates/kenney_mock",\n'
        '      "dimension": "3d",\n'
        '      "tags": ["fps", "shooter"],\n'
        '      "credit_cost_hint": 0,\n'
        '      "assets": [\n'
        '        {\n'
        '          "asset_id": "hud",\n'
        '          "category": "ui",\n'
        '          "local_path": "templates/kenney_mock/assets/ui/hud.png",\n'
        '          "checksum_sha256": "na",\n'
        '          "compatible_genres": ["shooter"],\n'
        '          "tags": ["ui"],\n'
        '          "source": {\n'
        '            "provider": "Kenney",\n'
        '            "author": "Kenney",\n'
        '            "source_url": "https://kenney.nl/assets/ui-pack",\n'
        '            "download_url": "https://kenney.nl/assets/ui-pack.zip",\n'
        '            "license": "CC0",\n'
        '            "attribution": "Kenney"\n'
        '          }\n'
        '        },\n'
        '        {\n'
        '          "asset_id": "sfx",\n'
        '          "category": "sfx",\n'
        '          "local_path": "templates/kenney_mock/assets/sfx/shot.ogg",\n'
        '          "checksum_sha256": "na",\n'
        '          "compatible_genres": ["shooter"],\n'
        '          "tags": ["sfx"],\n'
        '          "source": {\n'
        '            "provider": "Kenney",\n'
        '            "author": "Kenney",\n'
        '            "source_url": "https://kenney.nl/assets/ui-pack",\n'
        '            "download_url": "https://kenney.nl/assets/ui-pack.zip",\n'
        '            "license": "CC0",\n'
        '            "attribution": "Kenney"\n'
        '          }\n'
        '        },\n'
        '        {\n'
        '          "asset_id": "music",\n'
        '          "category": "music",\n'
        '          "local_path": "templates/kenney_mock/assets/music/loop.ogg",\n'
        '          "checksum_sha256": "na",\n'
        '          "compatible_genres": ["shooter"],\n'
        '          "tags": ["music"],\n'
        '          "source": {\n'
        '            "provider": "Kenney",\n'
        '            "author": "Kenney",\n'
        '            "source_url": "https://kenney.nl/assets/ui-pack",\n'
        '            "download_url": "https://kenney.nl/assets/ui-pack.zip",\n'
        '            "license": "CC0",\n'
        '            "attribution": "Kenney"\n'
        '          }\n'
        '        },\n'
        '        {\n'
        '          "asset_id": "sprites",\n'
        '          "category": "sprites",\n'
        '          "local_path": "templates/kenney_mock/assets/sprites/hero.png",\n'
        '          "checksum_sha256": "na",\n'
        '          "compatible_genres": ["shooter"],\n'
        '          "tags": ["sprites"],\n'
        '          "source": {\n'
        '            "provider": "Kenney",\n'
        '            "author": "Kenney",\n'
        '            "source_url": "https://kenney.nl/assets/ui-pack",\n'
        '            "download_url": "https://kenney.nl/assets/ui-pack.zip",\n'
        '            "license": "CC0",\n'
        '            "attribution": "Kenney"\n'
        '          }\n'
        '        },\n'
        '        {\n'
        '          "asset_id": "tiles",\n'
        '          "category": "tiles",\n'
        '          "local_path": "templates/kenney_mock/assets/tiles/ground.png",\n'
        '          "checksum_sha256": "na",\n'
        '          "compatible_genres": ["shooter"],\n'
        '          "tags": ["tiles"],\n'
        '          "source": {\n'
        '            "provider": "Kenney",\n'
        '            "author": "Kenney",\n'
        '            "source_url": "https://kenney.nl/assets/ui-pack",\n'
        '            "download_url": "https://kenney.nl/assets/ui-pack.zip",\n'
        '            "license": "CC0",\n'
        '            "attribution": "Kenney"\n'
        '          }\n'
        '        }\n'
        '      ]\n'
        '    }\n'
        '  ]\n'
        '}\n',
        encoding="utf-8",
    )


def test_export_preset_bootstrap_when_missing(tmp_path: Path) -> None:
    """POC-001: When template lacks export_presets.cfg, bootstrap auto-injects it."""
    _write_template_no_presets(tmp_path)
    _write_config_with_kenney_mock(tmp_path)

    engine = GameCreationEngine(workspace_root=tmp_path)
    result = engine.create_from_prompt("Create a first person shooter")

    assert result.status == RunStatus.COMPLETED
    assert result.preset_bootstrapped is True
    assert (result.project_dir / "export_presets.cfg").exists()
    content = (result.project_dir / "export_presets.cfg").read_text(encoding="utf-8")
    assert "Windows Desktop" in content


def test_export_preset_preserved_when_present(tmp_path: Path) -> None:
    """POC-001: When template already has presets, they are NOT overwritten."""
    _write_base_template(tmp_path)

    engine = GameCreationEngine(workspace_root=tmp_path)
    result = engine.create_from_prompt("Create a tiny platformer")

    assert result.status == RunStatus.COMPLETED
    assert result.preset_bootstrapped is False
    content = (result.project_dir / "export_presets.cfg").read_text(encoding="utf-8")
    # Original test template has a 4-line preset — should still be short
    assert "runnable=true" in content


def test_gate_d_failure_prevents_completed_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """POC-002: If Gate D headless validation fails, run cannot be COMPLETED."""
    _write_base_template(tmp_path)

    # Mock subprocess.run to simulate Gate D import failure
    import orchestration.game_creation as gc_module

    call_count = {"n": 0}

    def _fake_subprocess_run(args, stdout, stderr=None, timeout=None, check=False):
        call_count["n"] += 1
        # Simulate import failure (non-zero exit)
        class FakeResult:
            returncode = 1
        if stdout and hasattr(stdout, "write"):
            stdout.write("ERROR: Failed to import project\n")
        return FakeResult()

    monkeypatch.setattr(gc_module.subprocess, "run", _fake_subprocess_run)

    engine = GameCreationEngine(workspace_root=tmp_path)
    result = engine.create_from_prompt(
        "Create a tiny platformer",
        godot_exe="godot4",
    )

    assert result.status == RunStatus.FAILED
    assert "gate_d_failed" in (result.validation_report.summary or "")


def test_run_bundle_contains_gate_log_paths(tmp_path: Path) -> None:
    """POC-005: Run bundle JSON includes gate_d_log_paths and gate_e_log_paths keys."""
    _write_base_template(tmp_path)

    engine = GameCreationEngine(workspace_root=tmp_path)
    result = engine.create_from_prompt("Create a tiny platformer")

    assert result.run_bundle_path.exists()
    bundle = json.loads(result.run_bundle_path.read_text(encoding="utf-8"))
    assert "gate_d_log_paths" in bundle
    assert "gate_e_log_paths" in bundle
    assert isinstance(bundle["gate_d_log_paths"], list)
    assert isinstance(bundle["gate_e_log_paths"], list)


def test_kenney_style_template_bootstrap_and_structural_validation(tmp_path: Path) -> None:
    """End-to-end: Kenney-like template without presets completes structural
    validation and has presets bootstrapped."""
    _write_template_no_presets(tmp_path)
    _write_config_with_kenney_mock(tmp_path)

    events: list[str] = []
    engine = GameCreationEngine(workspace_root=tmp_path)
    result = engine.create_from_prompt(
        "Create an fps demo",
        progress_callback=lambda msg: events.append(msg),
    )

    assert result.status == RunStatus.COMPLETED
    assert result.preset_bootstrapped is True
    # Verify the bootstrap was logged
    bootstrap_events = [e for e in events if "preset_bootstrapped=True" in e]
    assert len(bootstrap_events) == 1
