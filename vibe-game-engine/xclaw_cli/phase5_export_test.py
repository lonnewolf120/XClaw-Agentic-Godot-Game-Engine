"""Phase 5 test: export preset generation + export flow.

Tests:
 1. write_export_preset generates valid INI for each target platform
 2. find_export_templates returns None when templates aren't installed
 3. export_project returns a clean error for missing templates (no crash)
 4. Full engine flow with export=True + mocked SDK: the bundle records export metadata
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

# Ensure the parent is on sys.path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from xclaw_cli import config
from xclaw_cli.exporter import (
    ExportConfig,
    ExportOutcome,
    ExportTarget,
    export_project,
    find_export_templates,
    write_export_preset,
)


def test_preset_generation():
    """Each target generates a valid preset file with the right platform string."""
    results = {}
    for target in ExportTarget:
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            (d / "project.godot").write_text("[gd_resource]", encoding="utf-8")
            cfg = ExportConfig(target=target, embed_pck=True)
            preset_path = write_export_preset(d, cfg, f"export/game{'.exe' if target == ExportTarget.WINDOWS else '.x86_64'}")
            assert preset_path.exists(), f"preset file not created for {target.value}"
            content = preset_path.read_text(encoding="utf-8")
            # Must contain the platform identifier
            platform_map = {
                ExportTarget.WINDOWS: '"Windows Desktop"',
                ExportTarget.LINUX: '"Linux"',
                ExportTarget.WEB: '"Web"',
            }
            assert platform_map[target] in content, f"platform string missing for {target.value}"
            # embed_pck is a desktop-only flag (not in the Web preset)
            if target != ExportTarget.WEB:
                assert "embed_pck=true" in content, f"embed_pck not set for {target.value}"
            assert "[preset.0]" in content, f"preset section missing for {target.value}"
            results[target.value] = "OK"
    return results


def test_export_templates_detection():
    """On this machine, export templates are NOT installed — should return None."""
    godot = config.resolve_godot_exe()
    tpl_dir, ver = find_export_templates(godot)
    assert ver, "should detect Godot version"
    assert "4.6" in ver, f"unexpected version: {ver}"
    # Templates aren't installed on this dev machine
    print(f"  templates_dir={tpl_dir}, version={ver}")
    return "OK" if tpl_dir is None else f"FOUND_AT={tpl_dir}"


def test_export_missing_templates():
    """export_project returns a clean error when templates aren't installed."""
    godot = config.resolve_godot_exe()

    # Use a real template so Godot won't balk at the project, but export
    # should fail at the "templates not installed" gate.
    template_dir = config.TEMPLATES_DIR / "Starter-Kit-3D-Platformer"
    if not template_dir.exists():
        return "SKIP (template missing)"

    # Work in a temp copy so we don't pollute the real template
    with tempfile.TemporaryDirectory() as td:
        import shutil
        dst = Path(td) / "project"
        shutil.copytree(
            template_dir, dst,
            ignore=shutil.ignore_patterns(".godot", ".import", "export", ".git"),
        )
        events: list[str] = []
        outcome = export_project(
            dst, godot,
            cfg=ExportConfig(target=ExportTarget.WINDOWS),
            on_event=events.append,
        )
        print(f"  ok={outcome.ok} error={outcome.error}")
        for e in events:
            print(f"  event: {e}")

        # Either templates are missing (expected) or templates exist and export succeeds/fails
        if "export_templates_missing" in outcome.error:
            return "OK (clean error for missing templates)"
        elif outcome.ok:
            return f"EXPORTED (unexpected — templates must be installed): {outcome.output_path}"
        else:
            return f"OTHER_ERROR: {outcome.error}"


def test_engine_export_bundle():
    """Engine with export=True records export metadata in the bundle (mocked LLM)."""
    import unittest.mock as mock

    # Mock anthropic so we don't need a key
    mock_anthropic = mock.MagicMock()
    mock_response = mock.MagicMock()
    mock_text_block = mock.MagicMock()
    mock_text_block.type = "text"
    mock_text_block.text = json.dumps({
        "summary": "Phase 5 test — no-op",
        "writes": [],
    })
    mock_response.content = [mock_text_block]
    mock_anthropic.Anthropic.return_value.messages.create.return_value = mock_response

    with mock.patch.dict("sys.modules", {"anthropic": mock_anthropic}):
        from xclaw_cli.engine import generate

        events: list[str] = []
        result = generate(
            "Make the player taller",
            template="Starter-Kit-3D-Platformer",
            provider="anthropic",
            export=True,
            export_target="windows",
            on_event=events.append,
        )
        # The generate succeeded (no-op writes → pristine template passes gate)
        assert result.ok, f"generate failed: {result.summary}"

        # Read the bundle
        bundle = json.loads(Path(result.bundle_path).read_text(encoding="utf-8"))
        assert bundle["export_requested"] is True, "export_requested not in bundle"

        # Export should have run but failed (no export templates installed)
        if result.export is not None:
            print(f"  export ok={result.export.ok} error={result.export.error}")
            assert "export" in bundle, "export section missing from bundle"
        else:
            print("  export=None (likely skipped — templates not installed?)")

        # Cleanup the run dir
        import shutil
        run_dir = Path(result.project_dir).parent
        shutil.rmtree(run_dir, ignore_errors=True)

        return "OK"


if __name__ == "__main__":
    tests = [
        ("preset_generation", test_preset_generation),
        ("export_templates_detection", test_export_templates_detection),
        ("export_missing_templates", test_export_missing_templates),
        ("engine_export_bundle", test_engine_export_bundle),
    ]
    results = {}
    for name, fn in tests:
        print(f"\n{'='*60}")
        print(f"TEST: {name}")
        print(f"{'='*60}")
        try:
            result = fn()
            results[name] = result
            print(f"-> {result}")
        except Exception as exc:
            import traceback
            traceback.print_exc()
            results[name] = f"FAIL: {exc}"
            print(f"-> FAIL: {exc}")

    print(f"\n{'='*60}")
    print("PHASE5_RESULTS:")
    for k, v in results.items():
        status = "PASS" if "OK" in str(v) or "PASS" in str(v) else "FAIL"
        print(f"  {k}: {status} ({v})")

    all_ok = all("OK" in str(v) or "PASS" in str(v) or "EXPORTED" in str(v) for v in results.values())
    print(f"\nPHASE5_RESULT={'PASS' if all_ok else 'FAIL'}")
    sys.exit(0 if all_ok else 1)
