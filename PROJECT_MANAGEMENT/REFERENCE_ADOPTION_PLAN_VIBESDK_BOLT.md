# XClaw Reference Adoption Plan (vibesdk + bolt.diy)

**Project:** XClaw Agentic Godot Game Engine  
**Scope:** Dashboard + execution pipeline + preview + build workflow hardening  
**Created:** 2026-03-16  
**Status:** Proposed (Execution-ready after approval)

---

## 1) Objective

Adopt proven workflow patterns from `vibesdk` and `bolt.diy` to accelerate PoC-to-MVP readiness for XClaw while preserving XClaw's core mission:

- Prompt -> playable Godot output
- Mandatory headless validation and strict export
- Deterministic artifacts, logs, replayability, and fail-closed status transitions

This plan does **not** pivot XClaw into a generic web app builder. It selectively imports execution and UX patterns that directly improve reliability, operator experience, and release confidence.

---

## 2) Reference Mapping (What We Reuse)

## From vibesdk (adopt)

1. Deterministic agent state machine with explicit run phases and transitions.
2. Phase-wise generation with progress annotations and resumable execution.
3. Context selection/summarization before generation to reduce noisy prompts.
4. Live preview lifecycle management (start, refresh, ready signals).
5. Durable event stream semantics for timeline/log updates.

## From bolt.diy (adopt)

1. Operator-centric product surface (chat-first + preview + logs + settings).
2. Broadcast-based preview refresh and reload behavior.
3. Integrated runtime terminal/log docking pattern.
4. Provider/configuration ergonomics and settings architecture.
5. Strong CI quality belt (quality, accessibility, performance, PR sizing).

## XClaw-specific constraints (do not dilute)

1. Gate D (runtime validation) and Gate E (export) are mandatory for success.
2. Any gate uncertainty fails closed to `failed` or `needs_human`.
3. Final manifest and checksums are required artifacts for successful runs.
4. Godot-first pipeline remains canonical execution path.

---

## 3) Architecture Target

## A. Control Plane

Introduce explicit run lifecycle states:

`queued -> planning -> generation -> validation_gate_d -> export_gate_e -> packaging -> completed`

Failure branches:

`validation_gate_d_fail -> retry/debug (max 3) -> failed|needs_human`

`export_gate_e_fail -> retry/debug (max 3) -> failed|needs_human`

## B. Event Fabric

Standardize structured event messages (timeline + UI):

- `phase_started`
- `phase_progress`
- `phase_completed`
- `phase_failed`
- `preview_ready`
- `preview_refreshed`
- `artifact_published`

Each event includes: `run_id`, `phase`, `timestamp_utc`, `severity`, `source`, `log_path`.

## C. Preview Subsystem

Three-level preview strategy:

1. Primary: HTML5 Godot export iframe (when available).
2. Secondary: frame/screenshot stream from headless runner.
3. Tertiary: log-first execution console with explicit preview-unavailable reason.

## D. Build/Export Subsystem

Queue-backed export workers with deterministic outputs:

- Input: run bundle + selected target profile
- Output: artifact + checksum + export log path + status
- Policy: never mark completed without successful Gate D and Gate E evidence

---

## 4) Workstreams and Milestones

## WS0 - Governance, Licensing, and Safe Reuse (P0)

Goal: ensure legal and technical reuse discipline.

Tasks:

1. Catalog borrowed patterns and source files (reference register).
2. Confirm license compatibility and attribution requirements.
3. Define import policy: pattern-level reuse first, code copy only where justified.
4. Add "reference provenance" entries in docs for each reused block.

Acceptance:

- Reuse register committed.
- Attribution checklist completed.

## WS1 - Deterministic Orchestration and Phase Contracts (P0)

Goal: align runtime flow with deterministic, observable phases.

Tasks:

1. Add phase contract schema for UI + pipeline state.
2. Emit normalized phase events from all gate transitions.
3. Implement strict transition guardrails (no illegal state hops).
4. Persist event stream in run bundle for replay.

Acceptance:

- Any run can be replayed from phase events.
- Illegal transition attempts are rejected and logged.

## WS2 - Prompt Execution Pipeline Hardening (P0)

Goal: make generation robust and context-aware.

Tasks:

1. Add optional context summarization + file selection pass pre-generation.
2. Integrate phase-wise generation checkpoints.
3. Add bounded continuation semantics for long generations.
4. Standardize retry causes taxonomy (`syntax`, `missing_asset`, `import_fail`, `export_fail`, etc.).

Acceptance:

- Retry causes are machine-classified and reported.
- Generation phases are visible in dashboard timeline.

## WS3 - Preview Runtime and Studio UX (P0)

Goal: production-credible operator experience for non-core users.

Tasks:

1. Wire studio prompt bar to real `/api/game/create` execution.
2. Bind center viewport to latest preview URL/artifact source.
3. Add real-time refresh channel (`preview_ready`, `file_change`, `refresh_preview`).
4. Connect right inspector to actual run graph and scene metadata.
5. Connect bottom dock to real logs (agent + Godot + export).

Acceptance:

