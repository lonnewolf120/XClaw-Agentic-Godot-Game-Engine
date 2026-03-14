from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

from contracts.validation import (
    ValidationIssue,
    ValidationReport,
    ValidationSeverity,
    ValidationStage,
)


FATAL_PATTERNS: Sequence[Tuple[re.Pattern[str], str]] = (
    (re.compile(r"\\bSCRIPT ERROR\\b", re.IGNORECASE), "script_error"),
    (re.compile(r"\\bParse Error\\b", re.IGNORECASE), "parse_error"),
    (re.compile(r"\\bCRASH\\b", re.IGNORECASE), "crash"),
    (re.compile(r"Cannot open file", re.IGNORECASE), "missing_file"),
    (re.compile(r"Invalid get index", re.IGNORECASE), "invalid_get_index"),
)

ERROR_PATTERNS: Sequence[Tuple[re.Pattern[str], str]] = (
    (re.compile(r"\\bERROR:\\b", re.IGNORECASE), "generic_error"),
)

WARNING_PATTERNS: Sequence[Tuple[re.Pattern[str], str]] = (
    (re.compile(r"\\bWARNING:\\b", re.IGNORECASE), "generic_warning"),
)


def infer_stage(log_path: Path) -> ValidationStage:
    name = log_path.name.lower()
    if "import" in name:
        return ValidationStage.IMPORT
    if "check" in name:
        return ValidationStage.CHECK
    return ValidationStage.SMOKE


def parse_issues(log_path: Path) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    stage = infer_stage(log_path)
    if not log_path.exists():
        issues.append(
            ValidationIssue(
                stage=stage,
                severity=ValidationSeverity.FATAL,
                message=f"Missing validation log: {log_path}",
                matched_pattern="missing_log",
            )
        )
        return issues

    for raw_line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line:
            continue

        matched = False
        for pattern, token in FATAL_PATTERNS:
            if pattern.search(line):
                issues.append(
                    ValidationIssue(
                        stage=stage,
                        severity=ValidationSeverity.FATAL,
                        message=line,
                        file_path=str(log_path),
                        matched_pattern=token,
                    )
                )
                matched = True
                break

        if matched:
            continue

        for pattern, token in ERROR_PATTERNS:
            if pattern.search(line):
                issues.append(
                    ValidationIssue(
                        stage=stage,
                        severity=ValidationSeverity.ERROR,
                        message=line,
                        file_path=str(log_path),
                        matched_pattern=token,
                    )
                )
                matched = True
                break

        if matched:
            continue

        for pattern, token in WARNING_PATTERNS:
            if pattern.search(line):
                issues.append(
                    ValidationIssue(
                        stage=stage,
                        severity=ValidationSeverity.WARNING,
                        message=line,
                        file_path=str(log_path),
                        matched_pattern=token,
                    )
                )
                break

    return issues


def build_report(run_id: str, attempt: int, log_paths: Iterable[Path]) -> ValidationReport:
    stage_logs = [str(path) for path in log_paths]
    all_issues: List[ValidationIssue] = []
    for path in log_paths:
        all_issues.extend(parse_issues(path))

    severity_counts: Dict[ValidationSeverity, int] = {
        ValidationSeverity.FATAL: 0,
        ValidationSeverity.ERROR: 0,
        ValidationSeverity.WARNING: 0,
    }
    for issue in all_issues:
        if issue.severity in severity_counts:
            severity_counts[issue.severity] += 1

    success = (
        severity_counts[ValidationSeverity.FATAL] == 0
        and severity_counts[ValidationSeverity.ERROR] == 0
    )

    summary = "validation_passed"
    if not success:
        summary = (
            f"validation_failed: fatal={severity_counts[ValidationSeverity.FATAL]}, "
            f"error={severity_counts[ValidationSeverity.ERROR]}"
        )

    return ValidationReport(
        run_id=run_id,
        attempt=attempt,
        success=success,
        timed_out=False,
        stage_logs=stage_logs,
        issues=all_issues,
        fatal_count=severity_counts[ValidationSeverity.FATAL],
        error_count=severity_counts[ValidationSeverity.ERROR],
        warning_count=severity_counts[ValidationSeverity.WARNING],
        summary=summary,
    )


def write_report(report: ValidationReport, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")


def exit_code_from_report(report_path: Path) -> int:
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    report = ValidationReport.model_validate(payload)
    return 0 if report.success else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Parse Godot validation logs")
    parser.add_argument("--run-id")
    parser.add_argument("--attempt", type=int)
    parser.add_argument("--logs", nargs="+")
    parser.add_argument("--output")
    parser.add_argument("--exit-code-from-report")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.exit_code_from_report:
        return exit_code_from_report(Path(args.exit_code_from_report))

    if not args.run_id or args.attempt is None or not args.logs or not args.output:
        raise ValueError("--run-id, --attempt, --logs, and --output are required")

    log_paths = [Path(item) for item in args.logs]
    report = build_report(run_id=args.run_id, attempt=args.attempt, log_paths=log_paths)
    write_report(report=report, output_path=Path(args.output))
    return 0 if report.success else 1


if __name__ == "__main__":
    sys.exit(main())
