from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.runtime import AgentRuntime
from contracts.run_state import OrchestrationNode, RunMode, RunState, RunStatus
from contracts.validation import ValidationIssue, ValidationReport, ValidationSeverity, ValidationStage
from tools.escalation import write_needs_human_ticket


def run_smoke(prompt: str) -> RunState:
    runtime = AgentRuntime()
    spec, graph, _ = runtime.invoke_project_manager(prompt)

    state = RunState(
        run_id=spec.run_id,
        prompt=prompt,
        mode=RunMode.STANDALONE,
        workspace_dir=f"runs/{spec.run_id}",
        current_node=OrchestrationNode.INTAKE,
        status=RunStatus.INTAKE,
        max_retries=3,
    )

    state, _ = runtime.invoke_coordinator(state, graph)
    state, _ = runtime.invoke_coordinator(state, graph)

    first_report = ValidationReport(
        run_id=spec.run_id,
        attempt=1,
        success=False,
        timed_out=False,
        stage_logs=["smoke-attempt-1.log"],
        issues=[
            ValidationIssue(
                stage=ValidationStage.CHECK,
                severity=ValidationSeverity.FATAL,
                message="Parse Error at res://scripts/player.gd",
                matched_pattern="parse_error",
            )
        ],
        fatal_count=1,
        error_count=0,
        warning_count=0,
        summary="parse error",
    )

    state, _ = runtime.invoke_coordinator(state, graph, validation_report=first_report)
    state, _ = runtime.invoke_coordinator(state, graph)

    patch_batch, _ = runtime.invoke_coding_agent(graph)
    _, _ = runtime.invoke_debugger_agent(patch_batch)

    second_report = ValidationReport(
        run_id=spec.run_id,
        attempt=2,
        success=True,
        timed_out=False,
        stage_logs=["smoke-attempt-2.log"],
        issues=[],
        fatal_count=0,
        error_count=0,
        warning_count=0,
        summary="ok",
    )

    state, _ = runtime.invoke_coordinator(state, graph, validation_report=second_report)
    return state


def main() -> int:
    state = run_smoke("Create a tiny platformer with one playable character")
    if state.status == RunStatus.NEEDS_HUMAN:
        ticket_path = write_needs_human_ticket(state, workspace_root=Path(__file__).resolve().parents[1])
        print(f"smoke_escalation_ticket={ticket_path}")
    print(f"smoke_final_status={state.status}")
    print(f"smoke_retry_count={state.retry_count}")
    return 0 if state.status == RunStatus.COMPLETED else 1


if __name__ == "__main__":
    raise SystemExit(main())
