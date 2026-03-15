# Architecture Decisions Log (ADR)

Project: **Vibe Game Engine – Godot 4.6.1 Hybrid Edition**  
Owner: **Project Manager / Coordinator System**  
Status: **Active**  
Last Updated: **2026-03-14**

---

## How to Use This File

- Record one decision per ADR entry.
- Never delete old decisions; supersede them with a new ADR.
- Each ADR includes:
  - Context
  - Decision
  - Consequences
  - Status
  - Date
  - Owner

---

## ADR-001 — Hybrid Execution Model (Standalone Default + Live Bridge Optional)

**Date:** 2026-03-14  
**Status:** Accepted  
**Owner:** Architecture Lead

### Context
We need reliable game generation in under 10 minutes with high first-pass success, while still supporting iterative editing inside a running Godot Editor.

### Decision
Adopt a **hybrid model**:
1. **Default**: file-based standalone pipeline (generate project → validate headless → export).
2. **Optional**: live editor integration through bridge RPC when available.
3. Always support automatic fallback from live mode to file mode.

### Consequences
- Reliability improves because standalone path remains canonical.
- Live editing is available without blocking core delivery.
- Additional complexity in mode switching and state consistency.

---

## ADR-002 — Orchestration Framework

**Date:** 2026-03-14  
**Status:** Accepted  
**Owner:** Platform Lead

### Context
System requires deterministic multi-agent coordination with retries, branch conditions, and persistent run state.

### Decision
Use **LangGraph-style stateful orchestration** with role-specialized agents (Project Manager, Coordinator, Coding, Debugger, Asset roles, Exporter).

### Consequences
- Clear graph transitions and retry loops.
- Better observability and replayability.
- Requires strict state contracts to prevent drift.

---

## ADR-003 — Strict Schema-First Agent Contracts

**Date:** 2026-03-14  
**Status:** Accepted  
**Owner:** Reliability Lead

### Context
Model outputs can hallucinate and break automation if free-form text is accepted.

### Decision
All inter-agent artifacts must be validated through **Pydantic v2 strict models** (`extra=forbid`, strict types). Invalid output triggers automatic regeneration or fail-fast.

### Consequences
- Strong reduction in malformed outputs.
- Slight increase in development overhead.
- Easier debugging and deterministic failure handling.

---

## ADR-004 — Anti-Hallucination Guardrails

**Date:** 2026-03-14  
**Status:** Accepted  
**Owner:** AI Systems Lead

### Context
Need near-production reliability for Godot code/scenes from natural language.

### Decision
Enforce a combined guardrail stack:
1. RAG over Godot 4.6.1 docs.
2. Few-shot known-good snippets.
3. Strict output schemas.
4. Headless validation + debugger retry loop (max 3).
5. Vision-based asset checks for semantic mismatch.

### Consequences
- Higher first-pass success.
- Additional compute and implementation complexity.
- Better root-cause traceability.

---

## ADR-005 — Validation Gate as Single Source of Truth for “Done”

**Date:** 2026-03-14  
**Status:** Accepted  
**Owner:** QA Lead

### Context
Agent confidence is not sufficient to guarantee runtime correctness.

### Decision
A run can only be marked **Done** if:
1. Headless validation passes.
2. Export artifact exists and integrity checks pass.
3. Smoke run passes.
4. Final manifest is generated.

### Consequences
- Prevents false positives.
- May increase average completion time slightly.
- Greatly improves production trust.

---

## ADR-006 — Retry Policy (Max 3 Automated Attempts)

**Date:** 2026-03-14  
**Status:** Accepted  
**Owner:** Reliability Lead

### Context
Unlimited retries waste resources and can loop indefinitely.

### Decision
Set a strict retry budget:
- Validation/Debug loop: max 3 cycles.
- If unresolved after 3, status moves to `needs_human`.

### Consequences
- Predictable runtime and cost.
- Clear escalation path.
- Some edge cases require manual intervention.

---

## ADR-007 — Godot Runtime and Export Standardization

**Date:** 2026-03-14  
**Status:** Accepted  
**Owner:** DevOps Lead

### Context
Local environment differences cause inconsistent build behavior.

### Decision
Standardize around containerized Godot headless execution and pinned engine/export-template versions (Godot 4.6.1).

