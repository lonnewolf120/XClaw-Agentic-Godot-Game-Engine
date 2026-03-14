from __future__ import annotations

from contracts.run_state import OrchestrationNode, RunState, RunStatus


def run_debug(state: RunState) -> RunState:
    return state.model_copy(
        update={
            "status": RunStatus.VALIDATING,
            "current_node": OrchestrationNode.VALIDATION,
        }
    )
