# Vibe Game Engine — Day-to-Day Runbook (Project Manager + Coordinator)

## Purpose
This runbook defines how to operate the project daily so implementation stays aligned with milestones, quality gates, and the production goal:

- **Default output:** standalone playable build
- **Optional output:** live-editable Godot workflow
- **Reliability target:** high first-pass success with strict validation loop

---

## Core Operating Principles

1. **Milestone-first execution**
   - Only work on tasks mapped to the active milestone.
   - Do not add side features unless they unblock a milestone acceptance criterion.

2. **Single source of truth**
   - Planning and execution status are tracked in:
     - `PROJECT_MANAGEMENT/MASTER_PLAN.md`
     - `PROJECT_MANAGEMENT/MILESTONES.md`
     - `PROJECT_MANAGEMENT/TASK_BOARD.md`
     - `PROJECT_MANAGEMENT/PROGRESS_LOG.md`
     - `PROJECT_MANAGEMENT/QUALITY_GATES.md`

3. **No “done” without validation**
   - A task is complete only when acceptance criteria and quality gates pass.

4. **Strict anti-hallucination policy**
   - Structured schemas required.
   - RAG-backed implementation decisions required.
   - Validation/debug loop mandatory before export.

---

## Team Roles (Operational)

## Project Manager (PM)
- Owns scope, priorities, milestone gates, and release readiness.
- Decides what enters current sprint window.
- Enforces “no out-of-track work” rule.

## Coordinator
- Breaks milestone into executable tasks.
- Assigns task order and dependencies.
- Triggers validation, retry loops, and escalation.

## Coding Agent
- Implements contracts, orchestration, and tool integrations.
- Produces deterministic code and config changes only.

## Debugger Agent
- Reads failures/logs and proposes root-cause fixes.
- Performs minimal, targeted patches.

## Exporter Agent
- Handles platform export requests and artifact packaging.
- Confirms artifact existence + smoke checks.

---

## Daily Cadence (Mandatory)

## 1) Daily Start (15–20 min)
1. Open `MILESTONES.md` and identify **active milestone**.
2. Open `TASK_BOARD.md`:
   - Move selected tasks to `in_progress`.
   - Confirm each task has clear acceptance criteria.
3. Review `RISKS.md` and blocked items.
4. Write a short start entry in `PROGRESS_LOG.md`:
   - Date/time
   - Milestone
   - Planned tasks for the day

## 2) Build Window (Focused execution)
- Implement only milestone tasks.
- After each meaningful change:
  - Run local checks (lint/tests where available)
  - Run validation flow relevant to the feature
- Update `TASK_BOARD.md` continuously:
  - `todo -> in_progress -> done` only with evidence
  - `in_progress -> blocked` with blocker reason + owner

## 3) Validation Window
For each completed task:
1. Verify acceptance criteria in `MILESTONES.md`
2. Verify quality gates in `QUALITY_GATES.md`
3. Attach proof (log reference, artifact path, test result)
4. Mark task `done`

## 4) End-of-Day Close (10–15 min)
1. Update `PROGRESS_LOG.md`:
   - What shipped
   - What failed
   - What was deferred
2. Update `RISKS.md`:
   - New risks
   - Mitigation status
3. Confirm next day’s top 3 priority tasks.

---

## Milestone Execution Protocol (Do Not Deviate)

For each milestone:

1. **Scope Lock**
   - Freeze milestone scope from `MILESTONES.md`.
   - Any additional work is deferred to backlog unless critical.

2. **Task Breakdown**
   - Split milestone into small, testable tasks.
   - Each task must have:
     - owner
     - dependency list
     - acceptance criteria
     - expected artifacts

3. **Implementation**
   - Work tasks in dependency order.
   - Keep commits/change sets atomic and reversible.

4. **Gate Check**
   - Execute milestone acceptance tests.
   - If any gate fails:
     - enter retry/debug loop
     - do not mark milestone complete

5. **Milestone Completion**
   - Mark milestone complete only when all criteria pass.
   - Add completion summary to `PROGRESS_LOG.md`.

---

## Definition of Done (Task Level)

A task is **Done** only if all are true:

- Implementation complete and deterministic.
- Related checks/tests pass.
- Validation output is successful.
- Required docs updated.
- Evidence linked in `TASK_BOARD.md`.

If any item is missing, status is **not done**.

---

## Definition of Done (Milestone Level)

A milestone is **Done** only if all are true:

1. All milestone tasks are done.
2. Acceptance criteria pass as written.
3. No unresolved blocker marked “critical.”
4. Progress summary logged.
5. Next milestone readiness confirmed.

---

## Change Control Rules

1. **No silent scope expansion**
   - Any new feature request must be logged in backlog first.

2. **No architecture drift**
   - If implementation changes architecture, record decision in `DECISIONS.md`.

3. **No hidden failures**
   - Log all failed validations and retries in `PROGRESS_LOG.md`.

4. **No skipping quality gates**
   - Validation/debug/export checks are mandatory.

---

## Incident Handling (When something breaks)

## Severity Levels
- **S1**: Core pipeline down (cannot generate/validate/export)
- **S2**: Major feature broken with workaround
- **S3**: Non-critical defect

