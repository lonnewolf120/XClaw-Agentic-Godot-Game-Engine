"""LLM generator: builds bounded context, calls the model, parses full-file writes.

One model call per loop attempt (cheap, deterministic). On retry the headless errors are
fed back so the model repairs exactly what failed.
"""
from __future__ import annotations

import json

from xclaw_cli.edits import FileWrite, list_files, read_file
from xclaw_cli.llm import LLMClient, LLMError
from xclaw_cli.loop import LoopContext

SYSTEM_PROMPT = """You are a senior Godot 4.6 GDScript engineer. You build a FULLY FUNCTIONAL game by editing an EXISTING, valid Godot project. 

VIBE CORE FRAMEWORK (MANDATORY USE)
Your project has a high-performance core library at `res://vibe_core/`. Use it to ensure organization and optimization:
1. VibeEvents (Autoload): The global signal bus. Use it for decoupled events.
2. VibeState (Autoload): Central game state (score, health, etc.).
3. VibeTraits (Autoload): Safe logic injection. Use `VibeTraits.add(node, "Name")` to attach logic to nodes without editing their scripts.
4. VibeEntity (Class): Base class for NPCs/Players with optimized health/damage logic.

HARD RULES
- PREFER TRAITS: Use the `VibeTraits` system to add modular logic to user-created nodes discovered by the Scout.
- Do not rewrite user scenes or large existing scripts if a Trait can do the job.
- Only modify GDScript (.gd) files. Never edit .tscn, .tres, or project.godot directly.
- Each write REPLACES THE ENTIRE FILE: include the complete, valid GDScript 4.6 file content.
- Use `func` (never Python `def`). Tabs for indentation.

OUTPUT
Return STRICT JSON only:
{"summary": "<one line>", "writes": [{"path": "res://scripts/x.gd", "content": "<full file>"}]}
"""

_MAX_FILE_CHARS = 6000


def _build_user_prompt(ctx: LoopContext) -> str:
    parts: list[str] = [f"USER REQUEST:\n{ctx.prompt}\n"]

    tree = list_files(ctx.project_dir, exts=(".gd", ".tscn", ".godot"))
    parts.append("PROJECT FILES:\n" + "\n".join(tree) + "\n")

    parts.append("CURRENT GDSCRIPT CONTENTS:")
    for rel in tree:
        if not rel.endswith(".gd"):
            continue
        content = read_file(ctx.project_dir, rel)
        if content is None:
            continue
        if len(content) > _MAX_FILE_CHARS:
            content = content[:_MAX_FILE_CHARS] + "\n# ...(truncated)\n"
        parts.append(f"\n--- {rel} ---\n{content}")

    if ctx.last_errors:
        parts.append(
            "\nPREVIOUS ATTEMPT FAILED THE HEADLESS GODOT CHECK WITH THESE ERRORS:\n"
            + "\n".join(ctx.last_errors[:15])
            + "\nReturn corrected full files that fix these errors."
        )

    # Summarize Runtime Scouting
    if hasattr(ctx, 'scout_data') and ctx.scout_data:
        parts.append("\nRUNTIME SCENE INSIGHTS (SCOUT):")
        globals = ctx.scout_data.get("globals", {})
        if globals:
            parts.append(f"Globals (VibeState): {json.dumps(globals)}")
        
        # Flattened list of significant user nodes
        nodes = []
        def _walk(n, depth=0):
            if not n.get("name", "").startswith("@@"):
                nodes.append(f"{'  '*depth}- {n['name']} ({n['type']})")
                for c in n.get("children", []):
                    _walk(c, depth+1)
        
        _walk(ctx.scout_data.get("tree", {}))
        parts.append("Scene Tree:\n" + "\n".join(nodes[:50]))

    return "\n".join(parts)


def _parse_writes(raw: str) -> tuple[str, list[FileWrite]]:
    text = raw.strip()
    # Tolerate accidental markdown fences.
    if text.startswith("```"):
        text = text.strip("`")
        nl = text.find("\n")
        if nl != -1:
            text = text[nl + 1 :]
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise LLMError("LLM did not return JSON.")
        data = json.loads(text[start : end + 1])

    writes_raw = data.get("writes", [])
    if not isinstance(writes_raw, list):
        raise LLMError("LLM JSON missing a 'writes' array.")
    writes: list[FileWrite] = []
    for item in writes_raw:
        path = str(item.get("path", "")).strip()
        content = item.get("content", "")
        if path.endswith(".gd") and isinstance(content, str) and content.strip():
            writes.append(FileWrite(path, content))
    return str(data.get("summary", "")), writes


class LLMGenerator:
    def __init__(self, client: LLMClient, on_event=None) -> None:
        self.client = client
        self.on_event = on_event

    def __call__(self, ctx: LoopContext) -> list[FileWrite]:
        user = _build_user_prompt(ctx)
        try:
            raw = self.client.complete(SYSTEM_PROMPT, user)
        except Exception as exc:  # surface provider/quota errors cleanly to the loop
            raise LLMError(f"{type(exc).__name__}: {exc}") from exc
        summary, writes = _parse_writes(raw)
        if self.on_event:
            self.on_event(f"llm: {summary or '(no summary)'} -> {len(writes)} file(s)")
        return writes
