from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.coding_agent import generate_patches
from agents.coordinator import coordinate
from agents.debugger_agent import apply_patch_batch, debug_patch
from agents.project_manager import build_project_spec, build_task_graph
from contracts.godot_patch import PatchBatch
from contracts.run_state import OrchestrationNode, RunMode, RunState, RunStatus
from contracts.validation import ValidationIssue, ValidationReport, ValidationSeverity, ValidationStage


def _base_state(run_id: str, prompt: str) -> RunState:
    return RunState(
        run_id=run_id,
        prompt=prompt,
        mode=RunMode.STANDALONE,
        workspace_dir=f"runs/{run_id}",
        current_node=OrchestrationNode.INTAKE,
        status=RunStatus.INTAKE,
        max_retries=3,
    )


def test_project_manager_builds_valid_spec_and_graph() -> None:
    spec = build_project_spec("Create a 2D platformer with jump mechanics")
    graph = build_task_graph(spec)
    assert spec.selected_template == "templates/base_2d_platformer"
    assert len(graph.tasks) >= 1


def test_coding_agent_generates_patch_batch() -> None:
    spec = build_project_spec("Create a tiny game")
    graph = build_task_graph(spec)
    patch_batch = generate_patches(graph)
    assert patch_batch.run_id == spec.run_id
    assert len(patch_batch.patches) >= 1


def test_debugger_applies_fallback_patch(tmp_path: Path) -> None:
    empty_batch = PatchBatch(run_id="run-1", attempt=1, patches=[])
    recovered = debug_patch(empty_batch)
    written = apply_patch_batch(str(tmp_path), recovered)
    assert len(written) == 1
    assert (tmp_path / "scripts" / "main.gd").exists()


def test_coordinator_moves_to_completed_after_retry() -> None:
    prompt = "A tiny game"
    spec = build_project_spec(prompt)
    graph = build_task_graph(spec)
    state = _base_state(spec.run_id, prompt)

    state = coordinate(state, graph)
    state = coordinate(state, graph)

    failure = ValidationReport(
        run_id=spec.run_id,
        attempt=1,
        success=False,
        timed_out=False,
        stage_logs=[],
        issues=[
            ValidationIssue(
                stage=ValidationStage.CHECK,
                severity=ValidationSeverity.FATAL,
                message="Parse Error at res://scripts/player.gd",
                matched_pattern="parse_error",
            )
        ],
        fatal_count=1,
        error_count=0,
        warning_count=0,
        summary="parse error",
    )
    state = coordinate(state, graph, validation_report=failure)
    assert state.status == RunStatus.DEBUGGING

    state = coordinate(state, graph)

    success = ValidationReport(
        run_id=spec.run_id,
        attempt=2,
        success=True,
        timed_out=False,
        stage_logs=[],
        issues=[],
        fatal_count=0,
        error_count=0,
        warning_count=0,
        summary="ok",
    )
    state = coordinate(state, graph, validation_report=success)
    assert state.status == RunStatus.COMPLETED
