# Risk Register — Vibe Game Engine (Godot 4.6.1 Hybrid Edition)

## Purpose
This register tracks delivery, technical, product, and operational risks for the Vibe Game Engine project and defines clear ownership, mitigation, and contingency actions.

## Scoring Model
- **Probability (P):** 1 (Low) → 5 (Very High)
- **Impact (I):** 1 (Low) → 5 (Critical)
- **Risk Score:** `P × I`
- **Priority:**
  - **Critical:** 16–25
  - **High:** 10–15
  - **Medium:** 6–9
  - **Low:** 1–5

## Status Values
- `open` — active, requires monitoring/mitigation
- `watch` — currently stable, monitor trigger signals
- `mitigated` — controls are in place and effective
- `realized` — risk occurred, contingency in action
- `closed` — no longer relevant

---

## Top Risks (Executive View)

| ID | Risk | Score | Priority | Owner | Status |
|---|---|---:|---|---|---|
| R-001 | First-pass generation success drops below 95% | 20 | Critical | AI Lead | open |
| R-002 | Headless validation unreliable across environments | 16 | Critical | Platform Lead | open |
| R-003 | Godot bridge disconnect or protocol drift | 15 | High | Integrations Lead | open |
| R-004 | Export templates mismatch/missing at runtime | 12 | High | DevOps Lead | open |
| R-005 | LLM hallucinations produce invalid Godot artifacts | 20 | Critical | AI Lead | open |
| R-006 | Asset generation latency exceeds <10 min target | 15 | High | ML Infra Lead | open |
| R-007 | Scope creep beyond 6-week delivery window | 16 | Critical | Project Manager | open |
| R-008 | Regression rate rises due to weak test matrix | 12 | High | QA Lead | open |

---

## Detailed Risk Register

### R-001 — First-pass success rate < 95%
- **Category:** Product / Reliability
- **Description:** End-to-end runs fail first try more often than target.
- **P/I/Score:** 4 / 5 / 20
- **Triggers:**
  - Rolling first-pass success < 92% over 3 days
  - > 15% of runs require manual checkpoint
- **Mitigations:**
  - Enforce strict Pydantic schemas on all agent outputs
  - RAG retrieval before every coding action
  - Deterministic templates and retry loop (max 3)
  - Prompt test harness (50+ prompts) in CI
- **Contingency:**
  - Freeze feature work
  - Run incident sprint focused on top 10 failure signatures
- **Owner:** AI Lead
- **Status:** open

### R-002 — Headless validation instability
- **Category:** Platform / CI
- **Description:** Validation behaves differently between local, container, and CI environments.
- **P/I/Score:** 4 / 4 / 16
- **Triggers:**
  - Inconsistent pass/fail on same commit
  - Frequent import/cache-related failures
- **Mitigations:**
  - Single pinned Docker image for validation/export
  - Clean workspace per run (`runs/<run_id>`)
  - Structured log parser and known-fatal pattern checks
- **Contingency:**
  - Route all validation through canonical container only
  - Disable non-deterministic checks temporarily
- **Owner:** Platform Lead
- **Status:** open

### R-003 — Live bridge disconnect / protocol changes
- **Category:** Integration
- **Description:** WebSocket bridge disconnects or behavior changes break live mode.
- **P/I/Score:** 3 / 5 / 15
- **Triggers:**
  - Heartbeat failures > 2 consecutive attempts
  - RPC timeout > 5s repeatedly
- **Mitigations:**
  - Heartbeat + reconnect + idempotent RPC wrappers
  - Auto-fallback to file mode
  - Keep file mode as source of truth
- **Contingency:**
  - Temporarily disable live mode in UI
  - Continue standalone pipeline without interruption
- **Owner:** Integrations Lead
- **Status:** open

### R-004 — Export templates unavailable/misconfigured
- **Category:** Build / Release
- **Description:** Missing or mismatched export templates block executable generation.
- **P/I/Score:** 3 / 4 / 12
- **Triggers:**
  - Export command errors for template resolution
  - Platform-specific export failures spike
- **Mitigations:**
  - Pre-bundle templates in container
  - Startup health check for template availability
  - Version-pinned `export_presets.cfg`
- **Contingency:**
  - Auto-download on first run with checksum verification
  - Skip failing platform and ship available artifacts with warning
- **Owner:** DevOps Lead
- **Status:** open

### R-005 — Model hallucination (invalid `.gd`/`.tscn`)
- **Category:** AI Quality
- **Description:** Generated code/scenes violate Godot 4.6.1 syntax or semantics.
- **P/I/Score:** 4 / 5 / 20
- **Triggers:**
  - Parse errors in headless logs
  - Rising rate of schema validation failures
- **Mitigations:**
  - Strict schema-first output with `extra=forbid`
  - Godot docs RAG chunks attached to each coding request
  - Few-shot with known-good snippets
  - Debugger root-cause patching (not broad rewrites)
