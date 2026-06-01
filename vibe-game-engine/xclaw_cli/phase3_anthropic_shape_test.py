"""Offline proof that the Anthropic provider calls the SDK correctly and drives the
loop+gate to a passing edit. Mocks `anthropic.Anthropic` so no key / network is needed.

Asserts the request shape mandated by the claude-api skill:
  model=claude-opus-4-8, thinking adaptive, structured-output json_schema, cached system.

    python -m xclaw_cli.phase3_anthropic_shape_test
"""
from __future__ import annotations

import json
import sys
import types

import anthropic

from xclaw_cli import config
from xclaw_cli.generator import LLMGenerator
from xclaw_cli.headless import GodotHeadless
from xclaw_cli.llm import AnthropicClient
from xclaw_cli.loop import run_loop
from xclaw_cli.workspace import prepare_workspace

TEMPLATE = "Starter-Kit-3D-Platformer"
captured: dict = {}


def _make_fake_anthropic():
    def create(**kwargs):
        captured.update(kwargs)
        # Build a valid full-file edit from the player.gd embedded in the user content.
        user = kwargs["messages"][0]["content"]
        marker = "--- res://scripts/player.gd ---"
        idx = user.find(marker)
        block = user[idx + len(marker):]
        nxt = block.find("\n--- ")
        content = (block[:nxt] if nxt != -1 else block).strip("\n")
        content = content.replace("@export var jump_strength = 7", "@export var jump_strength = 13")
        payload = json.dumps({"summary": "raise jump", "writes": [{"path": "res://scripts/player.gd", "content": content}]})
        text_block = types.SimpleNamespace(type="text", text=payload)
        return types.SimpleNamespace(content=[text_block])

    class FakeAnthropic:
        def __init__(self, *a, **k):
            self.messages = types.SimpleNamespace(create=create)

    return FakeAnthropic


def _log(m: str) -> None:
    print(f"[phase3-anthropic] {m}", flush=True)


def main() -> int:
    anthropic.Anthropic = _make_fake_anthropic()  # type: ignore[attr-defined]

    client = AnthropicClient(model="claude-opus-4-8")
    godot = GodotHeadless(config.resolve_godot_exe())
    project_dir, run_id = prepare_workspace(TEMPLATE)
    _log(f"run_id={run_id}")

    result = run_loop(project_dir, "make the player jump higher", LLMGenerator(client, on_event=_log), godot, max_attempts=2, on_event=_log)

    # Request-shape assertions (don't guess SDK usage — prove it).
    assert captured.get("model") == "claude-opus-4-8", captured.get("model")
    assert captured.get("thinking") == {"type": "adaptive"}, captured.get("thinking")
    fmt = captured.get("output_config", {}).get("format", {})
    assert fmt.get("type") == "json_schema" and "schema" in fmt, fmt
    sys_block = captured.get("system", [{}])[0]
    assert sys_block.get("cache_control", {}).get("type") == "ephemeral", sys_block
    _log("request shape OK: model/thinking/output_config/cache_control all correct")

    if not (result.ok and result.attempts == 1):
        _log(f"FAIL: loop ok={result.ok} attempts={result.attempts}")
        return 1

    _log("PHASE 3 ANTHROPIC PASS: SDK call shaped correctly + loop/gate passed.")
    print("PHASE3_ANTHROPIC_RESULT=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
