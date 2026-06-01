"""Environment + path resolution for the XClaw headless engine."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

# .../XClaw Agentic Godot Game Engine/vibe-game-engine/xclaw_cli/config.py
#   parents[0] = xclaw_cli, parents[1] = vibe-game-engine, parents[2] = repo root
XCLAW_DIR = Path(__file__).resolve().parent
VIBE_DIR = XCLAW_DIR.parent
REPO_ROOT = VIBE_DIR.parent

TEMPLATES_DIR = VIBE_DIR / "templates"
RUNS_DIR = XCLAW_DIR / "runs"
SCRATCH_DIR = XCLAW_DIR / ".scratch"

# Phase 0 confirmed: the GUI Godot.exe streams headless output through a pipe; the
# `_console.exe` wrapper on this box is broken (looks for a missing sibling binary).
_GODOT_CANDIDATES = (
    r"D:\Software\Godot\Godot.exe",
    "godot",
    "godot4",
)


def resolve_godot_exe() -> str:
    """Return a usable Godot 4.x executable, or raise FileNotFoundError.

    Override with the XCLAW_GODOT_EXE env var.
    """
    override = os.environ.get("XCLAW_GODOT_EXE", "").strip()
    if override:
        if Path(override).exists() or shutil.which(override):
            return override
        raise FileNotFoundError(f"XCLAW_GODOT_EXE set but not found: {override}")

    for candidate in _GODOT_CANDIDATES:
        if Path(candidate).exists():
            return candidate
        found = shutil.which(candidate)
        if found:
            return found

    raise FileNotFoundError(
        "Godot executable not found. Set XCLAW_GODOT_EXE to your Godot 4.x binary."
    )
