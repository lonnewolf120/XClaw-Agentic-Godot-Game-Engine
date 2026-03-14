from __future__ import annotations

from contracts.run_state import OrchestrationNode, RunState, RunStatus
from orchestration._compat import model_copy_compat


def run_intake(state: RunState) -> RunState:
    return model_copy_compat(
        state,
        update={
            "status": RunStatus.PLANNING,
            "current_node": OrchestrationNode.PLANNING,
            "failure_reason": None,
        },
    )
