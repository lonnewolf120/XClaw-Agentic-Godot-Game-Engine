"""Phase 1 proof: schema + vibe_game runtime + playtest gate, NO LLM.

Builds a workspace from a bare 2D template, injects the schema-driven runtime, drops in a
hand-authored game_spec.json + player.gd, and runs the playtest harness in real headless Godot.
Green here means the scaffold + gate plumbing work end-to-end with zero model variance.

Run:  ./.venv/Scripts/python.exe -m xclaw_cli.phase1_game_authoring_test
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from xclaw_cli import config, gamespec, workspace
from xclaw_cli.headless import GodotHeadless

FIXTURES = config.XCLAW_DIR / "fixtures" / "phase1"
TEMPLATE = "base_2d_platformer"


def main() -> int:
    print("[phase1] resolving godot...")
    try:
        godot_exe = config.resolve_godot_exe()
    except FileNotFoundError as exc:
        print(f"[phase1] FAIL: {exc}")
        return 2
    print(f"[phase1] godot={godot_exe}")

    # 1. Validate the hand-authored spec up front (the same gate the agentic loop will use).
    spec_src = FIXTURES / "game_spec.json"
    try:
        gamespec.load_and_validate(spec_src, written_paths={"res://scripts/player.gd"})
        print("[phase1] spec valid")
    except gamespec.SpecError as exc:
        print("[phase1] FAIL spec invalid:")
        for e in exc.errors:
            print("   -", e)
        return 2

    # 2. Prepare an isolated workspace with the game runtime injected.
    project_dir, run_id = workspace.prepare_workspace(TEMPLATE, inject_game_runtime=True)
    print(f"[phase1] run_id={run_id} project={project_dir}")

    # 3. Drop in the hand-authored content.
    (project_dir / "scripts").mkdir(exist_ok=True)
    shutil.copyfile(FIXTURES / "player.gd", project_dir / "scripts" / "player.gd")
    shutil.copyfile(spec_src, project_dir / "game_spec.json")

    godot = GodotHeadless(godot_exe, timeout=180)

    # 4. Import + parse-check (catch GDScript errors before running).
    print("[phase1] importing...")
    imp = godot.import_project(project_dir)
    print(f"[phase1] import: {imp.summary()}")
    print("[phase1] parse-check...")
    chk = godot.check(project_dir)
    if not chk.ok:
        print(f"[phase1] FAIL parse-check: {chk.summary()}")
        for e in chk.errors[:20]:
            print("   -", e)
        return 1
    print("[phase1] parse-check ok")

    # 5. Run the playtest gate.
    print("[phase1] running playtest harness...")
    pt = godot.run_playtest(project_dir, timeout=150)
    print(f"[phase1] playtest: {pt.summary()}")
    if pt.errors:
        print("[phase1] script errors during playtest:")
        for e in pt.errors[:20]:
            print("   -", e)

    ok = pt.ok
    print(f"\nXCLAW_PHASE1 RESULT verdict={'PASS' if ok else 'FAIL'} "
          f"checks={pt.checks} failed={pt.failed} run={run_id}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
