from __future__ import annotations

from contracts.run_state import OrchestrationNode, RunState, RunStatus


def run_planning(state: RunState) -> RunState:
    return state.model_copy(
        update={
            "status": RunStatus.VALIDATING,
            "current_node": OrchestrationNode.VALIDATION,
            "failure_reason": None,
        }
    )