## Response
1. Record incident in `PROGRESS_LOG.md` with timestamp.
2. Assign owner + immediate mitigation.
3. Prioritize root-cause fix over symptom patching.
4. Add preventive action to `RISKS.md` and `DECISIONS.md` if architectural.

---

## Needs-Human Escalation Policy (B-002)

When a run reaches `needs_human` after retry budget exhaustion, apply this policy immediately:

1. Auto-create escalation artifact:
   - `runs/<run_id>/.vibe/escalation/needs_human_ticket.json`
2. Auto-append queue entry:
   - `runs/needs_human_queue.jsonl`
3. Required ticket fields:
   - `run_id`, `retry_count`, `max_retries`, `failure_reason`
   - `latest_validation_summary`, retry event timeline, `workspace_dir`
4. Human operator action:
   - Triage queue entries in FIFO order.
   - Classify as `prompt_issue`, `template_issue`, `runtime_issue`, or `agent_logic_issue`.
   - Record disposition and mitigation in `PROGRESS_LOG.md`.
5. Completion rule:
   - Do not rerun until a concrete mitigation is attached to the ticket.

---

## Risk Management Rules

- Track each risk with:
  - probability (low/med/high)
  - impact (low/med/high)
  - owner
  - mitigation
  - trigger signal
- Review top 5 risks daily.
- Escalate any high-impact + high-probability risk immediately.

---

## Coordination Templates

## Daily Start Note (copy/paste)
- Date:
- Active Milestone:
- Today’s Top 3 Tasks:
- Known Blockers:
- Expected Deliverables by EOD:

## Task Completion Note
- Task ID:
- Acceptance Criteria Met:
- Validation Evidence:
- Artifacts Produced:
- Follow-up Needed:

## Milestone Completion Note
- Milestone:
- Completed Scope:
- Validation/Export Evidence:
- Open Non-Critical Items:
- Next Milestone Start Date:

---

## Golden Rules (Always Enforced)

1. Stay on milestone track.
2. Validate before claiming completion.
3. Log decisions and failures transparently.
4. Prioritize reliability over feature count.
5. Ship only what passes gates.

---

## Quick Command Checklist (Operational mindset)

At any point, ask:
1. Is this in the current milestone scope?
2. Does this move acceptance criteria forward?
3. Can I prove it passed validation?
4. Did I update tracking docs?
5. Is the project now closer to shippable release quality?

If any answer is “no,” stop and re-align before continuing.

---

## Docker Baseline Services Map (OPS-001)

The baseline local service map is defined in:
- `docker-compose.vibe-baseline.yml`

Services included:
1. `ollama` — local LLM endpoint for tool-augmented planning/coding.
2. `comfyui` — optional asset generation backend.
3. `godot_headless_461` — pinned Godot 4.6.1 headless runtime for validation/export parity.
4. `bridge_service` — placeholder bridge service endpoint for live editor integration wiring.

Operational notes:
- Use this compose file as the default local stack for M2/M3 verification.
- If a service is unavailable, mark run status as blocked and record fallback in `PROGRESS_LOG.md`.
- Any service/image version change must be logged in `DECISIONS.md`.

---

## Dashboard Command Center (M4)

Central UI location:
- `vibe-game-engine/dashboard-nextjs/`

Launch commands:
1. From workspace root (compat wrapper):
   - `python ./scripts/dashboard_server.py`
2. Direct Next.js launch:
   - `Set-Location "vibe-game-engine/dashboard-nextjs"`
   - `npm install`
   - `npm run dev`

Default URL:
- `http://127.0.0.1:3000`

Available command controls:
1. `Run Pytest` (`python -m pytest tests -q`)
2. `Run Smoke Prompt` (`python scripts/smoke_single_prompt.py`)
3. `Run Benchmark` (`python scripts/qa_benchmark.py`)
4. `Run Asset Quality Gate` (`python scripts/run_asset_quality_gate.py`)
5. `Triage Escalations` (`python scripts/triage_escalations.py`)

Operational rules:
- Only allowlisted commands can run from dashboard API.
- Command outputs are logged under `runs/dashboard_commands/`.
- Dashboard polling interval is 3 seconds for overview + jobs endpoints.

---

## MVP Scope Freeze & Release Hardening

As of the current milestone (M4 - Operational Control Plane), the MVP scope is officially frozen.

### Clean Machine Verification
To verify the engine works out-of-the-box on a fresh clone without environment-specific artifacts:

1. Copy the `vibe-game-engine/` and `templates/` folders to a fresh directory.
2. Setup the python virtual environment.
3. Install dependencies:
   ```bash
   python -m pip install pytest "pydantic>=1.10,<3"
   ```
4. Run the core orchestration tests and validations:
   ```bash
   python -m pytest tests -q
   python scripts/smoke_single_prompt.py
   python scripts/qa_benchmark.py
   ```
5. Ensure 100% of the non-escalating prompts pass deterministically.

### Pre-Release Checklist
- [x] Template assets fallbacks correctly configured.
- [x] Credit budgeting implemented for API interactions.
- [x] Recursive permissions explicitly enforced on Windows/Linux.
- [x] Control Plane dashboard operational (run workflows, triage).
- [x] Local clean machine workflow verified and passing.

If any major bug arises, do not expand the MVP scope. Focus exclusively on fixing regressions. All new features go into the post-MVP backlog.
