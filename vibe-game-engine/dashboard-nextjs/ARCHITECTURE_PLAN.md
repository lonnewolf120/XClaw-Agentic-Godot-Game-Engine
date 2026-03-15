# GENESIS ENGINE Dashboard OS - Component Plan

## Goal
Build `dashboard-nextjs` into the operating system for the Vibe Game Engine:
- control and monitor agents
- run commands and workflows
- observe live logs and job outcomes
- inspect engine status and artifacts
- manage runtime configuration and environment

## Information Architecture

### Global Shell (all routes)
- Left rail navigation: section switching and health badges
- Top command bar: global run controls, refresh cadence, clock
- Global status strip: backend health, queue count, active jobs

### Routes and Responsibilities
1. `/overview`
   - Mission status summary
   - KPI matrix (success rate, queue depth, retries, active jobs)
   - live recent runs timeline
   - command quick actions

2. `/agents`
   - Agent registry table (PM, Coordinator, Coding, Debugger, Exporter, QA, Asset)
   - Current state, capability tags, last run, assigned task
   - Agent action cards (start benchmark, smoke, triage, asset gate)

3. `/jobs`
   - Job queue and historical jobs
   - per-job status, return codes, duration, originating command
   - quick filters: running/completed/failed

4. `/logs`
   - Streaming log panel for selected job log file
   - latest command logs list
   - auto-tail mode with polling and line limits

5. `/engine`
   - Engine health panel (templates, runs, benchmark artifacts)
   - export artifact visibility
   - run-state and directory-level health checks

6. `/configs`
   - Runtime config inventory (compose file, root paths, command allowlist)
   - environment policy cards
   - read-only config summaries with links to source files

## Core Components
- `ControlPlaneLayout`: shell wrapper with nav + top bar + status strip
- `SectionHeader`: common heading + timestamp + refresh state
- `KpiGrid`: reusable KPI cards
- `AgentTable`: agent capability/state table
- `JobBoard`: running/completed/failed segmented lists
- `LogTailPanel`: selectable log source + auto tail display
- `EngineSnapshotPanel`: templates/runs/benchmarks stats
- `ConfigInventoryPanel`: runtime config and command catalog
- `CommandLauncher`: shared command trigger buttons

## Data Model (Dashboard API)
- `SystemSnapshot`
  - `timestampUtc`
  - `overview` (KPIs, agents, runs)
  - `jobs`
  - `engine` (templates, runs, benchmark files, health flags)
  - `configs` (project root, python executable, command list)
  - `logs` (recent log files and preview tails)

## Backend API Plan
- `GET /api/system`: aggregate snapshot for all pages
- `GET /api/logs`: list recent log files and optional tail content
- `POST /api/commands/run`: existing run endpoint for command launch
- `GET /api/jobs`: existing endpoint retained for focused polling
- `GET /api/overview`: existing endpoint retained for backward compatibility

## Realtime Strategy
- polling every 2-4 seconds for lightweight summary APIs
- route-level auto refresh controls in top bar
- future phase: upgrade to SSE/WebSocket once backend daemon emits event stream

## Implementation Phases
1. Phase A (this pass):
   - new route structure + shared shell
   - aggregate API + logs API
   - reusable section components and command launcher

2. Phase B:
   - full filter/search state in jobs and logs
   - artifact browser with run folder drill-down
   - config editing workflows with guarded mutations

3. Phase C:
   - SSE/WebSocket event stream
   - role-based access and action authorization
   - advanced observability (trace, retry funnel, latency percentile charts)
