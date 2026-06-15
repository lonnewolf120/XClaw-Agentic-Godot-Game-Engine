"""Isolated run workspaces built from a (valid, human-made) Kenney template."""
from __future__ import annotations

import shutil
import stat
from datetime import datetime, timezone
from pathlib import Path

from xclaw_cli import config

VIBE_CORE_SRC = config.XCLAW_DIR / "vibe_core_src"


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


def prepare_workspace(template_name: str, run_id: str | None = None) -> tuple[Path, str]:
    """Copy `templates/<template_name>` into an isolated run dir.

    Returns (project_dir, run_id). Raises FileNotFoundError if the template (or its
    project.godot) is missing.
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

    return project_dir, run_id
