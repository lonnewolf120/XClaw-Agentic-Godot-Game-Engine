# Vibe Game Engine – Task Board

**Project:** Godot 4.6.1 Hybrid Edition (Standalone Default + Live Editor Bridge)  
**Owner:** Project Manager Agent  
**Last Updated:** 2026-03-15  
**Status Legend:** `todo` | `in_progress` | `blocked` | `done`  
**Priority Legend:** `P0` Critical | `P1` High | `P2` Medium | `P3` Low

---

## Milestone Overview

| Milestone | Window | Goal | Status |
|---|---|---|---|
| M0 | Week 1 | Foundation setup + PM system + deterministic dev environment | `in_progress` |
| M1 | Weeks 1-2 | Core contracts + orchestration skeleton + validation/debug loop | `done` |
| M2 | Weeks 2-3 | Asset generation/import pipeline + quality gates | `in_progress` |
| M3 | Weeks 3-4 | Export pipeline + bridge mode + fallback hardening | `in_progress` |
| M4 | Weeks 4-5 | Frontend dashboard + live progress + previews | `in_progress` |
| M5 | Weeks 5-6 | Test matrix, polish, release readiness, public launch | `todo` |

---

## Current Sprint (Active): M2/M3 PoC Stabilization (Reality-Based)

### Sprint Goal
Close the real PoC gap by making imported templates exportable, enforcing runtime-grade validation in-pipeline, and proving repeatable strict-export success on a small benchmark slice.

### Tasks

| ID | Milestone | Task | Owner | Priority | Status | Dependencies | Acceptance Criteria |
|---|---|---|---|---|---|---|---|
| PM-001 | M0 | Create `PROJECT_MANAGEMENT` workspace | PM Agent | P0 | `done` | None | Directory exists |
| PM-002 | M0 | Create master planning docs (`MASTER_PLAN`, `MILESTONES`, `TASK_BOARD`, `QUALITY_GATES`, `PROGRESS_LOG`) | PM Agent | P0 | `in_progress` | PM-001 | All files created with initial content |
| ENG-001 | M0 | Initialize `vibe-game-engine` scaffold folders | Coordinator Agent | P0 | `done` | None | Core directories exist |
| ENG-002 | M0 | Define strict Pydantic v2 contracts (`RunState`, `ExportRequest`, `ValidationReport`) | Coding Agent | P0 | `done` | ENG-001 | Contracts compile and forbid extra keys |
| ENG-003 | M0 | Add orchestration state graph skeleton (LangGraph) | Coordinator Agent | P0 | `done` | ENG-002 | Graph runs dry-run without execution errors |
| ENG-004 | M0 | Add deterministic validation shell script (`scripts/validate.sh`) | Debugger Agent | P0 | `done` | ENG-001 | Script exits non-zero on fatal patterns |
| ENG-005 | M0 | Add retry loop coordinator (`max_retries=3`) | Coordinator Agent | P0 | `done` | ENG-003, ENG-004 | Retry behavior tested with synthetic failures |
| ENG-006 | M0 | Create base Godot template (`base_2d_platformer`) | Coding Agent | P0 | `done` | ENG-001 | Template opens + headless import works |
| QA-001 | M0 | Add smoke test harness for single prompt | QA Agent | P1 | `done` | ENG-004, ENG-006 | Test produces pass/fail report |
| ENG-201 | M2 | Scaffold base template files for export | Coding Agent | P0 | `done` | ENG-006 | Minimal Godot project files exist |
| ENG-202 | M2 | Create exporter agent stub | Coding Agent | P0 | `done` | ENG-201 | Export interface defined |
| ENG-203 | M2 | Execute template export and artifact smoke | Coding Agent | P0 | `done` | ENG-202 | ExportResult includes artifact + checksum |
| ENG-301 | M3 | Scaffold core agent stubs (PM/Coordinator/Coding/Debugger) | Coding Agent | P0 | `done` | ENG-202 | Interfaces defined |
| ENG-302 | M3 | Implement deterministic agent core methods | Coding Agent | P0 | `done` | ENG-301 | PM/Coordinator/Coding/Debugger execute without NotImplemented |
| OPS-001 | M0 | Define Docker compose baseline services map | Ops Agent | P1 | `done` | ENG-001 | Compose config spec documented |
| PM-003 | M0 | Lock Definition of Done for M0 | PM Agent | P0 | `done` | PM-002 | DoD approved in `QUALITY_GATES.md` |
| ENG-303 | M3 | Integrate agent prompt templates into runtime invocation | Coding Agent | P0 | `done` | ENG-302 | Runtime path loads and uses prompt templates |
| QA-102 | M3 | Export smoke test at 2-minute stability threshold | QA Agent | P0 | `done` | ENG-203 | Exported artifact remains alive for 2 minutes |
| OPS-002 | M3 | Add deterministic CI validation workflow | Ops Agent | P0 | `done` | ENG-303 | CI runs tests + smoke + benchmark on Python 3.10/3.12 |
| QA-103 | M3 | Expand benchmark corpus and trend reporting | QA Agent | P0 | `done` | QA-101 | >=20 prompts tracked with history output |
| ENG-304 | M3 | Assert manifest integrity after successful export | Coding Agent | P0 | `done` | ENG-203 | Automated test validates manifest checksums/log linkage |
| M2-104 | M2 | Implement deterministic asset quality gate tooling | QA Agent | P0 | `done` | QA-103 | Asset gate command returns structured pass/fail output |
| M3-104 | M3 | Automate needs-human queue triage summary | Ops Agent | P0 | `done` | ENG-304 | Triage summary generated from queue in deterministic categories |
| M4-001 | M4 | Build central dashboard command center UI | Frontend Agent | P0 | `done` | ENG-303 | UI shows KPIs, agent states, run timeline, and command controls |
| M4-002 | M4 | Add dashboard backend API + command runner | Platform Agent | P0 | `done` | M4-001 | Local server serves overview + command/job APIs |
| ENG-305 | M3 | Implement game creation pipeline entrypoint | Coding Agent | P0 | `done` | ENG-303 | Prompt-to-project flow creates run workspace, applies patches, validates structure, and persists run bundle |
| ENG-306 | M3 | Add optional export+manifest to game creation pipeline | Coding Agent | P0 | `done` | ENG-305 | Pipeline can optionally export artifact, generate final manifest, and support strict export failure mode |
| M4-006 | M4 | Add real-time game runtime control + timeline panels | Frontend Agent | P0 | `done` | M4-002, ENG-305 | Engine page supports launch/relaunch/cancel controls and structured live execution timeline for create-game jobs |

