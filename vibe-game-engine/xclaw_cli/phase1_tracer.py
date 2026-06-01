"""Phase 1 tracer bullet: prove the apply -> headless-check loop end to end.

No LLM. Hardcoded bounded edit. Run from the vibe-game-engine dir:
    python -m xclaw_cli.phase1_tracer
"""
from __future__ import annotations

import sys
from pathlib import Path

from xclaw_cli import config
from xclaw_cli.headless import GodotHeadless
from xclaw_cli.workspace import prepare_workspace

TEMPLATE = "Starter-Kit-3D-Platformer"


def _log(msg: str) -> None:
    print(f"[phase1] {msg}", flush=True)


def main() -> int:
    godot = GodotHeadless(config.resolve_godot_exe())
    _log(f"godot={godot.godot_exe}")

    project_dir, run_id = prepare_workspace(TEMPLATE)
    _log(f"run_id={run_id} project_dir={project_dir}")

    _log("importing project...")
    imp = godot.import_project(project_dir)
    _log(f"import: {imp.summary()}")

    base = godot.check(project_dir)
    _log(f"baseline check: {base.summary()}")
    if not base.ok:
        _log(f"FAIL: pristine template did not pass: {base.errors[:5]}")
        return 1

    # Bounded edit: raise jump_strength in player.gd (full-file write, line replace).
    player = project_dir / "scripts" / "player.gd"
    text = player.read_text(encoding="utf-8")
    if "@export var jump_strength = 7" not in text:
        _log("FAIL: expected jump_strength line not found in player.gd")
        return 1
    player.write_text(text.replace("@export var jump_strength = 7", "@export var jump_strength = 12"), encoding="utf-8")
    _log("applied edit: jump_strength 7 -> 12")

    after = godot.check(project_dir)
    _log(f"post-edit check: {after.summary()}")
    if not after.ok:
        _log(f"FAIL: valid edit broke the project: {after.errors[:5]}")
        return 1

    # Negative control: confirm the gate CATCHES a real parse error.
    player.write_text(text + "\nfunc broken(:\n\tpass\n", encoding="utf-8")
    broken = godot.check(project_dir)
    _log(f"negative-control check: {broken.summary()}")
    if broken.ok:
        _log("FAIL: gate did NOT catch an injected parse error")
        return 1
    _log(f"gate caught error: {broken.errors[0]}")

    _log("PHASE 1 PASS: apply->check loop works, gate detects valid vs broken.")
    print(f"PHASE1_RESULT=PASS run_id={run_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
