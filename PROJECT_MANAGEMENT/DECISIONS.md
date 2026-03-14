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