- Run can be initiated and monitored end-to-end in dashboard.
- Preview updates without manual page reload.

## WS4 - Build, Export, and Artifact Service (P0)

Goal: export reliability with auditable artifacts.

Tasks:

1. Auto-bootstrap export presets when missing.
2. Enforce Gate D commands in-pipeline (headless import/check/smoke).
3. Enforce Gate E strict export execution with hard fail behavior.
4. Publish artifact metadata + checksums + log paths to final manifest.

Acceptance:

- No run labeled success when export fails.
- Strict export matrix passes target threshold.

## WS5 - Settings and Provider/Mode Control Surface (P1)

Goal: bolt-style operator ergonomics for runtime controls.

Tasks:

1. Add settings panel with mode toggles (local, strict, cost-safe, debug).
2. Add model/provider strategy controls if multi-LLM routing is enabled.
3. Add guardrails for unsafe settings changes during active runs.
4. Persist user/operator preferences.

Acceptance:

- Operators can configure execution modes without editing files.

## WS6 - CI, Quality, and Regression Expansion (P0)

Goal: codify quality as pipeline policy.

Tasks:

1. Add dashboard checks: lint, typecheck, build, unit tests.
2. Add practical accessibility audit for core dashboard flows.
3. Add performance smoke checks for preview and timeline rendering.
4. Add benchmark subset CI run for prompt pipeline.
5. Add PR size and risk-class annotations for reviewer focus.

Acceptance:

- CI reports include quality, accessibility, performance, and regression slices.

## WS7 - Release Readiness and Operationalization (P0)

Goal: pass MVP release gate with operator confidence.

Tasks:

1. Run clean-machine setup drill.
2. Execute 50-prompt benchmark and publish taxonomy report.
3. Validate CLI + dashboard parity of outcomes.
4. Finalize runbook, known limitations, troubleshooting, demo script.

Acceptance:

- Release gate sign-off documented with evidence links.

---

## 5) Execution Order (Critical Path)

1. WS0 governance and reuse safety.
2. WS1 deterministic phase contracts.
3. WS4 Gate D/E hardening (non-negotiable for truthful status).
4. WS3 studio UX wiring to live runtime.
5. WS2 context-aware generation improvements.
6. WS6 CI quality belt.
7. WS7 release hardening.

Rationale: status-truthfulness and export reliability must be solved before UX polish can be trusted.

---

## 6) 4-Week Delivery Plan (PoC -> MVP Readiness)

## Week 1 (Reliability First)

1. Complete WS0 + WS1.
2. Ship Gate D/E enforcement and export preset bootstrap from WS4.
3. Produce strict-export matrix for 4 templates.

Exit criteria:

- >=3/4 strict-export pass rate, including >=2 Kenney templates.
- No false-success runs.

## Week 2 (Studio Wiring)

1. Wire studio UI to real job/run APIs (WS3).
2. Add live timeline/log bindings and preview refresh signals.
3. Add replay/download links from studio.

Exit criteria:

- Dashboard can launch, monitor, and retrieve full run outputs.

## Week 3 (Quality and Scale)

1. Add WS6 CI quality belt.
2. Expand benchmark corpus toward 50 prompts.
3. Add failure taxonomy and owner mapping report.

Exit criteria:

- Deterministic benchmark report generated.
- CI practical subset enabled on major changes.

## Week 4 (Release Gate)

1. Execute clean-machine runbook.
2. Validate CLI/dashboard parity.
3. Finalize all release docs and gate sign-off.

Exit criteria:

- All MVP exit criteria satisfied or blocked with explicit, owned mitigation.

---

## 7) KPI and SLO Targets

1. First-pass success rate: tracked and reported by template category.
2. Retry success rate: tracked separately from first-pass.
3. False-positive completion rate: target 0.
4. Median run duration by mode and template.
5. Preview availability rate per successful run.
6. Export artifact integrity rate (checksum and openability).

---

## 8) Risks and Mitigations

1. Risk: Dashboard polish outpaces backend truthfulness.  
Mitigation: Gate D/E enforcement precedes UI claims.

2. Risk: Borrowed patterns introduce scope creep.  
Mitigation: pattern-level adoption only; exclude unrelated feature sets.

3. Risk: Preview brittleness for non-HTML targets.  
Mitigation: three-level preview fallback strategy.

4. Risk: CI overhead slows iteration.  
Mitigation: practical subset on PR; full suite nightly/release.

5. Risk: Operator confusion from too many settings.  
Mitigation: opinionated defaults + guarded advanced mode.

---

## 9) Deliverables Checklist

1. Reference reuse register + attribution notes.
2. Phase contract schema + event emission implementation.
3. Gate D/E hardening with strict fail-closed behavior.
4. Studio wired to real runtime, logs, preview, artifacts.
5. CI quality belt and benchmark automation.
6. Release gate evidence package.

---

## 10) Session Reporting Format (Mandatory)

Each work session logs:

1. What changed.
2. Why it changed.
3. Evidence commands executed.
4. Pass/fail results.
5. Open blockers.
6. Next three concrete tasks.

This matches current XClaw project management discipline and remains required until MVP sign-off.
