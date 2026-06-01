"""Phase 3 wiring proof with a deterministic FakeClient (no network/quota needed).

Proves the full machine: context build -> LLM JSON -> parse full-file writes -> apply ->
headless gate -> pass. The fake extracts the real player.gd from the generated context
(verifying _build_user_prompt includes file contents) and returns a valid modified file.

    python -m xclaw_cli.phase3_fake_test
"""
from __future__ import annotations

import json
import sys

from xclaw_cli import config
from xclaw_cli.edits import read_file
from xclaw_cli.generator import LLMGenerator
from xclaw_cli.headless import GodotHeadless
from xclaw_cli.llm import FakeClient
from xclaw_cli.loop import run_loop
from xclaw_cli.workspace import prepare_workspace

TEMPLATE = "Starter-Kit-3D-Platformer"


def fake_responder(system: str, user: str) -> str:
    marker = "--- res://scripts/player.gd ---"
    idx = user.find(marker)
    assert idx != -1, "context did not include player.gd"
    block = user[idx + len(marker):]
    nxt = block.find("\n--- ")
    content = (block[:nxt] if nxt != -1 else block).strip("\n")
    # Apply the "requested" change as a full-file replacement.
    content = content.replace("@export var jump_strength = 7", "@export var jump_strength = 14")
    return json.dumps({"summary": "raise jump_strength", "writes": [{"path": "res://scripts/player.gd", "content": content}]})


def _log(msg: str) -> None:
    print(f"[phase3-fake] {msg}", flush=True)


def main() -> int:
    godot = GodotHeadless(config.resolve_godot_exe())
    project_dir, run_id = prepare_workspace(TEMPLATE)
    _log(f"run_id={run_id}")

    generator = LLMGenerator(FakeClient(fake_responder), on_event=_log)
    result = run_loop(project_dir, "make the player jump higher", generator, godot, max_attempts=2, on_event=_log)

    if not (result.ok and result.attempts == 1):
        _log(f"FAIL: expected pass at attempt 1, got ok={result.ok} attempts={result.attempts}")
        return 1

    player = read_file(project_dir, "res://scripts/player.gd") or ""
    if "@export var jump_strength = 14" not in player:
        _log("FAIL: edit not actually applied to player.gd")
        return 1

    _log("PHASE 3 WIRING PASS: context->LLM JSON->apply->headless gate, edit landed.")
    print("PHASE3_FAKE_RESULT=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