---

## Milestone M1 Backlog (Prepared)

| ID | Task | Owner | Priority | Status | Dependencies | Acceptance Criteria |
|---|---|---|---|---|---|---|
| ENG-101 | Implement `ProjectSpec` schema | Coding Agent | P0 | `done` | ENG-002 | Strict validation + unit tests |
| ENG-102 | Implement `TaskGraph` schema | Coding Agent | P0 | `done` | ENG-002 | Strict validation + unit tests |
| ENG-103 | Implement `GodotFilePatch` schema | Coding Agent | P0 | `done` | ENG-002 | Supports create/edit operations |
| ENG-104 | Implement `ValidationNode` | Coordinator Agent | P0 | `done` | ENG-003, ENG-004 | Produces structured `ValidationReport` |
| ENG-105 | Implement `DebugNode` root-cause patching | Debugger Agent | P0 | `done` | ENG-104 | Fixes at least 70% seeded failures |
| ENG-106 | Integrate 3-retry loop with human checkpoint | Coordinator Agent | P0 | `done` | ENG-105 | Correct branch after retries exhausted |
| QA-101 | 10 deterministic prompts benchmark | QA Agent | P0 | `done` | ENG-106 | >=80% pass baseline |
| PM-101 | M1 review + sign-off | PM Agent | P0 | `done` | All above | Milestone acceptance met |

---

## Blockers Register

