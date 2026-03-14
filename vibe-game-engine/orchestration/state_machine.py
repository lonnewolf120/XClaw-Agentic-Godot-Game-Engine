from __future__ import annotations

from typing import Dict

from contracts.run_state import OrchestrationNode, RunState, RunStatus
from contracts.validation import ValidationReport
from orchestration.nodes.debug import run_debug
from orchestration.nodes.intake import run_intake
from orchestration.nodes.planning import run_planning
from orchestration.nodes.validation import run_validation


TERMINAL_STATUSES = {RunStatus.COMPLETED, RunStatus.NEEDS_HUMAN, RunStatus.FAILED}

NODE_STATUS_MAP: Dict[OrchestrationNode, RunStatus] = {
    OrchestrationNode.INTAKE: RunStatus.INTAKE,
    OrchestrationNode.PLANNING: RunStatus.PLANNING,
    OrchestrationNode.VALIDATION: RunStatus.VALIDATING,
    OrchestrationNode.DEBUG: RunStatus.DEBUGGING,
    OrchestrationNode.DONE: RunStatus.COMPLETED,
}


class StateMachine:
    def step(
        self,
        state: RunState,
        validation_report: ValidationReport | None = None,
    ) -> RunState:
        if state.status in TERMINAL_STATUSES:
            return state

        if state.current_node == OrchestrationNode.INTAKE:
            return run_intake(state)

        if state.current_node == OrchestrationNode.PLANNING:
            return run_planning(state)

        if state.current_node == OrchestrationNode.VALIDATION:
            if validation_report is None:
                raise ValueError("validation_report is required for validation node")
            return run_validation(state, validation_report)

        if state.current_node == OrchestrationNode.DEBUG:
            return run_debug(state)

        if state.current_node == OrchestrationNode.DONE:
            return state.model_copy(update={"status": RunStatus.COMPLETED})

        raise ValueError(f"Unsupported node: {state.current_node}")
