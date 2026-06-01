"""XClaw headless CLI game engine.

A single-LLM, text-editing Godot game generator. Edits valid Kenney templates as
text (scripts first), validates with headless Godot, self-corrects from parse/script
errors, and exports a runnable artifact. Routes around the broken legacy orchestration.

See PROJECT_MANAGEMENT/XCLAW_HEADLESS_ENGINE_PLAN.md.
"""

__all__ = ["config", "headless", "workspace"]
