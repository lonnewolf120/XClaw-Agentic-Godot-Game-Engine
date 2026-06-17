"""Phase 2 game-authoring generator.

Teaches the model the schema-driven contract: it writes DATA (game_spec.json) + a small
player controller, NOT scenes or framework. The deterministic vibe_game/ runtime turns the
spec into a playable game; the playtest gate verifies it. Each attempt rewrites the full
files; failures from the gate feed back for repair.
"""
from __future__ import annotations

import json

from xclaw_cli.edits import FileWrite, read_file
from xclaw_cli.llm import LLMClient, LLMError

GAME_SYSTEM_PROMPT = """You are a senior Godot 4.6 game designer using the XClaw schema-driven runtime.

You do NOT build scenes, autoloads, or framework code. A TESTED runtime (res://vibe_game/) already
exists and, from a single data file, builds the ENTIRE playable game: main menu, every level's
platforms/hazards/enemies/coins/goal, the player, camera, HUD, score, lives, win/lose, game-over and
restart. Your job is to provide the DATA and the player's movement script.

YOU WRITE EXACTLY TWO FILES:
1. res://game_spec.json  — the whole game as DATA (schema below).
2. res://scripts/player.gd — the player movement controller.

=== game_spec.json schema ===
{
  "meta": { "title": str, "dimension": "2d", "genre": str },
  "progression": { "lives": int>=1, "win": "clear_all_levels" },
  "player": { "script": "res://scripts/player.gd", "size": {"w": int, "h": int}, "color": "#rrggbb" },
  "levels": [                      // >= 1 level
    {
      "name": str,
      "bounds": { "w": int, "h": int },
      "player_spawn": { "x": int, "y": int },          // CENTER
      "platforms":    [ { "x": int, "y": int, "w": int>0, "h": int>0 } ],   // (x,y)=TOP-LEFT, >=1 required
      "hazards":      [ { "type": "spike"|"pit", "x": int, "y": int, "w": int, "h": int } ],  // TOP-LEFT
      "enemies":      [ { "type": "patroller"|"chaser", "x": int, "y": int, "patrol": int, "speed": int } ], // CENTER
      "collectibles": [ { "type": "coin", "x": int, "y": int, "score": int } ],   // CENTER
      "goal":         { "x": int, "y": int, "w": int, "h": int }            // TOP-LEFT, required
    }
  ]
}
Only the listed type strings are allowed (unknown types are rejected). Every coordinate must be
within [0..bounds.w] x [0..bounds.h].

COORDINATES: Godot 2D — y is DOWN-positive (larger y = LOWER on screen). A ground platform has a
LARGER y than the player_spawn that sits above it. Example: spawn y=500, ground platform y=600.

REACHABILITY (critical — an automated bot plays every level): the bot HOLDS RIGHT and hops when it
stalls against a wall/step. Design accordingly:
- CONTINUOUS ground from spawn to goal. NO death-pits / gaps the player can fall through.
- Step-UPS must be <= 100px tall (the bot hops them). Step-DOWNS may be any height.
- Put the goal at the far right at ground level and make it tall (h >= 180) so the player hits it.
- Do NOT block the single ground path with hazards/enemies — put them on ledges above the path or
  off to the side (the gate teleport-tests them separately; they must merely exist and be lethal).
- This is generous greybox, not a precision platformer.

=== player.gd contract ===
extends CharacterBody2D. The runtime ALREADY added this body's CollisionShape2D and visual — do NOT
add child nodes. Implement ONLY movement in _physics_process(delta):
- Use ONLY built-in input actions: ui_left, ui_right, ui_accept. The project has NO custom input
  map; invented action names resolve to nothing and silently break the game and the test bot.
- Gravity while not is_on_floor(); horizontal velocity = Input.get_axis("ui_left","ui_right")*SPEED;
  jump (velocity.y = a negative JUMP) when is_on_floor() and Input.is_action_just_pressed("ui_accept");
  then move_and_slide(). Use `func` (never def) and tabs.
- If the request asks to track/emit something, you MAY use the autoloads VibeState / VibeEvents.

OUTPUT — STRICT JSON ONLY (no prose, no code fences). For game_spec.json put the spec as a nested
JSON OBJECT (not a stringified string); for player.gd put the file as a STRING:
{"summary": "<one line>", "writes": [
  {"path": "res://game_spec.json", "content": { ...the full game spec object... }},
  {"path": "res://scripts/player.gd", "content": "extends CharacterBody2D\\n..."}
]}
"""

