from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = PROJECT_ROOT / "runs" / "needs_human_queue.jsonl"
TRIAGE_LOG_PATH = PROJECT_ROOT / "runs" / "escalation_triage.jsonl"


def _classify(item: dict) -> str:
    reason = (item.get("failure_reason") or "").lower()
    summary = (item.get("latest_validation_summary") or "").lower()
    if "parse" in summary:
        return "agent_logic_issue"
    if "timeout" in summary:
        return "runtime_issue"
    if "resource" in summary or "missing_file" in summary:
        return "template_issue"
    if "invalid prompt" in reason:
        return "prompt_issue"
    return "runtime_issue"


def triage_queue(
    queue_path: Path = QUEUE_PATH,
    triage_log_path: Path = TRIAGE_LOG_PATH,
) -> dict:
    if not queue_path.exists():
        summary = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "triaged_items": 0,
            "class_counts": {},
            "notes": "queue_missing",
        }
        triage_log_path.parent.mkdir(parents=True, exist_ok=True)
        with triage_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(summary) + "\n")
        return summary

    lines = [line for line in queue_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    records = [json.loads(line) for line in lines]
    unique_by_run: dict[str, dict] = {}
    for record in records:
        unique_by_run[str(record.get("run_id", "unknown"))] = record

    classifications = Counter(_classify(item) for item in unique_by_run.values())
    summary = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "triaged_items": len(unique_by_run),
        "class_counts": dict(classifications),
        "run_ids": sorted(unique_by_run.keys()),
    }

    triage_log_path.parent.mkdir(parents=True, exist_ok=True)
    with triage_log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(summary) + "\n")

    return summary


def main() -> int:
    summary = triage_queue()
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())