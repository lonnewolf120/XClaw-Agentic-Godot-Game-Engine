"""Covers the baseline-fallback branch in engine.generate (the one path phase4_engine_test
can't reach, since all real templates pass the gate).

Simulates a selected template that FAILS the baseline gate by monkeypatching the headless
check to fail for any project dir that is not the `-fallback` re-prepare. Asserts the engine
falls back to the default kit and records it. No Godot, no key.

    python -m xclaw_cli.phase4_fallback_test
"""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import anthropic

from xclaw_cli import engine
from xclaw_cli.headless import CheckResult, GodotHeadless

PROMPT = "an arcade racing game with cars"  # selects Starter-Kit-Racing


def _make_fake_anthropic():
    def create(**kwargs):
        # A no-op valid edit is enough; the gate is monkeypatched.
        payload = json.dumps({"summary": "noop", "writes": []})
        return types.SimpleNamespace(content=[types.SimpleNamespace(type="text", text=payload)])

    class FakeAnthropic:
        def __init__(self, *a, **k):
            self.messages = types.SimpleNamespace(create=create)

    return FakeAnthropic


def _log(m: str) -> None:
    print(f"[phase4-fallback] {m}", flush=True)


def main() -> int:
    anthropic.Anthropic = _make_fake_anthropic()  # type: ignore[attr-defined]

    # Gate: pass only for the fallback workspace; fail the originally-selected template.
    def fake_check(self, project_dir):
        ok = "-fallback" in str(project_dir)
        errs = [] if ok else ["SCRIPT ERROR: Parse Error: simulated baseline failure"]
        return CheckResult(ok=ok, errors=errs)

    def fake_import(self, project_dir):
        return CheckResult(ok=True)

    GodotHeadless.check = fake_check  # type: ignore[method-assign]
    GodotHeadless.import_project = fake_import  # type: ignore[method-assign]

    result = engine.generate(PROMPT, provider="anthropic", max_attempts=2, on_event=_log)

    bundle = json.loads(Path(result.bundle_path).read_text(encoding="utf-8"))

    checks = {
        "selected racing then fell back": bundle["fallback_from"] == "Starter-Kit-Racing",
        "final template is default": result.template == engine.DEFAULT_TEMPLATE,
        "bundle template is default": bundle["template"] == engine.DEFAULT_TEMPLATE,
        "requested_template None (auto)": bundle["requested_template"] is None,
        "baseline_ok True after fallback": bundle["baseline_ok"] is True,
        "loop converged": result.ok,
        "run dir is the -fallback workspace": "-fallback" in result.project_dir,
    }
    failed = [name for name, ok in checks.items() if not ok]
    for name, ok in checks.items():
        _log(f"{'OK ' if ok else 'FAIL'} {name}")
    if failed:
        _log(f"PHASE 4 FALLBACK FAIL: {failed}")
        print("PHASE4_FALLBACK_RESULT=FAIL")
        return 1

    _log("PHASE 4 FALLBACK PASS: baseline failure falls back to default kit and is recorded.")
    print("PHASE4_FALLBACK_RESULT=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
