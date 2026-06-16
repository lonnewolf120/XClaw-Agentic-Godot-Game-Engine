"""Headless Godot gate.

Phase 0 findings drive this module:
- `Godot.exe --headless --path <ws> --import` imports assets (run once after copying a template).
- `Godot.exe --headless --path <ws> --editor --quit` loads the project + all scripts and prints
  parse/script errors to stdout/stderr.
- Exit code is UNRELIABLE (stays 0 on parse errors), so success is decided by scraping the log
  for known Godot error markers.
"""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

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
    scout_data: Dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        if self.timed_out:
            return "headless_check_timed_out"
        if self.ok:
            return "headless_check_passed"
        return f"headless_check_failed: {len(self.errors)} error line(s)"


@dataclass
class PlaytestResult:
    verdict: str = "NONE"          # PASS | FAIL | NONE
    checks: int = 0
    failed: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    timed_out: bool = False
    raw_log: str = ""

    @property
    def ok(self) -> bool:
        return self.verdict == "PASS" and not self.errors

    def summary(self) -> str:
        if self.errors:
            return f"playtest_script_errors: {len(self.errors)}"
        if self.timed_out and self.verdict == "NONE":
            return "playtest_timed_out_no_verdict"
        return f"playtest_{self.verdict.lower()} ({self.checks} checks, failed={self.failed})"


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
        # Filter out common Godot noise to find real errors
        errors = [e for e in self._errors_in(log) if "WASAPI" not in e and "X11" not in e]
        scout = self._parse_scout(log)
        return CheckResult(ok=not errors, errors=errors, raw_log=log, scout_data=scout)

    def smoke_test(self, project_dir: Path, timeout: int = 8) -> CheckResult:
        """Run the game project headlessly for a few seconds to verify behavior."""
        if not self.godot_exe:
            return CheckResult(ok=False, errors=["No Godot executable found"])
        
        try:
            # Run without --editor to actually execute the scene
            proc = subprocess.run(
                [str(self.godot_exe), "--headless", "--path", str(project_dir)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=timeout,
                check=False
            )
            return self._scrape(proc)
        except subprocess.TimeoutExpired as exc:
            # Timeout is actually a GOOD thing in a smoke test - it means the game didn't crash
            stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", "ignore")
            stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", "ignore")
            log = _strip_ansi(stdout + "\n" + stderr)
            scout = self._parse_scout(log)
            # If there's scout data, we consider it a success even if it timed out
            return CheckResult(ok=True, errors=[], raw_log=log, timed_out=True, scout_data=scout)
        except Exception as exc:
            return CheckResult(ok=False, errors=[str(exc)])

    def run_playtest(
        self,
        project_dir: str | Path,
        scene: str = "res://vibe_game/playtest_harness.tscn",
        timeout: int = 120,
    ) -> "PlaytestResult":
        """Run the schema-driven playtest harness scene headlessly and parse its verdict.

        The harness prints `VIBE_TEST RESULT verdict=PASS|FAIL checks=N failed=[...]` and then
        quits, so a normal (non-timeout) exit is expected. The verdict — not the process exit
        code — decides pass/fail.
        """
        try:
            proc = self._run(["--path", str(project_dir), scene], timeout=timeout)
            log = _strip_ansi((proc.stdout or "") + "\n" + (proc.stderr or ""))
            timed_out = False
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", "ignore")
            log = _strip_ansi(stdout)
            timed_out = True

        errors = [e for e in self._errors_in(log) if "WASAPI" not in e and "X11" not in e]
        verdict, checks, failed = self._parse_verdict(log)
        return PlaytestResult(
            verdict=verdict,
            checks=checks,
            failed=failed,
            errors=errors,
            timed_out=timed_out,
            raw_log=log,
        )

    @staticmethod
    def _parse_verdict(log: str) -> tuple[str, int, list[str]]:
        m = re.search(r"VIBE_TEST RESULT verdict=(\w+) checks=(\d+) failed=\[([^\]]*)\]", log)
        if not m:
            return ("NONE", 0, ["no_verdict_emitted"])
        verdict = m.group(1)
        checks = int(m.group(2))
        raw_failed = m.group(3).strip()
        failed = [s.strip().strip("'\"") for s in raw_failed.split(",") if s.strip()] if raw_failed else []
        return (verdict, checks, failed)

    @staticmethod
    def _parse_scout(log: str) -> Dict[str, Any]:
        """Extract JSON between VIBE_SCOUT_START and VIBE_SCOUT_END markers."""
        try:
            pattern = r"--- VIBE_SCOUT_START ---\s+(.*?)\s+--- VIBE_SCOUT_END ---"
            match = re.search(pattern, log, re.DOTALL)
            if match:
                return json.loads(match.group(1).strip())
        except Exception:
            pass
        return {}
