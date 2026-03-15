from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.triage_escalations import triage_queue


def test_triage_queue_writes_summary(tmp_path) -> None:
    queue = tmp_path / "needs_human_queue.jsonl"
    triage = tmp_path / "escalation_triage.jsonl"

    queue.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "run_id": "run-1",
                        "failure_reason": "validation_retry_exhausted",
                        "latest_validation_summary": "parse error",
                    }
                ),
                json.dumps(
                    {
                        "run_id": "run-2",
                        "failure_reason": "validation_retry_exhausted",
                        "latest_validation_summary": "resource missing_file",
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    summary = triage_queue(queue_path=queue, triage_log_path=triage)
    assert summary["triaged_items"] == 2
    assert "agent_logic_issue" in summary["class_counts"]
    assert "template_issue" in summary["class_counts"]

    lines = triage.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["triaged_items"] == 2

    # Queue should be cleared
    assert queue.read_text(encoding="utf-8") == ""
