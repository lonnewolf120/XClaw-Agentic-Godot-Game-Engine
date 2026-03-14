from __future__ import annotations

from contracts.run_state import OrchestrationNode, RunState, RunStatus


def run_intake(state: RunState) -> RunState:
    return state.model_copy(
        update={
            "status": RunStatus.PLANNING,
            "current_node": OrchestrationNode.PLANNING,
            "failure_reason": None,
        }
    )
