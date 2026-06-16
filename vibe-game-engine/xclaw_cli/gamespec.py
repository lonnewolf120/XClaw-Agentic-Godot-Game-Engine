"""GameSpec — the shared contract between the deterministic `vibe_game/` runtime and the
auto playtest gate.

The AI (or a human, in Phase 1) emits a `game_spec.json`. This module validates it BEFORE any
build so structured errors can feed back into the agentic loop, exactly like the headless error
markers do. The same JSON is read by `vibe_game/game_manager.gd` (to build the game) and by
`vibe_game/playtest_harness.gd` (to know what to verify).

Coordinate convention: Godot 2D, y is DOWN-positive. Larger y = lower on screen. Ground
platforms therefore have a LARGER y than the player spawn above them.

Scope (this phase): 2D only. Known archetypes:
  hazards:      spike, pit
  enemies:      patroller, chaser
  collectibles: coin
Unknown types fail validation (no silent drop).
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

HAZARD_TYPES = {"spike", "pit"}
ENEMY_TYPES = {"patroller", "chaser"}
COLLECTIBLE_TYPES = {"coin"}
BUILTIN_INPUT_ACTIONS = {"ui_left", "ui_right", "ui_up", "ui_down", "ui_accept"}


class SpecError(ValueError):
    """Raised when a GameSpec is structurally invalid. `errors` is the full list."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors) if errors else "invalid game spec")


def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _check_point(obj: Any, where: str, errs: list[str], need: tuple[str, ...] = ("x", "y")) -> None:
    if not isinstance(obj, dict):
        errs.append(f"{where}: expected an object with {need}, got {type(obj).__name__}")
        return
    for key in need:
        if key not in obj:
            errs.append(f"{where}: missing '{key}'")
        elif not _is_number(obj[key]):
            errs.append(f"{where}.{key}: must be a finite number")


def _check_size_positive(obj: dict, where: str, errs: list[str]) -> None:
    for key in ("w", "h"):
        if key in obj and not (_is_number(obj[key]) and obj[key] > 0):
            errs.append(f"{where}.{key}: size must be a positive finite number")


def _in_bounds(obj: dict, bounds: dict, where: str, errs: list[str]) -> None:
    """Soft bounds check for x/y if both the point and bounds are well-formed."""
    bw, bh = bounds.get("w"), bounds.get("h")
    if not (_is_number(bw) and _is_number(bh)):
        return
    x, y = obj.get("x"), obj.get("y")
    if _is_number(x) and not (0 <= x <= bw):
        errs.append(f"{where}.x={x} outside level bounds [0, {bw}]")
    if _is_number(y) and not (0 <= y <= bh):
        errs.append(f"{where}.y={y} outside level bounds [0, {bh}]")


