# QUALITY GATES & DEFINITION OF DONE
**Project:** Vibe Game Engine – Godot 4.6.1 Hybrid Edition  
**Owner:** Project Manager + Coordinator Agent  
**Version:** 1.0  
**Last Updated:** 2026-03-14

---

## 1) Purpose

This document defines the mandatory quality gates for all milestones, all agent runs, and all release builds.

A run can only be marked complete if it passes all applicable gates below.  
No exceptions.

---

## 2) Global Quality Principles

1. **Validation-first:** Nothing is “done” unless Godot headless validation passes.
2. **Schema-first:** All agent outputs must strictly validate against Pydantic v2 strict models.
3. **Reproducibility:** Every output must be replayable from prompt, plan, and patches.
4. **Fail closed:** If uncertain, run fails and escalates; it never silently “succeeds.”
5. **Traceability:** Every error must map to a source task, file, and owning agent.

---

## 3) Stage Gates (Pipeline)

## Gate A — Intake & Planning
**Entry criteria**
- User prompt received.
- Run ID created.
- Mode selected (`standalone`, `live_bridge`, `project_only`).

**Checks**
- Prompt stored in run workspace.
- Clarification asked if prompt is ambiguous (max 2 questions).
- `ProjectSpec` schema validates.
- Scope limits enforced (small/medium game constraints, multiplayer cap, timeline cap).

**Pass criteria**
- Approved `ProjectSpec`.
- Approved `TaskGraph`.
- Template selected.

**Fail conditions**
- Spec invalid or missing required fields.
- Unsafe or impossible scope without fallback.
- Clarification exhausted and still underspecified.

---

## Gate B — Code Generation
**Entry criteria**
- Planning gate passed.
- RAG context retrieved for Godot 4.6.1 APIs.

**Checks**
- All code output validates against `GodotFilePatch` schema.
- GDScript 2.0 syntax only.
- No TODOs, pseudo-code, placeholders, or fake APIs.
- Node paths deterministic and consistent with scene tree.
- File paths are valid and project-relative.

**Pass criteria**
- Patch set compiles structurally.
- Files generated in expected locations.

**Fail conditions**
- Schema violations.
- Unsupported APIs.
- Inconsistent node/resource paths.

---

## Gate C — Asset Generation & Import
**Entry criteria**
- Asset requests generated from approved plan.

**Checks**
- Asset metadata schema validates.
- Resolution/aspect/format meet spec.
- Naming conventions and folder taxonomy enforced.
- Import settings generated and valid.
- Vision-based semantic check meets threshold (where enabled).
- Fallback flow executes on timeout/OOM.

**Pass criteria**
- Assets imported and referenced by scenes/scripts.
- No missing resource references.

**Fail conditions**
- Broken imports.
- Semantic mismatch beyond threshold.
- Missing or corrupt files.

---

## Gate D — Validation Loop (Mandatory)
**Entry criteria**
- Code + assets integrated.

**Checks**
- Godot headless import run.
- Godot check-only/lint run.
- Headless smoke run (bounded time).
- Log parser produces structured `ValidationReport`.
- Debug loop retries max 3.

**Pass criteria**
- No fatal parse/runtime errors.
- Required gameplay loop reachable in smoke test.
- `ValidationReport.success == true`.

**Fail conditions**
- Fatal script/resource/runtime errors after max retries.
- Repeated identical failures (root-cause unresolved).
- Validation timeout beyond configured limits.

---

## Gate E — Export
**Entry criteria**
- Validation gate passed.

**Checks**
- Export preset exists and is valid.
- Templates available for target platform.
- Export command returns success.
- Output artifact generated at expected path.
- Artifact size and checksum recorded.

**Pass criteria**
- Playable artifact exists (`.exe`/`.zip`/`.apk` etc.).
- Export logs stored.
- `ExportResult.success == true`.

**Fail conditions**
- Missing preset/templates.
- Export command failure.
- Artifact missing/corrupt.

---

## Gate F — Packaging & Manifest
**Entry criteria**
- Export gate passed.

**Checks**
- `FinalManifest` generated with:
  - run_id
  - prompt
  - mode
  - files changed
  - assets generated
  - validation logs
  - export logs
  - checksums
