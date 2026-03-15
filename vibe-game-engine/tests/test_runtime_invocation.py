from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.runtime import AgentRuntime
from contracts.godot_patch import PatchBatch
from contracts.run_state import OrchestrationNode, RunMode, RunState, RunStatus
from contracts.validation import ValidationReport


def _state(run_id: str, prompt: str) -> RunState:
    return RunState(
        run_id=run_id,
        prompt=prompt,
        mode=RunMode.STANDALONE,
        workspace_dir=f"runs/{run_id}",
        current_node=OrchestrationNode.INTAKE,
        status=RunStatus.INTAKE,
        max_retries=3,
    )


def test_runtime_loads_templates_and_builds_spec_graph() -> None:
    runtime = AgentRuntime()
    spec, graph, template = runtime.invoke_project_manager("Build a tiny platformer")
    assert "Project Manager Prompt Template" in template
    assert spec.run_id == graph.run_id


def test_runtime_invokes_coordinator_and_coding_paths() -> None:
    runtime = AgentRuntime()
    spec, graph, _ = runtime.invoke_project_manager("Build a tiny platformer")

    state = _state(spec.run_id, "Build a tiny platformer")
    state, template = runtime.invoke_coordinator(state, graph)
    assert "Coordinator Prompt Template" in template
    assert state.current_node == OrchestrationNode.PLANNING

    state, _ = runtime.invoke_coordinator(state, graph)
    assert state.current_node == OrchestrationNode.VALIDATION

    patch_batch, coding_template = runtime.invoke_coding_agent(graph)
    assert isinstance(patch_batch, PatchBatch)
    assert "Coding Agent Prompt Template" in coding_template


def test_runtime_invokes_debugger_template() -> None:
    runtime = AgentRuntime()
    empty_batch = PatchBatch(run_id="run-1", attempt=1, patches=[])
    fixed, template = runtime.invoke_debugger_agent(empty_batch)
    assert "Debugger Agent Prompt Template" in template
    assert len(fixed.patches) >= 1


def test_runtime_passes_validation_report_to_coordinator() -> None:
    runtime = AgentRuntime()
    spec, graph, _ = runtime.invoke_project_manager("Build a tiny platformer")
    state = _state(spec.run_id, "Build a tiny platformer")
    state, _ = runtime.invoke_coordinator(state, graph)
    state, _ = runtime.invoke_coordinator(state, graph)

    report = ValidationReport(
        run_id=spec.run_id,
        attempt=1,
        success=True,
        timed_out=False,
        stage_logs=[],
        issues=[],
        fatal_count=0,
        error_count=0,
        warning_count=0,
        summary="ok",
    )
    state, _ = runtime.invoke_coordinator(state, graph, validation_report=report)
    assert state.status == RunStatus.COMPLETED
