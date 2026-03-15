from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contracts.run_state import OrchestrationNode, RunMode, RunState, RunStatus
from contracts.validation import ValidationIssue, ValidationReport, ValidationSeverity, ValidationStage
from orchestration.state_machine import StateMachine


def _base_state() -> RunState:
    return RunState(
        run_id="run-001",
        prompt="Create a tiny platformer",
        mode=RunMode.STANDALONE,
        workspace_dir="runs/run-001",
        current_node=OrchestrationNode.INTAKE,
        status=RunStatus.INTAKE,
        max_retries=3,
    )


def _report(attempt: int, success: bool, summary: str) -> ValidationReport:
    return ValidationReport(
        run_id="run-001",
        attempt=attempt,
        success=success,
        timed_out=False,
        stage_logs=[],
        issues=[],
        fatal_count=0 if success else 1,
        error_count=0,
        warning_count=0,
        summary=summary,
    )


def test_validation_loop_success_path() -> None:
    machine = StateMachine()
    state = _base_state()

    state = machine.step(state)
    assert state.current_node == OrchestrationNode.PLANNING
    assert state.status == RunStatus.PLANNING

    state = machine.step(state)
    assert state.current_node == OrchestrationNode.VALIDATION
    assert state.status == RunStatus.VALIDATING

    state = machine.step(state, validation_report=_report(attempt=1, success=True, summary="ok"))
    assert state.status == RunStatus.COMPLETED
    assert state.current_node == OrchestrationNode.DONE
    assert state.retry_count == 0


def test_validation_loop_moves_to_needs_human_after_three_failures() -> None:
    machine = StateMachine()
    state = _base_state()

    state = machine.step(state)
    state = machine.step(state)

    state = machine.step(state, validation_report=_report(attempt=1, success=False, summary="parse error"))
    assert state.status == RunStatus.DEBUGGING
    assert state.retry_count == 1
    state = machine.step(state)

    state = machine.step(state, validation_report=_report(attempt=2, success=False, summary="runtime error"))
    assert state.status == RunStatus.DEBUGGING
    assert state.retry_count == 2
    state = machine.step(state)

    state = machine.step(state, validation_report=_report(attempt=3, success=False, summary="resource missing"))
    assert state.status == RunStatus.NEEDS_HUMAN
    assert state.current_node == OrchestrationNode.DONE
    assert state.retry_count == 3
    assert state.failure_reason == "validation_retry_exhausted"


def test_debug_node_synthesizes_patch_batch_from_failure() -> None:
    machine = StateMachine()
    state = _base_state()

    state = machine.step(state)
    state = machine.step(state)

    failure_report = ValidationReport(
        run_id="run-001",
        attempt=1,
        success=False,
        timed_out=False,
        stage_logs=["runs/run-001/validation/import.log"],
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

    state = machine.step(state, validation_report=failure_report)
    assert state.status == RunStatus.DEBUGGING

    state = machine.step(state)
    assert state.current_node == OrchestrationNode.VALIDATION
    assert state.proposed_patch_batch is not None
    assert len(state.proposed_patch_batch.patches) >= 1
    assert state.proposed_patch_batch.patches[0].file_path == "res://scripts/player.gd"