### Consequences
- Reproducible validation/export results.
- Easier CI parity with local runs.
- Need to maintain container images and template cache.

---

## ADR-008 — Asset Generation Fallback Strategy

**Date:** 2026-03-14  
**Status:** Accepted  
**Owner:** Content Pipeline Lead

### Context
Generative asset services can fail due to memory/timeouts or style drift.

### Decision
Implement fallback chain:
1. Primary generation at target quality.
2. Retry with lower complexity/resolution.
3. If still failing, use template-safe placeholder asset and continue pipeline.

### Consequences
- Pipeline rarely blocks on assets.
- Visual quality may degrade in fallback mode.
- Must flag fallback use in final manifest.

---

## ADR-009 — Multiplayer Scope Limit for MVP

**Date:** 2026-03-14  
**Status:** Accepted  
**Owner:** Product Lead

### Context
Networking complexity can derail 6-week timeline.

### Decision
Cap multiplayer to **“lite” up to 4 players** using Godot high-level networking for MVP.

### Consequences
- Scope remains deliverable.
- Limits large-scale multiplayer expectations.
- Clear roadmap item for post-MVP scaling.

---

## ADR-010 — Repository Structure for Delivery

**Date:** 2026-03-14  
**Status:** Accepted  
**Owner:** PM / Tech Lead

### Context
Need clear ownership boundaries between orchestration, agents, contracts, tooling, templates, and frontend.

### Decision
Adopt structure:
- `PROJECT_MANAGEMENT/` for governance and planning
- `vibe-game-engine/contracts/`
- `vibe-game-engine/agents/`
- `vibe-game-engine/orchestration/`
- `vibe-game-engine/tools/`
- `vibe-game-engine/templates/`
- `vibe-game-engine/scripts/`
- `vibe-game-engine/tests/`

### Consequences
- Faster onboarding and execution tracking.
- Enables milestone-based implementation.
- Requires discipline to keep boundaries clean.

---

## ADR-011 — Metrics and SLO Baseline

**Date:** 2026-03-14  
**Status:** Accepted  
**Owner:** Observability Lead

### Context
Success claims need measurable targets and historical trends.

### Decision
Track and report:
- P50 and P95 generation time
- First-pass success rate
- Retry distribution
- Export success rate
- Bridge fallback rate
- Crash-free smoke-test rate

### Consequences
- Data-driven iteration.
- Additional telemetry plumbing required.
- Better release readiness decisions.

---

## ADR-012 — Security Baseline for Local/Cloud Operation

**Date:** 2026-03-14  
**Status:** Accepted  
**Owner:** Security Lead

### Context
Pipeline handles tokens, generated files, and potentially user-uploaded assets.

### Decision
Apply minimum controls:
- No secret/token logging.
- Per-run sandbox workspace.
- File size and runtime quotas.
- Dependency allowlist.
- Artifact checksums in final manifest.

### Consequences
- Reduced risk surface.
- Slight operational overhead.
- Required for safe public launch.

---

## ADR-013 — Temporary Runtime Fallback for Headless Validation/Export

**Date:** 2026-03-14  
**Status:** Accepted (Temporary)  
**Owner:** DevOps Lead

### Context
Current local environment lacks a direct Godot 4.6.1 CLI/runtime image, which blocks immediate headless validation and export execution evidence.

### Decision
Use Docker image `barichello/godot-ci:4.5.1` as a temporary fallback for:
1. Headless import/check/smoke validation.
2. Windows export command execution.

Preserve the requirement to rerun all critical evidence once a 4.6.1-compatible runtime is available.

### Consequences
- Unblocks milestone execution and evidence collection.
- Introduces version-parity risk against target 4.6.1 behavior.
- Requires follow-up parity verification before release sign-off.

### Supersedes
- Superseded by ADR-014 once 4.6.1 runtime parity is established.

---

## ADR-014 — Runtime Parity Pin on Godot 4.6.1

**Date:** 2026-03-14  
**Status:** Accepted  
**Owner:** DevOps Lead

### Context
Project target requires Godot 4.6.1 parity for headless validation and export evidence.

### Decision
Pin runtime verification to Docker image `barichello/godot-ci:4.6.1` and treat it as the baseline parity runtime for M2/M3 checks until a native local 4.6.1 CLI is provisioned.

