# Vibe Game Engine – Task Board

**Project:** Godot 4.6.1 Hybrid Edition (Standalone Default + Live Editor Bridge)  
**Owner:** Project Manager Agent  
**Last Updated:** 2026-03-14  
**Status Legend:** `todo` | `in_progress` | `blocked` | `done`  
**Priority Legend:** `P0` Critical | `P1` High | `P2` Medium | `P3` Low

---

## Milestone Overview

| Milestone | Window | Goal | Status |
|---|---|---|---|
| M0 | Week 1 | Foundation setup + PM system + deterministic dev environment | `in_progress` |
| M1 | Weeks 1-2 | Core contracts + orchestration skeleton + validation/debug loop | `todo` |
| M2 | Weeks 2-3 | Asset generation/import pipeline + quality gates | `todo` |
| M3 | Weeks 3-4 | Export pipeline + bridge mode + fallback hardening | `todo` |
| M4 | Weeks 4-5 | Frontend dashboard + live progress + previews | `todo` |
| M5 | Weeks 5-6 | Test matrix, polish, release readiness, public launch | `todo` |

---

## Current Sprint (Active): M0 Foundation

### Sprint Goal
Create project management system and baseline implementation scaffolding to begin M1 without blockers.

### Tasks

| ID | Milestone | Task | Owner | Priority | Status | Dependencies | Acceptance Criteria |
|---|---|---|---|---|---|---|---|
| PM-001 | M0 | Create `PROJECT_MANAGEMENT` workspace | PM Agent | P0 | `done` | None | Directory exists |
| PM-002 | M0 | Create master planning docs (`MASTER_PLAN`, `MILESTONES`, `TASK_BOARD`, `QUALITY_GATES`, `PROGRESS_LOG`) | PM Agent | P0 | `in_progress` | PM-001 | All files created with initial content |
| ENG-001 | M0 | Initialize `godot/vibe-game-engine` scaffold folders | Coordinator Agent | P0 | `done` | None | Core directories exist |
| ENG-002 | M0 | Define strict Pydantic v2 contracts (`RunState`, `ExportRequest`, `ValidationReport`) | Coding Agent | P0 | `todo` | ENG-001 | Contracts compile and forbid extra keys |
| ENG-003 | M0 | Add orchestration state graph skeleton (LangGraph) | Coordinator Agent | P0 | `todo` | ENG-002 | Graph runs dry-run without execution errors |
| ENG-004 | M0 | Add deterministic validation shell script (`scripts/validate.sh`) | Debugger Agent | P0 | `todo` | ENG-001 | Script exits non-zero on fatal patterns |
| ENG-005 | M0 | Add retry loop coordinator (`max_retries=3`) | Coordinator Agent | P0 | `todo` | ENG-003, ENG-004 | Retry behavior tested with synthetic failures |
| ENG-006 | M0 | Create base Godot template (`base_2d_platformer`) | Coding Agent | P0 | `todo` | ENG-001 | Template opens + headless import works |
| QA-001 | M0 | Add smoke test harness for single prompt | QA Agent | P1 | `todo` | ENG-004, ENG-006 | Test produces pass/fail report |
| OPS-001 | M0 | Define Docker compose baseline services map | Ops Agent | P1 | `todo` | ENG-001 | Compose config spec documented |
| PM-003 | M0 | Lock Definition of Done for M0 | PM Agent | P0 | `todo` | PM-002 | DoD approved in `QUALITY_GATES.md` |

---

## Milestone M1 Backlog (Prepared)

| ID | Task | Owner | Priority | Status | Dependencies | Acceptance Criteria |
|---|---|---|---|---|---|---|
| ENG-101 | Implement `ProjectSpec` schema | Coding Agent | P0 | `todo` | ENG-002 | Strict validation + unit tests |
| ENG-102 | Implement `TaskGraph` schema | Coding Agent | P0 | `todo` | ENG-002 | Strict validation + unit tests |
| ENG-103 | Implement `GodotFilePatch` schema | Coding Agent | P0 | `todo` | ENG-002 | Supports create/edit operations |
| ENG-104 | Implement `ValidationNode` | Coordinator Agent | P0 | `todo` | ENG-003, ENG-004 | Produces structured `ValidationReport` |
| ENG-105 | Implement `DebugNode` root-cause patching | Debugger Agent | P0 | `todo` | ENG-104 | Fixes at least 70% seeded failures |
| ENG-106 | Integrate 3-retry loop with human checkpoint | Coordinator Agent | P0 | `todo` | ENG-105 | Correct branch after retries exhausted |
| QA-101 | 10 deterministic prompts benchmark | QA Agent | P0 | `todo` | ENG-106 | >=80% pass baseline |
| PM-101 | M1 review + sign-off | PM Agent | P0 | `todo` | All above | Milestone acceptance met |

---

## Blockers Register

| Blocker ID | Description | Affects | Owner | Status | Mitigation |
|---|---|---|---|---|---|
| B-001 | Export templates/version parity not yet verified in environment | M1+ | Ops Agent | `open` | Validate Godot 4.6.1 templates in container before M3 |
| B-002 | LLM routing fallback policy not implemented yet | M1+ | Coordinator Agent | `open` | Add LiteLLM policy in M1 |

---

## Decision Queue

| Decision ID | Topic | Needed By | Owner | Status |
|---|---|---|---|---|
| D-001 | Canonical workspace root for generated runs (`runs/<run_id>`) | M1 | PM Agent | `pending` |
| D-002 | Minimum smoke test duration per export target | M3 | QA Agent | `pending` |
| D-003 | Asset fallback library scope (starter pack size) | M2 | Asset Lead | `pending` |

---

## Daily Execution Cadence

1. Pull top `P0` items in current milestone.
2. Move task to `in_progress`.
3. Implement + validate against acceptance criteria.
4. Mark `done` only with evidence in `PROGRESS_LOG.md`.
5. Recompute blockers and dependencies.
6. Do not start next milestone until current milestone DoD is met.

---

## Definition of Done (Task-Level)

A task is `done` only if:
- Implementation exists in repository.
- Validation/test evidence recorded.
- No unresolved critical errors linked to task.
- Related docs updated (if applicable).

---

## Immediate Next 5 Tasks (Execution Order)

1. `PM-002` – Finish all PM tracker files (`in_progress`)
2. `ENG-002` – Write strict contracts (`todo`)
3. `ENG-004` – Add validation script (`todo`)
4. `ENG-003` – Add orchestration skeleton (`todo`)
5. `ENG-006` – Add base 2D template (`todo`)