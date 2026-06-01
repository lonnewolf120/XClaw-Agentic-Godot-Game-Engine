"""Isolated run workspaces built from a (valid, human-made) Kenney template."""
from __future__ import annotations

import shutil
import stat
from datetime import datetime, timezone
from pathlib import Path

from xclaw_cli import config


def new_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    return f"xrun-{stamp}"


def _make_writable(root: Path) -> None:
    # Templates copied from read-only sources can carry read-only bits on Windows.
    for path in root.rglob("*"):
        if path.is_file():
            path.chmod(path.stat().st_mode | stat.S_IWRITE)


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
    return project_dir, run_id