| Blocker ID | Description | Affects | Owner | Status | Mitigation |
|---|---|---|---|---|---|
| B-001 | Export templates/version parity not yet verified in environment | M1+ | Ops Agent | `open` | Validate Godot 4.6.1 templates in container before M3 |
| B-002 | LLM routing fallback policy not implemented yet | M1+ | Coordinator Agent | `closed` | Added deterministic `needs_human` escalation policy with auto-ticket queue artifacts |
| B-003 | Local runtime lacks pinned Godot 4.6.1 CLI/image; fallback used 4.5.1 for validation/export evidence | M2+ | Ops Agent | `closed` | Pulled `barichello/godot-ci:4.6.1` and reran validation/export parity checks |
| B-004 | Imported Kenney templates fail strict export due missing `export_presets.cfg` in generated project root | M2/M3 | Coding Agent | `open` | Auto-bootstrap export presets pre-export and verify with strict-export matrix |

---

## Decision Queue

| Decision ID | Topic | Needed By | Owner | Status |
|---|---|---|---|---|
| D-001 | Canonical workspace root for generated runs (`runs/<run_id>`) | M1 | PM Agent | `done` |
| D-002 | Minimum smoke test duration per export target | M3 | QA Agent | `done` |
| D-003 | Asset fallback library scope (starter pack size) | M2 | Asset Lead | `done` |

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

1. `POC-001` – Inject/fallback `export_presets.cfg` for imported templates before export (`todo`)
2. `POC-002` – Add pipeline Gate D runtime check node (headless import/check/smoke) and fail closed (`todo`)
3. `POC-003` – Run strict-export matrix for 3 Kenney templates + 1 internal control and publish pass-rate (`todo`)
4. `POC-004` – Add regression test coverage for missing-presets and runtime-gate failure paths (`todo`)
5. `POC-005` – Update quality-gate evidence reporting to include real runtime log paths in run bundle (`todo`)

---

## Action Sprint (Next 5 Days)

| ID | Task | Owner | Priority | Status | Acceptance Criteria |
|---|---|---|---|---|---|
| POC-001 | Auto-bootstrap export presets when absent in selected template copy | Coding Agent | `P0` | `todo` | Strict export no longer fails with "missing export_presets.cfg" on Racing/City/FPS templates |
| POC-002 | Enforce real Gate D in `game_creation` via Docker Godot headless commands | Coding Agent | `P0` | `todo` | Run marked `failed` when import/check/smoke fails; run marked `completed` only when Gate D + E pass |
| POC-003 | Execute 4-run strict-export proof set and record outcomes in `PROGRESS_LOG.md` | QA Agent | `P0` | `todo` | >=3/4 strict-export passes including at least 2 Kenney templates |
| POC-004 | Add deterministic tests for preset bootstrap + validation gate integration | QA Agent | `P1` | `todo` | New tests pass locally and in CI with no flakiness |
| POC-005 | Re-baseline benchmark target from "moonshot" to practical PoC threshold | PM Agent | `P1` | `todo` | Documented threshold and signed gate in quality docs with explicit pass/fail rules |

---

## Reference Adoption Sprint (vibesdk + bolt.diy)

| ID | Milestone | Task | Owner | Priority | Status | Dependencies | Acceptance Criteria |
|---|---|---|---|---|---|---|---|
| REF-001 | M4 | Create reference reuse register and attribution checklist | PM Agent | P0 | `todo` | None | `REFERENCE_ADOPTION_PLAN_VIBESDK_BOLT.md` mapped to source patterns and license obligations |
| REF-002 | M3/M4 | Add deterministic phase event contract (`phase_started/progress/completed/failed`) | Platform Agent | P0 | `todo` | REF-001 | All run phases emit structured events with `run_id`, `phase`, `timestamp`, `log_path` |
| REF-003 | M3 | Harden Gate D/E transitions to fail closed only | Coding Agent | P0 | `todo` | POC-001, POC-002 | No run can transition to `completed` unless Gate D + Gate E pass |
| REF-004 | M4 | Wire studio page to real run APIs, preview URL, live logs, and artifacts | Frontend Agent | P0 | `todo` | REF-002, REF-003 | Dashboard can launch, monitor, replay, and download run artifacts end-to-end |
| REF-005 | M4 | Implement preview refresh channel (`preview_ready`, `refresh_preview`, `file_change`) | Platform Agent | P1 | `todo` | REF-004 | Preview updates without manual reload during iterative run flow |
| REF-006 | M5 | Add quality belt jobs for dashboard (lint/type/build/a11y/perf/benchmark-subset) | Ops Agent | P1 | `todo` | REF-004 | CI publishes quality artifacts and blocks regressions on major changes |
| REF-007 | M5 | Run CLI-dashboard parity benchmark and publish failure taxonomy report | QA Agent | P0 | `todo` | REF-004, REF-006 | Report includes pass rates, retry rates, failure classes, and owners |

