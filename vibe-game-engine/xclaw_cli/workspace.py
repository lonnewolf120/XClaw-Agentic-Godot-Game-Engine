"""Isolated run workspaces built from a (valid, human-made) Kenney template."""
from __future__ import annotations

import re
import shutil
import stat
from datetime import datetime, timezone
from pathlib import Path

from xclaw_cli import config

VIBE_CORE_SRC = config.XCLAW_DIR / "vibe_core_src"
VIBE_GAME_SRC = config.XCLAW_DIR / "vibe_game_src"


def new_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    return f"xrun-{stamp}"


def _make_writable(root: Path) -> None:
    # Templates copied from read-only sources can carry read-only bits on Windows.
    for path in root.rglob("*"):
        if path.is_file():
            path.chmod(path.stat().st_mode | stat.S_IWRITE)


def _inject_autoloads(project_dir: Path) -> None:
    """Add VibeCore autoloads to project.godot if missing."""
    godot_file = project_dir / "project.godot"
    if not godot_file.exists():
        return
    
    content = godot_file.read_text(encoding="utf-8")
    
    autoload_section = "[autoload]\n\nVibeEvents=\"*res://vibe_core/events.gd\"\nVibeState=\"*res://vibe_core/global_state.gd\"\nVibeTraits=\"*res://vibe_core/trait_applier.gd\"\nVibeHUD=\"*res://vibe_core/hud.gd\"\n"
    
    if "[autoload]" in content:
        # If section exists, append our specific ones if not there
        if "VibeEvents" not in content:
            content = content.replace("[autoload]", "[autoload]\n\nVibeEvents=\"*res://vibe_core/events.gd\"")
        if "VibeState" not in content:
            content = content.replace("[autoload]", "[autoload]\n\nVibeState=\"*res://vibe_core/global_state.gd\"")
        if "VibeTraits" not in content:
            content = content.replace("[autoload]", "[autoload]\n\nVibeTraits=\"*res://vibe_core/trait_applier.gd\"")
        if "VibeHUD" not in content:
            content = content.replace("[autoload]", "[autoload]\n\nVibeHUD=\"*res://vibe_core/hud.gd\"")
    else:
        # Append section to end
        content += "\n" + autoload_section
        
    godot_file.write_text(content, encoding="utf-8")


def _inject_game_autoload_and_boot(project_dir: Path) -> None:
    """Register the GameManager autoload (after VibeCore) and set the boot main_scene.

    GameManager connects to VibeEvents in _ready, so it must load AFTER the VibeCore
    autoloads — appending its line keeps that order.
    """
    godot_file = project_dir / "project.godot"
    if not godot_file.exists():
        return
    content = godot_file.read_text(encoding="utf-8")

    if "GameManager=" not in content:
        line = 'GameManager="*res://vibe_game/game_manager.gd"\n'
        if "[autoload]" in content:
            # Append after the existing autoload block's known last entry if present,
            # otherwise right after the section header.
            anchor = 'VibeHUD="*res://vibe_core/hud.gd"\n'
            if anchor in content:
                content = content.replace(anchor, anchor + line, 1)
            else:
                content = content.replace("[autoload]", "[autoload]\n\n" + line, 1)
        else:
            content += '\n[autoload]\n\n' + line

    # Point the project at the boot scene so a plain run plays the menu->levels game.
    if 'run/main_scene="res://vibe_game/boot.tscn"' not in content:
        if "run/main_scene=" in content:
            content = re.sub(
                r'run/main_scene="[^"]*"',
                'run/main_scene="res://vibe_game/boot.tscn"',
                content,
                count=1,
            )
        else:
            content = content.replace(
                "[application]",
                '[application]\n\nrun/main_scene="res://vibe_game/boot.tscn"',
                1,
            )
    godot_file.write_text(content, encoding="utf-8")


def prepare_workspace(
    template_name: str,
    run_id: str | None = None,
    inject_game_runtime: bool = False,
) -> tuple[Path, str]:
    """Copy `templates/<template_name>` into an isolated run dir.

    Returns (project_dir, run_id). Raises FileNotFoundError if the template (or its
    project.godot) is missing.

    When ``inject_game_runtime`` is True, also copy the schema-driven ``vibe_game/`` runtime,
    register the GameManager autoload, and set the boot scene as main_scene. The legacy
    single-LLM path leaves this False so it is unaffected.
    """
    run_id = run_id or new_run_id()
    source = config.TEMPLATES_DIR / template_name
    if not (source / "project.godot").exists():
        raise FileNotFoundError(f"Template has no project.godot: {source}")

    project_dir = config.RUNS_DIR / run_id / "project"
    project_dir.parent.mkdir(parents=True, exist_ok=True)

    shutil.copytree(
        source,
        project_dir,
        ignore=shutil.ignore_patterns(".godot", ".import", "export", ".git"),
        dirs_exist_ok=False,
    )
    _make_writable(project_dir)

    # Inject Vibe Core
    vibe_core_dest = project_dir / "vibe_core"
    if VIBE_CORE_SRC.is_dir():
        shutil.copytree(VIBE_CORE_SRC, vibe_core_dest, dirs_exist_ok=True)
        _inject_autoloads(project_dir)

    # Inject the schema-driven game runtime (opt-in).
    if inject_game_runtime and VIBE_GAME_SRC.is_dir():
        shutil.copytree(VIBE_GAME_SRC, project_dir / "vibe_game", dirs_exist_ok=True)
        _inject_game_autoload_and_boot(project_dir)

    return project_dir, run_id
