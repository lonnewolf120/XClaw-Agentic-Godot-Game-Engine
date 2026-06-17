"""Phase 2 agentic game authoring: NL prompt -> full playable game, gated by the playtest.

Multi-attempt repair loop driving any LLMClient (works keyless via the claude-code provider):
  generate (game_spec.json + player.gd) -> apply -> validate spec -> godot parse -> playtest
  -> feed failures back -> retry until the gate is green or the attempt cap is hit.

The vibe_game/ runtime is template-independent (it builds all geometry from the spec), so any 2D
template works; we use the minimal base_2d_platformer.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from xclaw_cli import config, gamespec
from xclaw_cli.edits import FileWrite, apply_writes
from xclaw_cli.game_generator import GameLLMGenerator
from xclaw_cli.headless import GodotHeadless
from xclaw_cli.llm import LLMError, get_client
from xclaw_cli.workspace import prepare_workspace

GAME_TEMPLATE = "base_2d_platformer"


@dataclass
class GameAttempt:
    attempt: int
    summary: str
    files_written: list[str]
    ok: bool
    feedback: list[str] = field(default_factory=list)


@dataclass
class GameResult:
    run_id: str
    project_dir: str
    ok: bool
    attempts: int
    history: list[GameAttempt] = field(default_factory=list)
    bundle_path: str = ""


def run_game_gate(
    godot: GodotHeadless, project_dir: Path, written_paths: set[str]
) -> tuple[bool, list[str]]:
    """Validate the spec, parse-check the project, then run the playtest. Returns (ok, feedback)."""
    # 1. Spec schema (cheapest, most actionable).
    try:
        gamespec.load_and_validate(project_dir / "game_spec.json", written_paths=written_paths)
    except gamespec.SpecError as exc:
        return False, ["game_spec invalid: " + e for e in exc.errors]

    # 2. Godot parse / load.
    chk = godot.check(project_dir)
    if not chk.ok:
        return False, ["godot parse error: " + e for e in chk.errors[:15]]

    # 3. Behavioral playtest.
    pt = godot.run_playtest(project_dir)
    if pt.ok:
        return True, []
    fb = pt.feedback()
    return False, fb if fb else [pt.summary()]


def _written_res_paths(writes: list[FileWrite]) -> set[str]:
    out: set[str] = set()
    for w in writes:
        p = w.path if w.path.startswith("res://") else "res://" + w.path.lstrip("/\\")
        out.add(p)
    return out


def generate_game(
    prompt: str,
    *,
    provider: str = "claude-code",
    model: str | None = None,
    max_attempts: int = 4,
    template: str = GAME_TEMPLATE,
    on_event: Callable[[str], None] | None = None,
) -> GameResult:
    def emit(msg: str) -> None:
        if on_event:
            on_event(msg)

    godot = GodotHeadless(config.resolve_godot_exe())
    emit(f"godot={godot.godot_exe}")

    project_dir, run_id = prepare_workspace(template, inject_game_runtime=True)
    emit(f"run_id={run_id} template={template} project={project_dir}")

    # Baseline: the injected runtime + template must parse before the model touches anything.
    godot.import_project(project_dir)
    baseline = godot.check(project_dir)
    emit(f"baseline: {baseline.summary()}")

    client = get_client(provider, model)
    emit(f"llm provider={client.name} model={model or 'default'}")
    generator = GameLLMGenerator(client, on_event=emit)

    history: list[GameAttempt] = []
    last_feedback: list[str] = []
    ok = False

    for attempt in range(1, max_attempts + 1):
        emit(f"attempt {attempt}/{max_attempts}: generating")
        try:
            summary, writes = generator(prompt, project_dir, last_feedback)
        except LLMError as exc:
            emit(f"attempt {attempt}: generation failed: {exc}")
            history.append(GameAttempt(attempt, f"generation error: {exc}", [], False, [str(exc)]))
            last_feedback = [f"your previous output could not be parsed: {exc}. Return STRICT JSON only."]
            continue

        written = apply_writes(project_dir, writes)
        emit(f"attempt {attempt}: wrote {len(written)} file(s)")

        # Register any new scripts/resources before gating.
        godot.import_project(project_dir)
        gate_ok, feedback = run_game_gate(godot, project_dir, _written_res_paths(writes))
        history.append(GameAttempt(attempt, summary, written, gate_ok, feedback))

        if gate_ok:
            emit(f"attempt {attempt}: PLAYTEST PASSED")
            ok = True
            break
        emit(f"attempt {attempt}: gate failed ({len(feedback)} issue(s))")
        for f in feedback[:8]:
            emit(f"   - {f}")
        last_feedback = feedback

    bundle_path = _write_bundle(run_id, project_dir, prompt, provider, model, ok, history)
    emit(f"RESULT ok={ok} attempts={len(history)} bundle={bundle_path}")
    return GameResult(
        run_id=run_id,
        project_dir=str(project_dir),
        ok=ok,
        attempts=len(history),
        history=history,
        bundle_path=str(bundle_path),
    )


def _write_bundle(
    run_id: str,
    project_dir: Path,
    prompt: str,
    provider: str,
    model: str | None,
    ok: bool,
    history: list[GameAttempt],
) -> Path:
    bundle = {
        "run_id": run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "game_authoring",
        "prompt": prompt,
        "provider": provider,
        "model": model,
        "ok": ok,
        "attempts": len(history),
        "project_dir": str(project_dir),
        "history": [
            {
                "attempt": a.attempt,
                "summary": a.summary,
                "files_written": a.files_written,
                "ok": a.ok,
                "feedback": a.feedback[:20],
            }
            for a in history
        ],
    }
    path = project_dir.parent / "run_bundle.json"
    path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    return path