### Consequences
- Validation and export evidence now align with target runtime major/minor/patch.
- Removes version-parity blocker B-003.
- Keeps local execution reproducible through pinned container runtime.

---

## ADR-015 — Needs-Human Escalation Artifacts + Benchmark Trend Baseline

**Date:** 2026-03-14  
**Status:** Accepted  
**Owner:** PM + Reliability Lead

### Context
Runs that exhaust retries need deterministic handoff to human operators, and benchmark health requires historical trend evidence instead of one-off pass/fail snapshots.

### Decision
1. On `needs_human`, auto-generate escalation ticket artifacts:
  - `runs/<run_id>/.vibe/escalation/needs_human_ticket.json`
  - queue append in `runs/needs_human_queue.jsonl`
2. Expand deterministic benchmark corpus to versioned file:
  - `vibe-game-engine/benchmarks/prompt_corpus_v1.txt`
3. Persist benchmark outputs each run:
  - `vibe-game-engine/benchmarks/results/latest.json`
  - `vibe-game-engine/benchmarks/results/history.jsonl`
4. Enforce deterministic checks in CI workflow for tests + smoke + benchmark.

### Consequences
- Human escalation becomes auditable and queue-driven.
- Reliability trends are measurable over time.
- CI catches regressions before merge with consistent validation commands.

---

## ADR-016 — Operational Policy Lock for D-001, D-002, D-003

**Date:** 2026-03-15  
**Status:** Accepted  
**Owner:** PM + QA Lead

### Context
Decision queue items D-001/D-002/D-003 were pending and blocking downstream implementation consistency for run paths, smoke thresholds, and asset fallback capacity.

### Decision
Lock machine-readable operational policies in:
- `vibe-game-engine/config/operational_policies.json`

Policy values:
1. `D-001`: Canonical run workspace root is `runs/<run_id>`.
2. `D-002`: Minimum smoke durations are target-specific (Windows/Linux: 120s, Web/Android: 90s).
3. `D-003`: Starter fallback asset library scope is capped at 32 total assets with explicit category and format constraints.

### Consequences
- All automation now references one source for these policy values.
- Reduces drift between docs, scripts, and validation behavior.
- Enables deterministic gate scripts to enforce policy directly.

---

## ADR-017 — Central Dashboard Command Center Architecture

**Date:** 2026-03-15  
**Status:** Accepted  
**Owner:** Platform + Frontend Leads

### Context
Operational visibility and control were CLI-fragmented, reducing real-time awareness of agent activity and slowing routine command execution.

### Decision
Implement local command-center architecture:
1. Backend API server: `vibe-game-engine/scripts/dashboard_server.py`.
2. Web UI: `vibe-game-engine/dashboard/` static app.
3. Whitelisted command execution from UI (tests, smoke, benchmark, asset gate, escalation triage).
4. Telemetry polling for KPI cards, agent state panel, recent runs, and command job history.

### Consequences
- Operators can launch and monitor core workflows from a single interface.
- Improves observability without introducing external infrastructure dependencies.
- Keeps command execution constrained to an explicit allowlist for safety.

---

## ADR-018 — Dashboard Frontend Stack Migration to Next.js + Tailwind

**Date:** 2026-03-15  
**Status:** Accepted  
**Owner:** Frontend + Platform Leads

### Context
Operator preference requires a Next.js-based dashboard with TailwindCSS instead of the prior static HTML/CSS/JS implementation.

### Decision
Implement dashboard UI and API layer in:
- `vibe-game-engine/dashboard-nextjs/`

Use stack:
1. Next.js App Router
2. TailwindCSS styling
3. API routes for overview, jobs, commands, and command execution

Add compatibility launcher at:
- `scripts/dashboard_server.py`

### Consequences
- Dashboard development now uses modern React/Next patterns.
- Command center remains local-first with the same allowlisted operational commands.
- Prior static dashboard remains in repo history but is superseded operationally.

---

## ADR Template (for new entries)

```text
## ADR-XXX — Title

Date: YYYY-MM-DD
Status: Proposed | Accepted | Superseded | Rejected
Owner: <role/person>

### Context
<why this decision is needed>

### Decision
<what was decided>

### Consequences
<positive/negative trade-offs>

### Supersedes
<optional: ADR-YYY>
```

---

## Change Log

- **2026-03-14**: Initial ADR set created (ADR-001 to ADR-012).