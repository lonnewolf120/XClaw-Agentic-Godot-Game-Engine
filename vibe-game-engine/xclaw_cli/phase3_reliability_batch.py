"""Phase 3 reliability batch: run several varied prompts through the keyless game loop and
report a real pass rate. This is the honest 'does it work repeatedly' measurement, not a single
happy path.

Run:  ./.venv/Scripts/python.exe -m xclaw_cli.phase3_reliability_batch
"""
from __future__ import annotations

from xclaw_cli.game_engine import generate_game

PROMPTS = [
    ("single_min",
     "A short single-level 2D platformer: run right to a goal flag, collect 3 coins along the way, "
     "with one enemy sitting on a ledge above the path. 1 life, a main menu and restart."),
    ("three_levels_chaser",
     "A 2D platformer with THREE levels of increasing length. Each level has a handful of coins and "
     "one CHASING enemy placed on a ledge above the route. 5 lives, main menu, game-over and restart."),
    ("coin_collector",
     "A 2D coin-collector platformer: one large level packed with coins on the ground and on ledges, "
     "two patrolling enemies up on raised platforms, and a goal at the far right. 2 lives."),
    ("double_jump",
     "A 2D platformer where the player can double jump (a second jump in mid-air). Two levels, one "
     "spike hazard per level off the main path, reach the goal at the right. 3 lives, menu and restart."),
]


def main() -> int:
    results = []
    for name, prompt in PROMPTS:
        print(f"\n========== PROMPT: {name} ==========", flush=True)
        try:
            res = generate_game(
                prompt,
                provider="claude-code",
                max_attempts=4,
                on_event=lambda m, n=name: print(f"[{n}] {m}", flush=True),
            )
            results.append((name, res.ok, res.attempts, res.run_id))
        except Exception as exc:  # keep the batch going on a single prompt's failure
            print(f"[{name}] EXCEPTION: {type(exc).__name__}: {exc}", flush=True)
            results.append((name, False, 0, "exception"))

    passed = sum(1 for _, ok, _, _ in results if ok)
    print("\n\n================ BATCH SUMMARY ================")
    for name, ok, attempts, run_id in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name:24s} attempts={attempts} run={run_id}")
    print(f"\nXCLAW_PHASE3 RELIABILITY pass={passed}/{len(results)} "
          f"rate={passed / max(len(results), 1):.0%}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
