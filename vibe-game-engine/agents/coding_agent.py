"""Coding agent stub for Milestone 3.

Responsible for generating and validating Godot project patches given a TaskGraph.
"""

from __future__ import annotations
import os
import json

from contracts.godot_patch import GodotFilePatch, PatchBatch, PatchOp
from contracts.task_graph import TaskGraph
from agents.llm_manager import get_llm_manager

def generate_patches(task_graph: TaskGraph) -> PatchBatch:
    """Generate a batch of patches for a given task graph."""
    if os.environ.get("USE_REAL_LLM") == "1":
        manager = get_llm_manager()
        prompt = f"Given this game task graph:\n{task_graph}\nGenerate valid Godot gdscript entries. Respond carefully."
        
        # Here we'd actually use the LLM to generate the patches dynamically.
        # But for safety, fallback to the structured output definition.
        # Using a dummy call for context outline:
        # result = manager.invoke_with_json_schema(prompt, PatchBatch)
    
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
