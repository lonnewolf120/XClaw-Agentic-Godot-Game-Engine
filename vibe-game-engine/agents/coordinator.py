"""Coordinator agent stub for Milestone 3.

Responsible for orchestrating between agents and ensuring schema compliance.
"""

from __future__ import annotations

from contracts.run_state import RunState
from contracts.task_graph import TaskGraph
from contracts.validation import ValidationReport
from orchestration.state_machine import StateMachine


def coordinate(
    run_state: RunState,
    task_graph: TaskGraph,
    validation_report: ValidationReport | None = None,
) -> RunState:
    """Advance the run state based on task graph progress."""
    if not task_graph.tasks:
        raise ValueError("task_graph must have at least one task")

    machine = StateMachine()
    return machine.step(run_state, validation_report=validation_report)
