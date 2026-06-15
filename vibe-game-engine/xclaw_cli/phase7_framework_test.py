"""Phase 7 Test: Framework Injection & Validation.

Verifies that:
 1. VibeCore scripts are copied into the workspace.
 2. project.godot is updated with Autoloads.
 3. The project still passes the headless check (valid GDScript).
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure the parent is on sys.path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from xclaw_cli import config
from xclaw_cli.headless import GodotHeadless
from xclaw_cli.workspace import prepare_workspace


def test_core_injection():
    """Verify scripts and autoloads exist in a new workspace."""
    project_dir, run_id = prepare_workspace("Starter-Kit-3D-Platformer")
    
    # 1. Check Files
    core_dir = project_dir / "vibe_core"
    assert core_dir.exists()
    assert (core_dir / "events.gd").exists()
    assert (core_dir / "global_state.gd").exists()
    assert (core_dir / "vibe_entity.gd").exists()
    print(f"  [PASS] Files found in {core_dir}")
    
    # 2. Check Autoloads in project.godot
    godot_file = project_dir / "project.godot"
    content = godot_file.read_text(encoding="utf-8")
    assert 'VibeEvents="*res://vibe_core/events.gd"' in content
    assert 'VibeState="*res://vibe_core/global_state.gd"' in content
    print(f"  [PASS] Autoloads injected into project.godot")
    
    # 3. Headless Validation (Godot Gate)
    godot = GodotHeadless(config.resolve_godot_exe())
    print("  Checking headless validation (this may take a few seconds)...")
    godot.import_project(project_dir) # Import first
    check = godot.check(project_dir)
    assert check.ok, f"Project FAILED headless check after injection: {check.summary()}"
    print(f"  [PASS] Headless gate: {check.summary()}")
    
    # Cleanup
    import shutil
    shutil.rmtree(project_dir.parent, ignore_errors=True)
    return "OK"

if __name__ == "__main__":
    print("\n" + "="*60)
    print("TEST: Phase 7 Framework Integration")
    print("="*60)
    try:
        res = test_core_injection()
        print(f"\nPHASE7_RESULT={res}")
        sys.exit(0)
    except Exception as exc:
        import traceback
        traceback.print_exc()
        print(f"\nPHASE7_RESULT=FAIL ({exc})")
        sys.exit(1)
