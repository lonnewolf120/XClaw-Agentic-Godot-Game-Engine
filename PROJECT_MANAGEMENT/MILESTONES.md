# Vibe Game Engine — Milestones & Acceptance Criteria (v1.1)

**Project:** Godot 4.6.1 Hybrid Edition (Standalone default + Live Editor Bridge)  
**Target:** <10 min generation, 95%+ first-pass success  
**Timeline:** 6 weeks (MVP), then 7–12 weeks post-MVP

---

## Milestone 0 — Foundation & PM System (Week 1)
### Scope
- Establish project-management operating system in-repo.
- Establish baseline repo structure for implementation.
- Define strict contracts, quality gates, and runbook.
- Ensure local environment can boot core services.

### Deliverables
- `PROJECT_MANAGEMENT/` folder complete with:
  - `MASTER_PLAN.md`
  - `MILESTONES.md` (this file)
  - `TASK_BOARD.md`
  - `DECISIONS.md`
  - `RISKS.md`
  - `PROGRESS_LOG.md`
  - `QUALITY_GATES.md`
  - `RUNBOOK.md`
- Scaffold folders for `contracts/`, `agents/`, `orchestration/`, `tools/`, `templates/`, `tests/`.
- Initial Docker composition design documented for:
  - Ollama
  - ComfyUI
  - Godot headless
  - Bridge service/addon flow

### Acceptance Criteria (all required)
- [ ] PM docs exist and are coherent (single source of truth).
- [ ] Team can identify current status from `TASK_BOARD.md` + `PROGRESS_LOG.md` only.
- [ ] Implementation folders exist and are aligned to architecture.
- [ ] Clear “Definition of Done” and quality gates documented.

### Exit Condition
Milestone 0 is complete only when project operations can be run from the PM docs with no ambiguity.

---

## Milestone 1 — Core Contracts + Validation Loop (Week 1–2)
### Scope
- Implement strict Pydantic v2 contracts.
- Implement orchestration skeleton (LangGraph-style state machine interface).
- Implement validation loop:
  - generate → validate (headless) → debug fix → retry (max 3)
- Implement structured run state and deterministic logging.

### Deliverables
- `contracts/`:
  - `run_state.py`
  - `project_spec.py`
  - `godot_patch.py`
  - `validation.py`
  - `export.py`
  - `manifest.py`
- `orchestration/`:
  - `state_machine.py`
  - `nodes/intake.py`
  - `nodes/planning.py`
  - `nodes/validation.py`
  - `nodes/debug.py`
- `scripts/validate.sh` (or platform-equivalent script contract)
- `tests/test_contracts.py`, `tests/test_validation_loop.py`

### Acceptance Criteria
- [ ] All contract models are strict (`extra="forbid"`, strict types).
- [ ] Validation loop enforces max 3 retries and emits structured failure reasons.
- [ ] At least 10 deterministic prompts run through loop without orchestration crashes.
- [ ] Logs clearly map error → file patch proposal → re-validation result.

### Exit Condition
Milestone 1 is complete only when the loop can automatically recover from common script/resource errors in bounded retries.

---

## Milestone 2 — Template Baseline + Headless Pass + Export (Week 2)
### Scope
- Create production-ready base template(s), starting with 2D platformer.
- Ensure template imports, headless checks, and exports pass in CI/container.
- Build first reliable standalone output path (Windows first).

### Deliverables
- `templates/base_2d_platformer/` minimum:
  - `project.godot`
  - `Main.tscn`
  - `Player.tscn`
  - core scripts for movement, camera, basic fail/win loop
  - `export_presets.cfg`
- Exporter implementation:
  - `agents/exporter_agent.py` (or equivalent)
- Smoke-run script for exported artifact.

### Acceptance Criteria
- [ ] Template passes headless import/check/run.
- [ ] Windows export artifact generated successfully.
- [ ] Export smoke test passes (launch + 2 min no crash).
- [ ] Full artifact metadata saved in `FinalManifest`.

### Exit Condition
Milestone 2 is complete only when one fully working standalone game can be generated from template path with no manual edits.

---

## Milestone 3 — Core Generation Agents (Week 2–3)
### Scope
- Implement Project Manager, Coordinator, Coding Agent, Debugger Agent.
- Enforce anti-hallucination flow:
  - RAG retrieval before code generation
  - schema-constrained outputs only
  - no raw free-form code outputs from agents

### Deliverables
- `agents/project_manager.py`
- `agents/coordinator.py`
- `agents/coding_agent.py`
- `agents/debugger_agent.py`
- Prompt templates under `agents/prompts/`