- **Contingency:**
  - Escalate to human checkpoint after max retries
  - Add failure signature to permanent regression suite
- **Owner:** AI Lead
- **Status:** open

### R-006 — Generation time exceeds 10-minute goal
- **Category:** Performance / UX
- **Description:** End-to-end execution misses P95 < 10 min objective.
- **P/I/Score:** 3 / 5 / 15
- **Triggers:**
  - P95 > 12 min for 48h
  - Queue depth for model workers > threshold
- **Mitigations:**
  - Parallelize code/asset branches
  - Use lower-complexity fallback assets after timeout
  - Cache reusable templates/assets
  - Budget caps per run
- **Contingency:**
  - Graceful “fast mode” toggle
  - Defer non-essential assets post-export
- **Owner:** ML Infra Lead
- **Status:** open

### R-007 — Scope creep jeopardizes 6-week schedule
- **Category:** Delivery / Governance
- **Description:** Adding non-MVP features delays launch.
- **P/I/Score:** 4 / 4 / 16
- **Triggers:**
  - Milestones slipping > 3 business days
  - New feature requests without de-scoping
- **Mitigations:**
  - Milestone gate reviews and change control
  - Strict MVP definition and DoD
  - Backlog triage twice weekly
- **Contingency:**
  - Lock scope to must-have list
  - Move extras to post-MVP roadmap (Weeks 7–12)
- **Owner:** Project Manager
- **Status:** open

### R-008 — Insufficient test coverage/regression leaks
- **Category:** QA
- **Description:** New changes break existing use cases undetected.
- **P/I/Score:** 3 / 4 / 12
- **Triggers:**
  - Reopened bugs increase week-over-week
  - Flaky CI test outcomes
- **Mitigations:**
  - 50-prompt matrix across core game types
  - Deterministic smoke tests on exported artifacts
  - Failure signature replay bundles
- **Contingency:**
  - Release freeze until critical tests stabilize
  - Add mandatory pre-merge validation suite
- **Owner:** QA Lead
- **Status:** open

### R-009 — Dependency/version drift (Godot, models, bridge)
- **Category:** Configuration Management
- **Description:** Upstream updates cause incompatibility with pinned stack.
- **P/I/Score:** 3 / 4 / 12
- **Triggers:**
  - Build break after dependency update
  - Behavior change in bridge/API responses
- **Mitigations:**
  - Pin image tags and package versions
  - Weekly compatibility checks in branch
  - Controlled upgrade policy
- **Contingency:**
  - Roll back to last known-good lockfile/image
  - Patch adapter layer
- **Owner:** Platform Lead
- **Status:** watch

### R-010 — Asset licensing/compliance issues
- **Category:** Legal / Compliance
- **Description:** Generated or bundled assets violate licensing constraints.
- **P/I/Score:** 2 / 5 / 10
- **Triggers:**
  - Unknown provenance assets in build
  - Missing attribution metadata
- **Mitigations:**
  - License policy and allowlist
  - Manifest includes provenance and generator metadata
  - Exclude external unverified assets by default
- **Contingency:**
  - Remove offending assets and rebuild with placeholders
  - Publish compliance patch release
- **Owner:** Product + Legal
- **Status:** open

### R-011 — Security exposure (tokens, prompts, artifacts)
- **Category:** Security
- **Description:** Sensitive tokens or user data leak through logs/artifacts.
- **P/I/Score:** 2 / 5 / 10
- **Triggers:**
  - Token-like strings detected in logs
  - Unauthorized artifact access
- **Mitigations:**
  - Secret redaction in logs
  - Scoped tokens and local-only defaults
  - Per-run sandbox and retention policy
- **Contingency:**
  - Revoke tokens immediately
  - Incident response and audit
- **Owner:** Security Lead
- **Status:** open

### R-012 — Multiplayer-lite desync complexity underestimated
- **Category:** Technical Scope
- **Description:** Networking edge cases consume disproportionate time.
- **P/I/Score:** 3 / 3 / 9
- **Triggers:**
  - Repeated sync bugs beyond cap
  - Frequent rollback to single-player
- **Mitigations:**
  - Cap at 4 players
  - Restrict supported net patterns in MVP
  - Add explicit warning in planner output
- **Contingency:**
  - Mark multiplayer as experimental in MVP
  - Move advanced sync to post-MVP
- **Owner:** Gameplay Lead
- **Status:** watch

---

## Risk Burndown Targets
- Week 2: All **Critical** risks have active mitigations implemented.
- Week 4: No **open** risk with score > 16 without contingency tested.
- Week 6: All launch-blocking risks set to `mitigated` or accepted with documented waiver.

---

## Cadence
- **Daily:** quick risk scan in standup (new triggers only)
- **Twice weekly:** full risk review with owners
- **Milestone gate:** mandatory risk sign-off before advancing

---

## Change Log
- **2026-03-14:** Initial register created for v1.0 production plan.