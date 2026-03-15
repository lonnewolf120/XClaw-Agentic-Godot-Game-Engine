from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from contracts.run_state import RunState, RunStatus


POLICY_VERSION = "needs_human_v1"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_needs_human_ticket(state: RunState) -> dict[str, object]:
    if state.status != RunStatus.NEEDS_HUMAN:
        raise ValueError("state must be needs_human to build escalation ticket")

    return {
        "policy_version": POLICY_VERSION,
        "created_at_utc": _utc_now(),
        "run_id": state.run_id,
        "status": state.status,
        "retry_count": state.retry_count,
        "max_retries": state.max_retries,
        "failure_reason": state.failure_reason or "unspecified",
        "workspace_dir": state.workspace_dir,
        "latest_validation_summary": (
            state.validation_report.summary if state.validation_report is not None else "missing_validation_report"
        ),
        "retry_events": [
            {
                "attempt": event.attempt,
                "node": event.node,
                "reason": event.reason,
                "timestamp_utc": event.timestamp_utc,
            }
            for event in state.retry_events
        ],
    }


def write_needs_human_ticket(state: RunState, workspace_root: str | Path) -> Path:
    workspace_root_path = Path(workspace_root)
    ticket = build_needs_human_ticket(state)

    run_workspace = workspace_root_path / state.workspace_dir
    escalation_dir = run_workspace / ".vibe" / "escalation"
    escalation_dir.mkdir(parents=True, exist_ok=True)
    ticket_path = escalation_dir / "needs_human_ticket.json"
    ticket_path.write_text(json.dumps(ticket, indent=2), encoding="utf-8")

    queue_path = workspace_root_path / "runs" / "needs_human_queue.jsonl"
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    with queue_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(ticket) + "\n")

    return ticket_path
