from __future__ import annotations

import re

from contracts.godot_patch import GodotFilePatch, PatchBatch, PatchOp
from contracts.run_state import OrchestrationNode, RunState, RunStatus
from contracts.validation import ValidationIssue, ValidationReport
from orchestration._compat import model_copy_compat


_RESOURCE_PATH_PATTERN = re.compile(r"res://[^\s:]+")


def _candidate_file_path(issue: ValidationIssue) -> str:
    match = _RESOURCE_PATH_PATTERN.search(issue.message)
    if match:
        return match.group(0)
    return "res://scripts/main.gd"


def _replacement_for_issue(issue: ValidationIssue) -> str:
    token = issue.matched_pattern or "unknown"
    if token == "parse_error":
        return "extends Node\n\nfunc _ready() -> void:\n    pass\n"
    if token == "missing_file":
        return "extends Node\n\nfunc _ready() -> void:\n    push_warning(\"Fallback file created by debug node\")\n"
    if token == "invalid_get_index":
        return "extends Node\n\nfunc _ready() -> void:\n    if has_method(\"bootstrap\"):\n        bootstrap()\n"
    return "extends Node\n\nfunc _ready() -> void:\n    pass\n"


def synthesize_patch_batch(report: ValidationReport) -> PatchBatch:
    patches: list[GodotFilePatch] = []
    for idx, issue in enumerate(report.issues, start=1):
        if issue.severity.value not in {"fatal", "error"}:
            continue

        patches.append(
            GodotFilePatch(
                patch_id=f"debug-{report.attempt}-{idx}",
                op=PatchOp.UPDATE,
                file_path=_candidate_file_path(issue),
                language="gdscript",
                reason=f"Auto patch for {issue.matched_pattern or issue.severity.value}",
                full_content=_replacement_for_issue(issue),
                hunks=[],
                creates_backup=True,
            )
        )

    if not patches:
        patches.append(
            GodotFilePatch(
                patch_id=f"debug-{report.attempt}-fallback",
                op=PatchOp.UPDATE,
                file_path="res://scripts/main.gd",
                language="gdscript",
                reason="Auto patch fallback for unresolved validation issue",
                full_content="extends Node\n\nfunc _ready() -> void:\n    pass\n",
                hunks=[],
                creates_backup=True,
            )
        )

    return PatchBatch(run_id=report.run_id, attempt=report.attempt, patches=patches)


def run_debug(state: RunState, validation_report: ValidationReport | None = None) -> RunState:
    patch_batch = None
    if validation_report is not None and not validation_report.success:
        patch_batch = synthesize_patch_batch(validation_report)

    return model_copy_compat(
        state,
        update={
            "status": RunStatus.VALIDATING,
            "current_node": OrchestrationNode.VALIDATION,
            "proposed_patch_batch": patch_batch,
        },
    )
