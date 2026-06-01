"""End-to-end Phase 4 proof: engine.generate with auto-selection + baseline gate + bundle.

Mocks the Anthropic SDK (no key/network) but runs the REAL headless Godot gate, so it
exercises the new path: prompt -> auto-selected template -> baseline check -> LLM loop ->
run_bundle.json with selection metadata, in an isolated runs/<id>/ dir.

    python -m xclaw_cli.phase4_engine_test
"""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import anthropic

from xclaw_cli import engine

PROMPT = "polish the experience and make it feel nicer"  # no genre/tag signal -> default kit


def _make_fake_anthropic():
    def create(**kwargs):
        user = kwargs["messages"][0]["content"]
        marker = "--- res://scripts/player.gd ---"
        idx = user.find(marker)
        block = user[idx + len(marker):]
        nxt = block.find("\n--- ")
        content = (block[:nxt] if nxt != -1 else block).strip("\n")
        content = content.replace("@export var jump_strength = 7", "@export var jump_strength = 14")
        payload = json.dumps({"summary": "raise jump", "writes": [{"path": "res://scripts/player.gd", "content": content}]})
        return types.SimpleNamespace(content=[types.SimpleNamespace(type="text", text=payload)])

    class FakeAnthropic:
        def __init__(self, *a, **k):
            self.messages = types.SimpleNamespace(create=create)

    return FakeAnthropic


def _log(m: str) -> None:
    print(f"[phase4-engine] {m}", flush=True)


def main() -> int:
    anthropic.Anthropic = _make_fake_anthropic()  # type: ignore[attr-defined]

    result = engine.generate(PROMPT, provider="anthropic", max_attempts=2, on_event=_log)

    # Auto-selection picked the default kit (no genre signal in the prompt).
    if result.template != engine.DEFAULT_TEMPLATE:
        _log(f"FAIL: expected auto-select {engine.DEFAULT_TEMPLATE}, got {result.template}")
        return 1

    if not result.ok:
        _log(f"FAIL: loop did not converge (ok={result.ok}, attempts={result.attempts})")
        return 1

    # Isolated run dir + bundle with the new selection metadata.
    bundle_path = Path(result.bundle_path)
    if not bundle_path.exists():
        _log(f"FAIL: bundle not written at {bundle_path}")
        return 1
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    for key in ("template", "requested_template", "selection_reason", "baseline_ok", "fallback_from"):
        if key not in bundle:
            _log(f"FAIL: bundle missing key {key!r}")
            return 1
    if bundle["requested_template"] is not None:
        _log(f"FAIL: requested_template should be None (auto), got {bundle['requested_template']!r}")
        return 1
    if not bundle["baseline_ok"]:
        _log("FAIL: baseline_ok should be True for the Kenney kit")
        return 1
    if not Path(result.project_dir).exists():
        _log("FAIL: isolated project_dir missing")
        return 1

    _log(f"selection_reason={bundle['selection_reason']!r} baseline_ok={bundle['baseline_ok']}")
    _log(f"isolated run at {result.project_dir}")
    _log("PHASE 4 ENGINE PASS: auto-select + baseline gate + loop + bundle all correct.")
    print("PHASE4_ENGINE_RESULT=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
