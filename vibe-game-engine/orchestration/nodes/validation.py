from __future__ import annotations

from datetime import datetime, timezone

from contracts.run_state import OrchestrationNode, RetryEvent, RunState, RunStatus
from contracts.validation import ValidationReport
from orchestration._compat import model_copy_compat


def run_validation(state: RunState, report: ValidationReport) -> RunState:
    update = {"validation_report": report}

    if report.success:
        update.update(
            {
                "status": RunStatus.COMPLETED,
                "current_node": OrchestrationNode.DONE,
                "failure_reason": None,
            }
        )
        return model_copy_compat(state, update=update)

    next_retry_count = state.retry_count + 1
    retry_event = RetryEvent(
        attempt=next_retry_count,
        node=OrchestrationNode.VALIDATION,
        reason=report.summary,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
    )
    retry_events = [*state.retry_events, retry_event]

    if next_retry_count >= state.max_retries:
        update.update(
            {
                "retry_count": next_retry_count,
                "retry_events": retry_events,
                "status": RunStatus.NEEDS_HUMAN,
                "current_node": OrchestrationNode.DONE,
                "failure_reason": "validation_retry_exhausted",
            }
        )
        return model_copy_compat(state, update=update)

    update.update(
        {
            "retry_count": next_retry_count,
            "retry_events": retry_events,
            "status": RunStatus.DEBUGGING,
            "current_node": OrchestrationNode.DEBUG,
            "failure_reason": report.summary,
        }
    )
    return model_copy_compat(state, update=update)
