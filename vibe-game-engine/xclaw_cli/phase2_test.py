"""Phase 2: prove the self-correction loop converges from a real headless error and
respects the retry cap. Deterministic generator stands in for the LLM.

The gate (`--editor --quit`) only validates scripts the project actually loads, so the
test mutates a REFERENCED script (player.gd, attached to player.tscn).

    python -m xclaw_cli.phase2_test
"""
from __future__ import annotations

import sys

from xclaw_cli import config
from xclaw_cli.edits import FileWrite, read_file
from xclaw_cli.headless import GodotHeadless
from xclaw_cli.loop import LoopContext, run_loop
from xclaw_cli.workspace import prepare_workspace

TEMPLATE = "Starter-Kit-3D-Platformer"
TARGET = "res://scripts/player.gd"
BAD_SUFFIX = "\nfunc _xclaw_broken(:\n\tpass\n"  # parse error: bad param list


def make_generator(original: str):
    """attempt 1 -> break the referenced script; later attempts -> restore valid content."""
    def generator(ctx: LoopContext) -> list[FileWrite]:
        if ctx.attempt == 1:
            return [FileWrite(TARGET, original + BAD_SUFFIX)]
        return [FileWrite(TARGET, original)]  # repair, informed by ctx.last_errors
    return generator


def _log(msg: str) -> None:
    print(f"[phase2] {msg}", flush=True)


def main() -> int:
    godot = GodotHeadless(config.resolve_godot_exe())

    # Case 1: converges within the cap (broken on attempt 1, fixed on attempt 2).
    project_dir, run_id = prepare_workspace(TEMPLATE)
    original = read_file(project_dir, TARGET)
    if original is None:
        _log("FAIL: could not read player.gd")
        return 1
    _log(f"converge-case run_id={run_id}")
    result = run_loop(project_dir, "probe", make_generator(original), godot, max_attempts=3, on_event=_log)
    if not (result.ok and result.attempts == 2):
        _log(f"FAIL: expected ok at attempt 2, got ok={result.ok} attempts={result.attempts}")
        if result.final_check:
            _log(f"  errors: {result.final_check.errors[:3]}")
        return 1
    _log("converged at attempt 2 as expected")

    # Case 2: cap respected — max_attempts=1 cannot recover (generator only fixes on attempt>=2).
    project_dir2, run_id2 = prepare_workspace(TEMPLATE)
    _log(f"cap-case run_id={run_id2}")
    capped = run_loop(project_dir2, "probe", make_generator(original), godot, max_attempts=1, on_event=_log)
    if capped.ok or capped.attempts != 1:
        _log(f"FAIL: cap not respected, ok={capped.ok} attempts={capped.attempts}")
        return 1
    _log("cap respected: failed after 1 attempt without recovery")

    _log("PHASE 2 PASS: loop self-corrects from a real headless error and honors the cap.")
    print("PHASE2_RESULT=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