---

## Game Dev Haven Sprint (Creator-First)

| ID | Milestone | Task | Owner | Priority | Status | Dependencies | Acceptance Criteria |
|---|---|---|---|---|---|---|---|
| HAVEN-001 | M4 | Upgrade studio to full workbench (preview, diff, editor, inspector, logs) | Frontend Agent | P0 | `todo` | M4-006 | Studio supports complete create-inspect-iterate loop in one surface |
| HAVEN-002 | M4 | Add prompt mode presets and starter prompt chips | Frontend Agent | P0 | `todo` | HAVEN-001 | New users can launch common game types without manual prompt engineering |
| HAVEN-003 | M4 | Implement preview lifecycle channel and instant refresh UX | Platform Agent | P0 | `todo` | HAVEN-001 | Preview updates from run events without manual reload |
| HAVEN-004 | M4/M5 | Add replay and share flow (share link + source/artifact download) | Platform Agent | P1 | `todo` | HAVEN-003 | Every successful run can be replayed and shared from dashboard |
| HAVEN-005 | M5 | Add context compactifier and file-context selector for long sessions | Coding Agent | P1 | `todo` | ENG-305 | Long conversations stay stable and regenerate targeted files |
| HAVEN-006 | M5 | Create template registry and template picker UI | Coding Agent | P1 | `todo` | HAVEN-002 | Users can pick tagged templates and launch with predictable setup |
| HAVEN-007 | M5 | Add fallback asset pack mapping and inspector visibility | Coding Agent | P1 | `todo` | HAVEN-006 | Missing asset classes auto-fallback with clear timeline reporting |
| HAVEN-008 | M5 | Publish creator-centric demo flow (prompt -> playtest -> share) | PM Agent | P0 | `todo` | HAVEN-001, HAVEN-004 | Demo can be executed by non-core user end-to-end |

---

## Evidence (2026-03-14)

- Implemented strict contracts and exports under `vibe-game-engine/contracts/`.
- Implemented orchestration skeleton and retry branch under `vibe-game-engine/orchestration/`.
- Implemented validation tooling: `vibe-game-engine/scripts/validate.sh` and `vibe-game-engine/tools/log_parser.py`.
- Added deterministic tests:
	- `vibe-game-engine/tests/test_contracts.py`
	- `vibe-game-engine/tests/test_validation_loop.py`
- Test evidence:
	- Command: `python -m pytest tests -q`
	- Result: `6 passed in 0.07s`
	- Command: `python3.12 -m pytest tests -q`
	- Result: `6 passed in 0.05s`
	- Command: `python -m pytest tests -q` (after ENG-102/ENG-105)
	- Result: `9 passed in 0.12s`
	- Command: `python3.12 -m pytest tests -q` (after ENG-102/ENG-105)
	- Result: `9 passed in 0.08s`
	- Command: `python -m pytest tests -q` (after phase 2/3 implementations)
	- Result: `14 passed in 0.13s`
	- Command: `python scripts/smoke_single_prompt.py`
	- Result: `smoke_final_status=completed`, `smoke_retry_count=1`
	- Command: Docker headless validation (import/check/smoke) with `barichello/godot-ci:4.5.1`
	- Result: `validation_report_attempt_2.json` => `success=true`
	- Command: Docker-backed exporter invocation via `agents.exporter_agent.export_project`
	- Result: `success=true`, artifact `templates/base_2d_platformer/export/game.exe`, checksum recorded
	- Command: Docker image pinning for parity
	- Result: `barichello/godot-ci:4.6.1` pulled successfully
	- Command: Docker headless validation (4.6.1 import/check/smoke)
	- Result: `validation_report_attempt_461.json` => `success=true`
	- Command: Docker-backed exporter invocation with 4.6.1
	- Result: `success=true`, artifact `templates/base_2d_platformer/export/game_461.exe`, checksum recorded
	- Command: 2-minute export smoke (`game_461.exe`)
	- Result: `smoke_2min_alive=True` (bounded stop after threshold)