- Replay bundle archived.

**Pass criteria**
- Manifest complete and schema-valid.
- Artifacts and logs linked.

**Fail conditions**
- Missing replay data.
- Incomplete manifest.

---

## Gate G — Release Readiness (Milestone/Launch)
**Entry criteria**
- Required run batches complete.

**Checks**
- Automated prompt suite pass rate meets SLO.
- Crash-free smoke test threshold met.
- Docs and runbook updated.
- Known limitations documented.
- License and attribution complete.

**Pass criteria**
- Release checklist 100% complete.
- Sign-off from PM + Tech Lead.

**Fail conditions**
- Any checklist blocker unresolved.
- SLO below target.

---

## 4) Retry & Escalation Policy

- Validation/debug retries: **max 3** per run.
- If 3 attempts fail:
  - Mark run `needs_human`.
  - Attach root-cause summary.
  - Preserve all logs and patches.
- No silent continuation after retry exhaustion.

---

## 5) Severity Model

- **S0 (Blocker):** Security issue, corrupted export, non-runnable build.
- **S1 (Critical):** Validation fails, hard crash, missing core gameplay loop.
- **S2 (Major):** Significant feature mismatch, severe asset inconsistency.
- **S3 (Minor):** Cosmetic defects, minor balancing issues.
- **S4 (Trivial):** Non-functional polish items.

**Rule:** S0/S1 block release. S2 requires explicit PM sign-off. S3/S4 can be deferred.

---

## 6) Definition of Done (Run-Level)

A run is marked `done` only if **all** are true:

1. Planning outputs are schema-valid.
2. Generated code/scene patches are schema-valid.
3. Assets imported with no missing references.
4. Headless validation passes.
5. Export succeeds for requested target(s).
6. Smoke test passes within time budget.
7. Final manifest is complete and valid.
8. Replay bundle saved (prompt, plan, patches, logs, checksums).
9. Task board and progress log updated.

If any item fails, status is not `done`.

---

## 7) Definition of Done (Milestone-Level)

A milestone is complete only if:

1. All milestone acceptance criteria are met.
2. All mandatory tests for that milestone pass.
3. No open S0/S1 issues.
4. Documentation updated for implemented features.
5. Rollback plan exists for new critical systems.
6. PM coordination docs updated (`MILESTONES.md`, `TASK_BOARD.md`, `PROGRESS_LOG.md`).

---

## 8) Required Artifacts Per Run

- `run_state.json`
- `project_spec.json`
- `task_graph.json`
- `patches/` (all file edits)
- `assets_manifest.json`
- `validation/` logs + `validation_report.json`
- `export/` logs + artifacts + checksums
- `final_manifest.json`
- `replay_bundle.zip`

Missing artifacts = gate failure.

---

## 9) Performance & Reliability Targets (SLOs)

- P50 generation time: **< 6 min**
- P95 generation time: **< 10 min**
- First-pass success: **>= 95%**
- Success within max 3 retries: **>= 99%**
- Bridge fallback success: **>= 99.5%**
- Crash-free 2-minute smoke run: **>= 98%**

If SLOs regress for 2 consecutive runs, open incident and freeze new feature merges.

---

## 10) Compliance Rules

- Never store secrets in logs/artifacts.
- Bridge token handled via secure local file/env only.
- Per-run isolated workspace required.
- Dependency allowlist enforced.
- Third-party assets must include license metadata.

---

## 11) Operational Checklist (Per Run)

- [ ] Run ID created
- [ ] Prompt captured and clarified
- [ ] Planning schemas valid
- [ ] Code patches schema-valid
- [ ] Assets generated/imported
- [ ] Headless validation pass
- [ ] Export pass
- [ ] Smoke test pass
- [ ] Manifest + replay bundle created
- [ ] PM logs updated

---

## 12) Change Control

Any modification to these gates requires:
1. ADR entry in `DECISIONS.md`
2. PM approval
3. Update to test harness and runbook
4. Version bump of this document

---

**Enforcement Statement:**  
These gates are mandatory for all agents, all modes, all milestones, and all releases.