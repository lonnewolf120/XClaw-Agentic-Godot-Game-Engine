from __future__ import annotations

from pathlib import Path

from agents.coding_agent import generate_patches
from agents.coordinator import coordinate
from agents.debugger_agent import debug_patch
from agents.project_manager import build_project_spec, build_task_graph
from contracts.godot_patch import PatchBatch
from contracts.project_spec import ProjectSpec
from contracts.run_state import RunState
from contracts.task_graph import TaskGraph
from contracts.validation import ValidationReport


PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def _load_prompt_template(template_name: str) -> str:
    template_path = PROMPTS_DIR / f"{template_name}.prompt.md"
    if not template_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {template_path}")
    return template_path.read_text(encoding="utf-8")


class AgentRuntime:
    def invoke_project_manager(self, prompt: str) -> tuple[ProjectSpec, TaskGraph, str]:
        template = _load_prompt_template("project_manager")
        spec = build_project_spec(prompt)
        graph = build_task_graph(spec)
        return spec, graph, template

    def invoke_coordinator(
        self,
        run_state: RunState,
        task_graph: TaskGraph,
        validation_report: ValidationReport | None = None,
    ) -> tuple[RunState, str]:
        template = _load_prompt_template("coordinator")
        next_state = coordinate(run_state, task_graph, validation_report=validation_report)
        return next_state, template

    def invoke_coding_agent(self, task_graph: TaskGraph) -> tuple[PatchBatch, str]:
        template = _load_prompt_template("coding_agent")
        patch_batch = generate_patches(task_graph)
        return patch_batch, template

    def invoke_debugger_agent(self, patch_batch: PatchBatch) -> tuple[PatchBatch, str]:
        template = _load_prompt_template("debugger_agent")
        fixed_batch = debug_patch(patch_batch)
        return fixed_batch, template
