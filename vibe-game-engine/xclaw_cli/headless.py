"""Headless Godot gate.

Phase 0 findings drive this module:
- `Godot.exe --headless --path <ws> --import` imports assets (run once after copying a template).
- `Godot.exe --headless --path <ws> --editor --quit` loads the project + all scripts and prints
  parse/script errors to stdout/stderr.
- Exit code is UNRELIABLE (stays 0 on parse errors), so success is decided by scraping the log
  for known Godot error markers.
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

# Markers Godot prints when a script fails to parse/load or errors at load time.
ERROR_MARKERS: tuple[str, ...] = (
    "SCRIPT ERROR:",
    "Parse Error:",
    "USER ERROR:",
    "Failed to load script",
)

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


@dataclass
class CheckResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    raw_log: str = ""
    timed_out: bool = False

    def summary(self) -> str:
        if self.timed_out:
            return "headless_check_timed_out"
        if self.ok:
            return "headless_check_passed"
        return f"headless_check_failed: {len(self.errors)} error line(s)"


class GodotHeadless:
    def __init__(self, godot_exe: str, timeout: int = 180) -> None:
        self.godot_exe = godot_exe
        self.timeout = timeout

    def _run(self, extra_args: list[str], timeout: int | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(
            [self.godot_exe, "--headless", *extra_args],
            capture_output=True,
            text=True,
            timeout=timeout or self.timeout,
            check=False,
        )

    def import_project(self, project_dir: str | Path) -> CheckResult:
        """Import resources. Returns a CheckResult (scraped for errors)."""
        try:
            proc = self._run(["--path", str(project_dir), "--import"])
        except subprocess.TimeoutExpired:
            return CheckResult(ok=False, errors=["import_timeout"], timed_out=True)
        return self._scrape(proc)

    def check(self, project_dir: str | Path) -> CheckResult:
        """Load the project + scripts in editor mode and report parse/script errors."""
        try:
            proc = self._run(["--path", str(project_dir), "--editor", "--quit"])
        except subprocess.TimeoutExpired:
            return CheckResult(ok=False, errors=["check_timeout"], timed_out=True)
        return self._scrape(proc)

    def smoke(self, project_dir: str | Path, seconds: int = 8) -> CheckResult:
        """Bounded headless run of the main scene. A timeout-kill is treated as success
        (the game ran without crashing); only logged error markers fail it."""
        try:
            proc = self._run(["--path", str(project_dir)], timeout=seconds)
        except subprocess.TimeoutExpired as exc:
            log = _strip_ansi((exc.stdout or "") if isinstance(exc.stdout, str) else "")
            errors = self._errors_in(log)
            return CheckResult(ok=not errors, errors=errors, raw_log=log)
        return self._scrape(proc)

    @staticmethod
    def _errors_in(log: str) -> list[str]:
        return [
            line.strip()
            for line in log.splitlines()
            if any(marker in line for marker in ERROR_MARKERS)
        ]

    def _scrape(self, proc: subprocess.CompletedProcess) -> CheckResult:
        log = _strip_ansi((proc.stdout or "") + "\n" + (proc.stderr or ""))
        errors = self._errors_in(log)
        return CheckResult(ok=not errors, errors=errors, raw_log=log)
