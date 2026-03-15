"""Coding agent stub for Milestone 3.

Responsible for generating and validating Godot project patches given a TaskGraph.
"""

from __future__ import annotations

from contracts.godot_patch import GodotFilePatch, PatchBatch, PatchOp
from contracts.task_graph import TaskGraph


def generate_patches(task_graph: TaskGraph) -> PatchBatch:
    """Generate a batch of patches for a given task graph."""
    patches = [
        GodotFilePatch(
            patch_id="patch-main-script",
            op=PatchOp.UPDATE,
            file_path="res://scripts/main.gd",
            language="gdscript",
            reason="Ensure minimal runnable entry point",
            full_content=(
                "extends Node2D\n\n"
                "func _ready() -> void:\n"
                "    print(\"vibe run started\")\n"
            ),
            hunks=[],
            creates_backup=True,
        )
    ]

    return PatchBatch(run_id=task_graph.run_id, attempt=1, patches=patches)