_MAX_SPEC_CHARS = 5000
_MAX_SCRIPT_CHARS = 3000


def _build_game_user_prompt(prompt: str, project_dir, last_feedback: list[str]) -> str:
    parts: list[str] = [f"GAME REQUEST:\n{prompt}\n"]

    spec = read_file(project_dir, "game_spec.json")
    if spec:
        if len(spec) > _MAX_SPEC_CHARS:
            spec = spec[:_MAX_SPEC_CHARS] + "\n...(truncated)\n"
        parts.append("CURRENT game_spec.json:\n" + spec)
    player = read_file(project_dir, "scripts/player.gd")
    if player:
        if len(player) > _MAX_SCRIPT_CHARS:
            player = player[:_MAX_SCRIPT_CHARS] + "\n# ...(truncated)\n"
        parts.append("CURRENT scripts/player.gd:\n" + player)

    if last_feedback:
        parts.append(
            "THE PREVIOUS ATTEMPT FAILED THE AUTOMATED PLAYTEST WITH:\n"
            + "\n".join(f"- {f}" for f in last_feedback[:20])
            + "\nFix the root cause and return the FULL corrected game_spec.json AND player.gd. "
            "If a level was unreachable (player_x well below goal_x), make the ground continuous "
            "and flatten step-ups to <= 100px."
        )

    return "\n".join(parts)


def _extract_json_object(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        nl = text.find("\n")
        if nl != -1:
            text = text[nl + 1:]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise LLMError("model did not return a JSON object")
        return json.loads(text[start:end + 1])


def _parse_game_writes(raw: str) -> tuple[str, list[FileWrite]]:
    data = _extract_json_object(raw)
    writes_raw = data.get("writes", [])
    if not isinstance(writes_raw, list):
        raise LLMError("model JSON missing a 'writes' array")
    writes: list[FileWrite] = []
    for item in writes_raw:
        if not isinstance(item, dict):
            continue
        path = str(item.get("path", "")).strip()
        content = item.get("content", "")
        # The model may embed the spec as a JSON string OR as a nested object — accept both.
        if path.endswith(".json") and isinstance(content, (dict, list)):
            content = json.dumps(content, indent=2)
        if (path.endswith(".gd") or path.endswith(".json")) and isinstance(content, str) and content.strip():
            if not path.startswith("res://"):
                path = "res://" + path.lstrip("/\\")
            writes.append(FileWrite(path, content))
    if not writes:
        raise LLMError("model returned no usable writes (.json/.gd)")
    return str(data.get("summary", "")), writes


class GameLLMGenerator:
    def __init__(self, client: LLMClient, on_event=None) -> None:
        self.client = client
        self.on_event = on_event

    def __call__(self, prompt: str, project_dir, last_feedback: list[str]) -> tuple[str, list[FileWrite]]:
        user = _build_game_user_prompt(prompt, project_dir, last_feedback)
        try:
            raw = self.client.complete(GAME_SYSTEM_PROMPT, user)
        except Exception as exc:
            raise LLMError(f"{type(exc).__name__}: {exc}") from exc
        summary, writes = _parse_game_writes(raw)
        if self.on_event:
            self.on_event(f"llm: {summary or '(no summary)'} -> {len(writes)} file(s)")
        return summary, writes
