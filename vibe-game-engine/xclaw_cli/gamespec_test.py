"""Run as a module:  python -m xclaw_cli.gamespec_test
Self-contained checks for the GameSpec validator (no pytest dependency)."""
from __future__ import annotations

from xclaw_cli import gamespec


def _valid_spec() -> dict:
    return {
        "meta": {"title": "T", "dimension": "2d", "genre": "platformer"},
        "progression": {"lives": 3, "win": "clear_all_levels"},
        "player": {"script": "res://scripts/player.gd", "size": {"w": 32, "h": 48}},
        "levels": [
            {
                "name": "Level 1",
                "bounds": {"w": 2000, "h": 720},
                "player_spawn": {"x": 100, "y": 400},
                "platforms": [{"x": 0, "y": 600, "w": 800, "h": 40}],
                "hazards": [{"type": "spike", "x": 880, "y": 580, "w": 64, "h": 20}],
                "enemies": [{"type": "patroller", "x": 1200, "y": 560, "patrol": 200}],
                "collectibles": [{"type": "coin", "x": 500, "y": 520, "score": 10}],
                "goal": {"x": 1900, "y": 560, "w": 48, "h": 64},
                "input_plan": [{"action": "ui_right", "frames": 120}, {"action": "ui_accept", "frames": 1}],
            }
        ],
    }


def _expect(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def main() -> int:
    passed = 0

    # 1. A well-formed spec validates clean.
    errs = gamespec.validate(_valid_spec())
    _expect(errs == [], f"valid spec should pass, got: {errs}")
    passed += 1

    # 2. written_paths cross-check.
    errs = gamespec.validate(_valid_spec(), written_paths={"res://scripts/player.gd"})
    _expect(errs == [], f"valid spec w/ matching written_paths should pass, got: {errs}")
    errs = gamespec.validate(_valid_spec(), written_paths={"res://scripts/other.gd"})
    _expect(any("not among files" in e for e in errs), "missing player.script write should fail")
    passed += 1

    # 3. Wrong dimension fails.
    s = _valid_spec(); s["meta"]["dimension"] = "3d"
    _expect(any("dimension" in e for e in gamespec.validate(s)), "3d should fail")
    passed += 1

    # 4. Unknown enemy type fails (no silent drop).
    s = _valid_spec(); s["levels"][0]["enemies"][0]["type"] = "boss"
    _expect(any("enemies[0].type" in e for e in gamespec.validate(s)), "unknown enemy type should fail")
    passed += 1

    # 5. Missing goal fails.
    s = _valid_spec(); del s["levels"][0]["goal"]
    _expect(any("goal" in e for e in gamespec.validate(s)), "missing goal should fail")
    passed += 1

    # 6. No platforms fails.
    s = _valid_spec(); s["levels"][0]["platforms"] = []
    _expect(any("platforms" in e for e in gamespec.validate(s)), "no platforms should fail")
    passed += 1

    # 7. Out-of-bounds coordinate fails.
    s = _valid_spec(); s["levels"][0]["goal"]["x"] = 99999
    _expect(any("outside level bounds" in e for e in gamespec.validate(s)), "OOB goal should fail")
    passed += 1

    # 8. Bad input_plan action fails.
    s = _valid_spec(); s["levels"][0]["input_plan"][0]["action"] = "jump"
    _expect(any("input_plan" in e for e in gamespec.validate(s)), "non-builtin action should fail")
    passed += 1

    # 9. Empty levels fails.
    s = _valid_spec(); s["levels"] = []
    _expect(any("levels" in e for e in gamespec.validate(s)), "empty levels should fail")
    passed += 1

    print(f"GAMESPEC_TEST RESULT verdict=PASS checks={passed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