def _validate_level(level: Any, idx: int, errs: list[str]) -> None:
    where = f"levels[{idx}]"
    if not isinstance(level, dict):
        errs.append(f"{where}: expected an object")
        return

    bounds = level.get("bounds")
    if not isinstance(bounds, dict):
        errs.append(f"{where}.bounds: required object with w,h")
        bounds = {}
    else:
        _check_size_positive(bounds, f"{where}.bounds", errs)

    if "player_spawn" not in level:
        errs.append(f"{where}.player_spawn: required")
    else:
        _check_point(level["player_spawn"], f"{where}.player_spawn", errs)
        if isinstance(level.get("player_spawn"), dict):
            _in_bounds(level["player_spawn"], bounds, f"{where}.player_spawn", errs)

    platforms = level.get("platforms")
    if not isinstance(platforms, list) or len(platforms) < 1:
        errs.append(f"{where}.platforms: at least one platform required")
    else:
        for i, p in enumerate(platforms):
            pw = f"{where}.platforms[{i}]"
            _check_point(p, pw, errs)
            if isinstance(p, dict):
                _check_size_positive(p, pw, errs)
                if "w" not in p or "h" not in p:
                    errs.append(f"{pw}: platform needs w and h")

    if "goal" not in level:
        errs.append(f"{where}.goal: required")
    else:
        _check_point(level["goal"], f"{where}.goal", errs)
        if isinstance(level.get("goal"), dict):
            _in_bounds(level["goal"], bounds, f"{where}.goal", errs)

    for i, h in enumerate(level.get("hazards", []) or []):
        _check_typed_entity(h, HAZARD_TYPES, f"{where}.hazards[{i}]", errs)
    for i, e in enumerate(level.get("enemies", []) or []):
        _check_typed_entity(e, ENEMY_TYPES, f"{where}.enemies[{i}]", errs)
    for i, c in enumerate(level.get("collectibles", []) or []):
        _check_typed_entity(c, COLLECTIBLE_TYPES, f"{where}.collectibles[{i}]", errs)

    plan = level.get("input_plan")
    if plan is not None:
        if not isinstance(plan, list):
            errs.append(f"{where}.input_plan: must be a list of steps if present")
        else:
            for i, step in enumerate(plan):
                sw = f"{where}.input_plan[{i}]"
                if not isinstance(step, dict):
                    errs.append(f"{sw}: expected an object")
                    continue
                action = step.get("action")
                if action not in BUILTIN_INPUT_ACTIONS:
                    errs.append(
                        f"{sw}.action={action!r}: must be one of {sorted(BUILTIN_INPUT_ACTIONS)}"
                    )
                if not (isinstance(step.get("frames"), int) and step["frames"] >= 1):
                    errs.append(f"{sw}.frames: must be an integer >= 1")


def _check_typed_entity(obj: Any, allowed: set[str], where: str, errs: list[str]) -> None:
    if not isinstance(obj, dict):
        errs.append(f"{where}: expected an object")
        return
    _check_point(obj, where, errs)
    t = obj.get("type")
    if t not in allowed:
        errs.append(f"{where}.type={t!r}: must be one of {sorted(allowed)}")


def validate(spec: Any, *, written_paths: set[str] | None = None) -> list[str]:
    """Return a list of human-readable error strings. Empty list == valid."""
    errs: list[str] = []
    if not isinstance(spec, dict):
        return ["game_spec must be a JSON object"]

    meta = spec.get("meta")
    if not isinstance(meta, dict):
        errs.append("meta: required object")
    else:
        dim = (meta.get("dimension") or "").lower()
        if dim != "2d":
            errs.append(f"meta.dimension={meta.get('dimension')!r}: only '2d' supported in this scope")

    player = spec.get("player")
    if not isinstance(player, dict):
        errs.append("player: required object")
    else:
        script = player.get("script")
        if not (isinstance(script, str) and script.startswith("res://") and script.endswith(".gd")):
            errs.append("player.script: must be a res:// path to a .gd file")
        elif written_paths is not None and script not in written_paths:
            errs.append(f"player.script={script!r}: not among files the run wrote {sorted(written_paths)}")

    progression = spec.get("progression")
    if not isinstance(progression, dict):
        errs.append("progression: required object")
    else:
        lives = progression.get("lives")
        if not (isinstance(lives, int) and lives >= 1):
            errs.append("progression.lives: integer >= 1 required")

    levels = spec.get("levels")
    if not isinstance(levels, list) or len(levels) < 1:
        errs.append("levels: non-empty list required")
    else:
        for idx, level in enumerate(levels):
            _validate_level(level, idx, errs)

    return errs


def load_and_validate(path: str | Path, *, written_paths: set[str] | None = None) -> dict:
    """Load a game_spec.json, validate it, and return the dict. Raises SpecError on failure."""
    p = Path(path)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SpecError([f"game_spec not found: {p}"])
    except json.JSONDecodeError as exc:
        raise SpecError([f"game_spec is not valid JSON: {exc}"])
    errs = validate(data, written_paths=written_paths)
    if errs:
        raise SpecError(errs)
    return data