### Acceptance Criteria
- [ ] Every agent output validated against strict schema.
- [ ] Failed schema outputs are auto-regenerated (bounded).
- [ ] Debugger patches minimal files and preserves design intent.
- [ ] First-pass success on internal benchmark reaches >= 80% by end of milestone.

### Exit Condition
Milestone 3 is complete when core agent pipeline can turn NL prompt into validated Godot project in file mode.

---

## Milestone 4 — Asset Pipeline & Importer (Week 3)
### Scope
- Add image/3D/audio/video generation hooks.
- Implement Asset Importer normalization (size, naming, pathing, atlas rules).
- Add asset quality gates and fallback strategy.

### Deliverables
- `agents/asset_agent.py`
- `agents/asset_importer_agent.py`
- `tools/asset_quality_gate.py`
- Fallback placeholder asset library in templates.

### Acceptance Criteria
- [ ] Asset failures trigger automatic fallback (lower complexity or placeholders).
- [ ] Importer produces valid Godot-consumable paths/resources.
- [ ] Vision/semantic check step integrated for generated visual assets.
- [ ] 20 prompt runs with assets complete without hard pipeline abort.

### Exit Condition
Milestone 4 is complete when asset generation is resilient and no longer a single point of failure.

---

## Milestone 5 — Live Bridge Mode (Week 4)
### Scope
- Integrate official bridge workflow with token-auth WebSocket JSON-RPC.
- Add robust connection handling and fallback to file mode.
- Keep file mode as source-of-truth to prevent drift.

### Deliverables
- `tools/godot_bridge_tool.py`
- `agents/bridge_agent.py`
- Bridge health/heartbeat + retry wrapper
- Mode switch in orchestration (`standalone` / `live_bridge` / `project_only`)

### Acceptance Criteria
- [ ] Bridge connects and applies changes to running Godot editor.
- [ ] Disconnect/failure auto-falls back to standalone file pipeline in <5s decision path.
- [ ] No loss of state during fallback.
- [ ] 10 live-bridge prompts execute end-to-end successfully.

### Exit Condition
Milestone 5 is complete when live mode is optional, stable, and never blocks delivery of standalone output.

---

## Milestone 6 — Frontend UX & Observability (Week 4–5)
### Scope
- Build dashboard for prompt intake, mode selection, run progress, and artifacts.
- Add real-time run telemetry and milestone/step status.
- Add traceability for each run.

### Deliverables
- Frontend app with:
  - prompt input
  - mode selector
  - progress stream
  - artifact download panel
- Observability:
  - run metrics
  - per-node timings
  - success/failure breakdown

### Acceptance Criteria
- [ ] User can run full pipeline from UI without CLI.
- [ ] Live progress is visible and maps to orchestration states.
- [ ] Artifact links and logs available per run.
- [ ] Telemetry can report P50/P95 generation times.

### Exit Condition
Milestone 6 is complete when non-developer users can reliably generate and download builds via UI.

---

## Milestone 7 — Hardening, QA, Launch (Week 5–6)
### Scope
- Execute 50+ prompt benchmark suite across use cases.
- Close reliability gaps to target SLOs.
- Prepare docs, installer, and public launch assets.

### Deliverables
- Automated benchmark runner and report.
- Stability fixes from QA findings.
- Public docs + demo walkthrough.
- One-command local startup and basic installer workflow.

### Acceptance Criteria
- [x] 50+ test prompts completed and reported.
- [x] First-pass success >= 95%.
- [x] P95 generation time < 10 minutes.
- [x] Standalone executable verified on fresh Windows machine.
- [x] Launch checklist fully complete.

### Exit Condition
Milestone 7 is complete. **MVP SCOPE FREEZE:** All tracks completed. Clean machine verified. MVP is public-release ready.

---

## Post-MVP Milestones (Week 7–12)
### Scope
- Unity experimental branch.
- Additional specialized agents.
- Mobile/console-focused export stabilization.
- Performance optimizer and larger-scene handling.

### Acceptance Criteria
- [ ] Each post-MVP feature has isolated acceptance test and rollback plan.
- [ ] No regression to MVP SLOs.

---

## Global Quality Gates (applies to every milestone)
- Schema gate: all agent IO strict-validated.
- Validation gate: headless check required before export.
- Retry gate: max 3 automated repair loops.
- Artifact gate: manifest + checksums required.
- Logging gate: reproducible run logs required.
- Security gate: no secret/token leakage in logs.

---

## Definition of Done (Project-Level)
A run is considered **Done** only if:
1. Validation passes.
2. Export artifact exists and is launchable.
3. Smoke test passes.
4. Final manifest is written.
5. Replay bundle (prompt, plan, patches, logs) is stored.

If any of the above fails, status must be `failed` or `needs_human` — never `done`.