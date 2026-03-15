"""Debugger agent stub for Milestone 3.

Responsible for applying patches and attempting repairs when validation fails.
"""

from __future__ import annotations

from pathlib import Path

from contracts.godot_patch import GodotFilePatch, PatchBatch, PatchOp


def debug_patch(patch_batch: PatchBatch) -> PatchBatch:
    """Analyze and potentially expand a patch batch based on validation failures."""
    patches = list(patch_batch.patches)
    if patches:
        return patch_batch

    fallback = GodotFilePatch(
        patch_id=f"debug-fallback-{patch_batch.attempt}",
        op=PatchOp.UPDATE,
        file_path="res://scripts/main.gd",
        language="gdscript",
        reason="Inject fallback entrypoint to recover run",
        full_content="extends Node2D\n\nfunc _ready() -> void:\n    pass\n",
        hunks=[],
        creates_backup=True,
    )
    return PatchBatch(run_id=patch_batch.run_id, attempt=patch_batch.attempt, patches=[fallback])


def apply_patch_batch(project_root: str, patch_batch: PatchBatch) -> list[str]:
    written_paths: list[str] = []
    root = Path(project_root)

    for patch in patch_batch.patches:
        relative_path = patch.file_path.replace("res://", "")
        target_path = root / relative_path

        if patch.op == PatchOp.DELETE:
            if target_path.exists():
                target_path.unlink()
            written_paths.append(str(target_path))
            continue

        target_path.parent.mkdir(parents=True, exist_ok=True)
        content = patch.full_content or ""
        target_path.write_text(content, encoding="utf-8")
        written_paths.append(str(target_path))

    return written_paths
