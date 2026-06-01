"""Safe file operations confined to a run workspace.

v1 uses full-file writes only (no fragile in-place patching — that was the bug in the
legacy `local_executor._patch_script`). Paths are sandboxed to the workspace.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileWrite:
    path: str  # "res://..." or a workspace-relative path
    content: str


def _resolve(project_dir: Path, rel: str) -> Path:
    cleaned = rel.replace("res://", "").lstrip("/\\")
    project_dir = project_dir.resolve()
    target = (project_dir / cleaned).resolve()
    if target != project_dir and project_dir not in target.parents:
        raise ValueError(f"path escapes workspace: {rel}")
    return target


def apply_writes(project_dir: str | Path, writes: list[FileWrite]) -> list[str]:
    project_dir = Path(project_dir)
    written: list[str] = []
    for write in writes:
        target = _resolve(project_dir, write.path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(write.content, encoding="utf-8")
        written.append(str(target))
    return written


def read_file(project_dir: str | Path, rel: str) -> str | None:
    target = _resolve(Path(project_dir), rel)
    if not target.exists() or not target.is_file():
        return None
    return target.read_text(encoding="utf-8", errors="replace")


def list_files(project_dir: str | Path, exts: tuple[str, ...] = (".gd", ".tscn", ".tres", ".godot")) -> list[str]:
    project_dir = Path(project_dir)
    out: list[str] = []
    for path in sorted(project_dir.rglob("*")):
        if ".godot" in path.parts or not path.is_file():
            continue
        if exts and path.suffix not in exts:
            continue
        out.append("res://" + path.relative_to(project_dir).as_posix())
    return out
