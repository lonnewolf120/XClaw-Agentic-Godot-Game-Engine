"""Run a deterministic benchmark to verify the validation + retry loop works across multiple prompts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contracts.run_state import OrchestrationNode, RunMode, RunState, RunStatus
from contracts.validation import (
    ValidationIssue,
    ValidationReport,
    ValidationSeverity,
    ValidationStage,
)
from orchestration.state_machine import StateMachine
from tools.escalation import write_needs_human_ticket


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[0]
DEFAULT_CORPUS_PATH = PROJECT_ROOT / "benchmarks" / "prompt_corpus_v1.txt"
BENCHMARK_RESULTS_DIR = PROJECT_ROOT / "benchmarks" / "results"


@dataclass
class PromptResult:
    prompt: str
    success: bool
    attempts: int
    final_status: str
    escalation_ticket_path: str = ""


def make_validation_report(run_id: str, attempt: int, succeed: bool) -> ValidationReport:
    if succeed:
        return ValidationReport(
            run_id=run_id,
            attempt=attempt,
            success=True,
            timed_out=False,
            stage_logs=[],
            issues=[],
            fatal_count=0,
            error_count=0,
            warning_count=0,
            summary="ok",
        )

    issue = ValidationIssue(
        stage=ValidationStage.CHECK,
        severity=ValidationSeverity.FATAL,
        message="Parse Error at res://scripts/player.gd",
        matched_pattern="parse_error",
    )

    return ValidationReport(
        run_id=run_id,
        attempt=attempt,
        success=False,
        timed_out=False,
        stage_logs=[f"run_{run_id}_attempt_{attempt}.log"],
        issues=[issue],
        fatal_count=1,
        error_count=0,
        warning_count=0,
        summary="parse error",
    )


def run_prompt(prompt: str, seed: int, workspace_root: str | Path = PROJECT_ROOT) -> PromptResult:
    """Run the orchestration loop for a single prompt and return result."""
    state_machine = StateMachine()
    state = RunState(
        run_id=f"run-{seed}",
        prompt=prompt,
        mode=RunMode.STANDALONE,
        workspace_dir=f"runs/run-{seed}",
        current_node=OrchestrationNode.INTAKE,
        status=RunStatus.INTAKE,
        max_retries=3,
    )

    if seed % 10 in (6, 7, 8):
        success_on_attempt = 3
    elif seed % 10 in (9, 0):
        success_on_attempt = 999
    else:
        success_on_attempt = 1

    attempts = 0
    while True:
        if state.status in {RunStatus.COMPLETED, RunStatus.NEEDS_HUMAN, RunStatus.FAILED}:
            break

        if state.current_node == OrchestrationNode.VALIDATION:
            attempts += 1
            succeed = attempts >= success_on_attempt
            report = make_validation_report(state.run_id, attempts, succeed)
            state = state_machine.step(state, validation_report=report)
        else:
            state = state_machine.step(state)

    escalation_ticket_path = ""
    if state.status == RunStatus.NEEDS_HUMAN:
        ticket_path = write_needs_human_ticket(state, workspace_root=workspace_root)
        escalation_ticket_path = str(ticket_path)

    return PromptResult(
        prompt=prompt,
        success=state.status == RunStatus.COMPLETED,
        attempts=attempts,
        final_status=state.status,
        escalation_ticket_path=escalation_ticket_path,
    )


def run_benchmark(prompts: List[str], workspace_root: str | Path = PROJECT_ROOT) -> List[PromptResult]:
    return [run_prompt(p, idx + 1, workspace_root=workspace_root) for idx, p in enumerate(prompts)]


def load_prompt_corpus(corpus_path: str | Path = DEFAULT_CORPUS_PATH) -> List[str]:
    path = Path(corpus_path)
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    prompts = [line for line in lines if line and not line.startswith("#")]
    if not prompts:
        raise ValueError("benchmark prompt corpus is empty")
    return prompts


def _write_benchmark_results(results: List[PromptResult]) -> None:
    BENCHMARK_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    successes = sum(1 for item in results if item.success)
    total = len(results)
    success_rate = round(successes / total, 4) if total else 0.0
    needs_human_count = sum(1 for item in results if item.final_status == RunStatus.NEEDS_HUMAN)
    avg_attempts = round(sum(item.attempts for item in results) / total, 3) if total else 0.0

    summary = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "total_prompts": total,
        "successes": successes,
        "success_rate": success_rate,
        "needs_human_count": needs_human_count,
        "avg_attempts": avg_attempts,
    }

    latest_payload = {
        "summary": summary,
        "results": [
            {
                "prompt": item.prompt,
                "success": item.success,
                "attempts": item.attempts,
                "final_status": item.final_status,
                "escalation_ticket_path": item.escalation_ticket_path,
            }
            for item in results
        ],
    }

    (BENCHMARK_RESULTS_DIR / "latest.json").write_text(
        json.dumps(latest_payload, indent=2),
        encoding="utf-8",
    )

    with (BENCHMARK_RESULTS_DIR / "history.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(summary) + "\n")


def main() -> int:
    prompts = load_prompt_corpus()
    results = run_benchmark(prompts, workspace_root=PROJECT_ROOT)
    _write_benchmark_results(results)

    successes = [r for r in results if r.success]
    print(f"{len(successes)}/{len(results)} prompts completed successfully")

    for r in results:
        print(f"- {r.prompt[:40]:40} | status={r.final_status} | attempts={r.attempts}")
    escalations = [item for item in results if item.escalation_ticket_path]
    print(f"needs_human_escalations={len(escalations)}")

    return 0 if len(successes) >= 8 else 1


if __name__ == "__main__":
    raise SystemExit(main())
