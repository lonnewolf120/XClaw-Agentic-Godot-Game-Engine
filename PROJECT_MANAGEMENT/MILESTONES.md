# Vibe Game Engine — Milestones & Acceptance Criteria (v2.0)

**Project:** Godot 4.6.1 Hybrid Edition (Execution Track → Reliability Track → UX Track)
**Target:** 60-75% first-pass success (90-95% after automatic retries), 8-12 min P50 generation
**Timeline:** 6 weeks (MVP Scope strictly focused and gated)

---

## Phase 0 (Week 1) — Deterministic Generator Skeleton
### Goal
Prove determinism: **Prompt → working Godot project → headless run success**

### Scope & Deliverables
- CLI generator only (No UI or dashboard).
- Single planner agent & Single coder agent.
- Strict action schema v0.
- Template-based assets only (no AI asset generation).
- Godot headless validation command integration.
- Replay bundle saving.
- One baseline playable template success (2D Platformer).

### Acceptance Criteria
- [ ] Single command line execution reliably generates a runnable Godot project.
- [ ] Headless validation runs without crashing.
- [ ] 1 baseline template (2D Platformer) generates correctly without manual intervention.

---

## Phase 1 (Weeks 2–3) — Reliability Engine
### Goal
**Make generation stable before making it smart.** Focus entirely on the debugger loop and export.

### Scope & Deliverables
- Debugger agent loop (max 2 retries).
- Structured error classification from Godot logs to agent actions.
- Deterministic node naming enforced.
- Validation result schema defined.
- Prompt regression suite (10 prompts for the 3 MVP Archetypes).
- Run telemetry (track pass/fail and latency context).
- Export artifact builder (automatic Windows .exe packaging).

### Acceptance Criteria
- [ ] Failed generations correctly enter the debugger loop, automatically fix issues, and re-validate.
- [ ] Over 90% success on the 10-prompt regression suite using max 2 retries.
- [ ] Telemetry captures full RunState details.
- [ ] Final output is a standalone playable executable.

---

## Phase 2 (Weeks 4–5) — Agent Scaling + Asset Layer Lite
### Goal
**Improve capability without breaking reliability.**

### Scope & Deliverables
- Multi-agent orchestration scaling (Planner + Coder + Debugger).
- Simple sprite/texture generation only (NO 3D, NO Video, NO Audio generators yet).
- Asset normalization pipeline (force sizes/formats for Godot).
- Project chunking logic to support larger prompts without token exhaustion.
- Local model router integration (Ollama / OpenRouter fallback).
- Cost tracking per run (implementing the ~.85/run cost model).

### Acceptance Criteria
- [ ] Prompts reliably trigger 2D sprite generation and properly import into the game.
- [ ] Token and compute costs are logged to RunState, enforcing constraints.
- [ ] Multi-agent handoffs via RunState are stable (no freeform chatting).

---

## Phase 3 (Week 6+) — Native Editor Plugin (XClaw)
### Goal
**Move from batch generator to interactive system.** (Handled last because plugin UX hides reliability issues.)

### Scope & Deliverables
- Godot dock plugin UI.
- Selection-context extraction mechanism (feed selected node properties to prompt).
- Action diff preview logic.
- Undo grouping execution layer (EditorUndoRedoManager).
- Live apply mode.
- Bridge fallback stability.

### Acceptance Criteria
- [ ] Plugin runs cleanly in Godot Editor.
- [ ] AI updates apply instantly with Ctrl+Z rollback capabilities.
- [ ] Network failures fallback gracefully to file mode.

---

## Global Quality Gates (Applies to all Phases)
- **Schema gate:** All agent IO strict-validated.
- **Cost gate:** Total generation cost tracked and kept under constraints.
- **Validation gate:** Headless check required before considering a run successful.
- **Artifact gate:** Standalone executable MUST be generated as proof.
- **Logging gate:** Reproducible run logs saved to replay bundles.

