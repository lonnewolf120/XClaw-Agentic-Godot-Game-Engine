"""Top-level engine: prompt -> isolated template copy -> LLM loop -> headless-gated result.

Routes around the broken legacy orchestration entirely. v1 = script-level edits only.
Optional --export flag triggers Godot export after a successful loop.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from xclaw_cli import config
from xclaw_cli.catalog import DEFAULT_TEMPLATE, select_template
from xclaw_cli.exporter import ExportConfig, ExportOutcome, ExportTarget, export_project
from xclaw_cli.generator import LLMGenerator
from xclaw_cli.headless import GodotHeadless
from xclaw_cli.llm import get_client
from xclaw_cli.loop import LoopResult, run_loop
from xclaw_cli.workspace import prepare_workspace


@dataclass
class EngineResult:
    run_id: str
    project_dir: str
    ok: bool
    attempts: int
    summary: str
    bundle_path: str
    template: str
    selection_reason: str
    export: ExportOutcome | None = None


def _write_bundle(
    *,
    run_id: str,
    project_dir: Path,
    prompt: str,
    template: str,
    selection_reason: str,
    requested_template: str | None,
    baseline_ok: bool,
    fallback_from: str | None,
    provider: str,
    model: str | None,
    result: LoopResult,
    export_requested: bool = False,
    export_outcome: ExportOutcome | None = None,
) -> Path:
    bundle = {
        "run_id": run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "prompt": prompt,
        "template": template,
        "requested_template": requested_template,
        "selection_reason": selection_reason,
        "baseline_ok": baseline_ok,
        "fallback_from": fallback_from,
        "provider": provider,
        "model": model,
        "ok": result.ok,
        "attempts": result.attempts,
        "export_requested": export_requested,
        "project_dir": str(project_dir),
        "history": [
            {
                "attempt": rec.attempt,
                "files_written": rec.files_written,
                "ok": rec.check.ok,
                "summary": rec.check.summary(),
                "errors": rec.check.errors[:20],
            }
            for rec in result.history
        ],
    }
    if export_outcome:
        bundle["export"] = {
            "ok": export_outcome.ok,
            "output_path": export_outcome.output_path,
            "size_bytes": export_outcome.size_bytes,
            "sha256": export_outcome.sha256,
            "error": export_outcome.error,
            "command": export_outcome.command,
        }
    bundle_path = project_dir.parent / "run_bundle.json"
    bundle_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    return bundle_path


def generate(
    prompt: str,
    *,
    template: str | None = None,
    provider: str = "anthropic",
    model: str | None = None,
    max_attempts: int = 3,
    export: bool = False,
    export_target: str = "windows",
    export_path: str | None = None,
    on_event: Callable[[str], None] | None = None,
) -> EngineResult:
    def emit(msg: str) -> None:
        if on_event:
            on_event(msg)

    godot = GodotHeadless(config.resolve_godot_exe())
    emit(f"godot={godot.godot_exe}")

    # Template: explicit wins; otherwise score the prompt against the catalog.
    requested_template = template
    if template:
        selection_reason = "explicit (--template)"
        emit(f"template={template} (explicit)")
    else:
        sel = select_template(prompt)
        template = sel.name
        selection_reason = sel.reason
        emit(f"template={template} (auto-selected, score={sel.score:.1f}: {sel.reason})")

    project_dir, run_id = prepare_workspace(template)
    emit(f"run_id={run_id} template={template} project_dir={project_dir}")

    # Baseline gate: the chosen template must itself pass headless before the LLM touches
    # it, so the loop starts from a valid project. On failure fall back to the default kit
    # (turns "is this template valid?" into the existing gate, not a hardcoded allowlist).
    emit("baseline: importing + checking pristine template")
    godot.import_project(project_dir)
    baseline = godot.check(project_dir)
    baseline_ok = baseline.ok
    fallback_from: str | None = None
    if not baseline.ok and template != DEFAULT_TEMPLATE:
        emit(f"baseline FAILED for {template} ({baseline.summary()}); falling back to {DEFAULT_TEMPLATE}")
        fallback_from = template
        template = DEFAULT_TEMPLATE
        project_dir, run_id = prepare_workspace(template, run_id=f"{run_id}-fallback")
        godot.import_project(project_dir)
        baseline = godot.check(project_dir)
        baseline_ok = baseline.ok
    emit(f"baseline: {baseline.summary()}")

    client = get_client(provider, model)
    emit(f"llm provider={client.name} model={model or 'default'}")
    generator = LLMGenerator(client, on_event=emit)

    # Template already imported above for the baseline gate.
    result = run_loop(
        project_dir, prompt, generator, godot,
        max_attempts=max_attempts, import_first=False, on_event=emit,
    )

    # ── Export (optional) ──────────────────────────────────────────────
    export_outcome: ExportOutcome | None = None
    if export and result.ok:
        emit("export: starting")
        try:
            tgt = ExportTarget(export_target)
        except ValueError:
            tgt = ExportTarget.WINDOWS
        ecfg = ExportConfig(target=tgt, output_path=export_path)
        export_outcome = export_project(
            project_dir, godot.godot_exe, cfg=ecfg, on_event=emit,
        )
    elif export and not result.ok:
        emit("export: SKIPPED — LLM loop did not produce a valid project")

    bundle_path = _write_bundle(
        run_id=run_id,
        project_dir=project_dir,
        prompt=prompt,
        template=template,
        selection_reason=selection_reason,
        requested_template=requested_template,
        baseline_ok=baseline_ok,
        fallback_from=fallback_from,
        provider=provider,
        model=model,
        result=result,
        export_requested=export,
        export_outcome=export_outcome,
    )
    final = result.final_check
    summary = final.summary() if final else "no_attempts"
    emit(f"RESULT ok={result.ok} attempts={result.attempts} template={template} ({summary})")
    if export_outcome:
        emit(f"EXPORT ok={export_outcome.ok} {export_outcome.summary()}")
    emit(f"bundle={bundle_path}")

    return EngineResult(
        run_id=run_id,
        project_dir=str(project_dir),
        ok=result.ok,
        attempts=result.attempts,
        summary=summary,
        bundle_path=str(bundle_path),
        template=template,
        selection_reason=selection_reason,
        export=export_outcome,
    )
