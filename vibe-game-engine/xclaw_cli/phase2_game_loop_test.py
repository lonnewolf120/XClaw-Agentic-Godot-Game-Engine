"""Phase 2 proof: NL prompt -> full playable game -> green playtest, keyless (claude-code).

Run:  ./.venv/Scripts/python.exe -m xclaw_cli.phase2_game_loop_test
"""
from __future__ import annotations

from xclaw_cli.game_engine import generate_game

PROMPT = (
    "A 2D greybox platformer with TWO levels. The player runs right and jumps to reach a goal at "
    "the far right of each level. Scatter a few coins to collect for score, add one patrolling "
    "enemy and one spike hazard per level (off the main path), 3 lives, with a main menu, "
    "game-over screen and restart."
)


def main() -> int:
    res = generate_game(
        PROMPT,
        provider="claude-code",
        max_attempts=4,
        on_event=lambda m: print("[phase2]", m, flush=True),
    )
    print(
        f"\nXCLAW_PHASE2 RESULT verdict={'PASS' if res.ok else 'FAIL'} "
        f"attempts={res.attempts} run={res.run_id} project={res.project_dir}"
    )
    return 0 if res.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
