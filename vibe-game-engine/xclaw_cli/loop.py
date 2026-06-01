"""The core engine loop: generate -> apply -> headless-check -> feed errors back -> retry.

The generator is pluggable so the same loop drives a deterministic test fixer (Phase 2)
and the real LLM tool loop (Phase 3).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from xclaw_cli.edits import FileWrite, apply_writes
from xclaw_cli.headless import CheckResult, GodotHeadless


@dataclass
class LoopContext:
    prompt: str
    project_dir: Path
    attempt: int
    last_errors: list[str] = field(default_factory=list)


# A generator inspects the context (prompt + workspace + last_errors) and returns the
# file writes to apply this attempt.
Generator = Callable[[LoopContext], list[FileWrite]]


@dataclass
class AttemptRecord:
    attempt: int
    files_written: list[str]
    check: CheckResult


@dataclass
class LoopResult:
    ok: bool
    attempts: int
    history: list[AttemptRecord] = field(default_factory=list)

    @property
    def final_check(self) -> CheckResult | None:
        return self.history[-1].check if self.history else None


def run_loop(
    project_dir: str | Path,
    prompt: str,
    generator: Generator,
    godot: GodotHeadless,
    max_attempts: int = 3,
    import_first: bool = True,
    on_event: Callable[[str], None] | None = None,
) -> LoopResult:
    project_dir = Path(project_dir)

    def emit(msg: str) -> None:
        if on_event:
            on_event(msg)

    if import_first:
        emit("import: starting")
        imp = godot.import_project(project_dir)
        emit(f"import: {imp.summary()}")

    last_errors: list[str] = []
    history: list[AttemptRecord] = []

    for attempt in range(1, max_attempts + 1):
        ctx = LoopContext(prompt=prompt, project_dir=project_dir, attempt=attempt, last_errors=last_errors)
        emit(f"attempt {attempt}/{max_attempts}: generating")
        writes = generator(ctx)
        written = apply_writes(project_dir, writes)
        emit(f"attempt {attempt}: wrote {len(written)} file(s)")

        check = godot.check(project_dir)
        history.append(AttemptRecord(attempt=attempt, files_written=written, check=check))
        emit(f"attempt {attempt}: {check.summary()}")

        if check.ok:
            return LoopResult(ok=True, attempts=attempt, history=history)
        last_errors = check.errors

    return LoopResult(ok=False, attempts=max_attempts, history=history)
