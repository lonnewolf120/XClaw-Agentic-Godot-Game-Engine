"""Deterministic proof of Phase 4 template selection (no Godot, no API key).

Asserts that NL prompts resolve to the right template folder, including the tag-collision
case the advisor flagged: "first person shooter" must pick the human-made Kenney FPS kit,
not the micro_fps_3d scaffold (the "3d" tag must not double-count with the dimension score).

    python -m xclaw_cli.phase4_selection_test
"""
from __future__ import annotations

import sys

from xclaw_cli.catalog import DEFAULT_TEMPLATE, load_templates, select_template

# (prompt, expected_folder)
CASES = [
    ("make an arcade racing game with cars", "Starter-Kit-Racing"),
    ("a city builder simulation where you place buildings", "Starter-Kit-City-Builder"),
    ("first person shooter with weapons and enemies", "Starter-Kit-FPS"),
    ("a 3d platformer with double jump and collectible coins", "Starter-Kit-3D-Platformer"),
    ("a 2d platformer where you jump between platforms", "base_2d_platformer"),
    ("a top-down shooter with bullets", "topdown_shooter"),
    ("an endless runner dodging obstacles", "endless_runner"),
    # No genre signal at all -> default kit, never a crash.
    ("make it more fun", DEFAULT_TEMPLATE),
]


def _log(m: str) -> None:
    print(f"[phase4-select] {m}", flush=True)


def main() -> int:
    templates = load_templates()
    names = sorted(t.name for t in templates)
    _log(f"loaded {len(templates)} candidate templates: {names}")
    if not templates:
        _log("FAIL: no candidate templates loaded from catalog")
        return 1

    failures = 0
    for prompt, expected in CASES:
        sel = select_template(prompt, templates)
        ok = sel.name == expected
        flag = "OK " if ok else "FAIL"
        _log(f"{flag} {expected:24} <- score={sel.score:>5.1f} got={sel.name:24} | {prompt!r}")
        if not ok:
            _log(f"      reason: {sel.reason}")
            failures += 1

    # A 2D-explicit prompt must NEVER resolve to a 3D kit (all Kenney kits are 3D).
    twod = select_template("a 2d side-scroller", templates)
    twod_info = next(t for t in templates if t.name == twod.name)
    if twod_info.dimension == "3d":
        _log(f"FAIL: 2D prompt resolved to a 3D template ({twod.name})")
        failures += 1
    else:
        _log(f"OK  2D prompt -> {twod_info.dimension} template ({twod_info.name})")

    if failures:
        _log(f"PHASE 4 SELECTION FAIL: {failures} case(s) wrong")
        print("PHASE4_SELECTION_RESULT=FAIL")
        return 1

    _log("PHASE 4 SELECTION PASS: all prompts resolved to the expected template.")
    print("PHASE4_SELECTION_RESULT=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
