# Vibe Game Engine – Master Plan & Operating Model (v1.1)

**Project:** Vibe Game Engine (Godot 4.6.1 Hybrid Edition)  
**Date:** March 14, 2026  
**Owner:** Project Manager + Coordinator Multi-Agent System  
**Mission:** Convert natural-language game ideas into playable outputs in under 10 minutes with production reliability.
High-Level Overview
The Vibe Game Engine is a fully autonomous, multi-agent game generation system targeting Godot 4.6.1. It relies on AI orchestration to generate standalone executables or live-editable Godot projects from natural-language prompts in under 10 minutes.

## Pull the full repository with submodules

Clone everything in one pass:

```powershell
git clone --recurse-submodules https://github.com/lonnewolf120/XClaw-Agentic-Godot-Game-Engine.git
cd "XClaw-Agentic-Godot-Game-Engine"
git submodule update --init --recursive
```

Update an existing checkout, including every submodule:

```powershell
git pull --recurse-submodules
git submodule sync --recursive
git submodule update --init --recursive
```

Architectural Paths
Default (Standalone Export-First):
Prompt → Planner → Code/Asset Agents → Import → Headless Validate → Debug Loop (max 3 retries) → Export → Package
Optional (Live Bridge):
Utilizes a WebSocket JSON-RPC bridge (godot-bridge-mcp-public) for live editor integration, with automatic fallback to standalone mode if disconnected.
Core Platform Stack
Orchestration: LangGraph state machine using CrewAI-style role boundaries for multi-agent coordination.
LLM Routing: LiteLLM with a local-first policy (using DeepSeek-V3.2 via Ollama), falling back to OpenRouter.
RAG (Retrieval-Augmented Generation): Chroma vector index containing official Godot 4.6.1 documentation and examples.
Validation & CI: docker-godot-headless images for deterministic CI/headless operations, import checks, and logic testing.
Local Asset Generation: FLUX.1 schnell (2D/Images), TripoSR (3D models), Wan2.6 (Video), and Stable Audio Open.
Multi-Agent Operating Model
The workload is distributed among specialized agents:

Project Manager & Coordinator: Handle requirements, milestone gating, and task graph/dependency execution.
Coding & Asset Agents: Generate Godot scenes, .gd scripts, and normalized audio/visual assets.
Importer & Debugger: Manage resource importing, scene wiring, and parsing validation logs for root-cause fixes.
Exporter & QA/Validator: Handle packaging, acceptance checks, and final manifest generation.
Anti-Hallucination Controls
A strict framework enforces code reliability and valid scene generation:

Pydantic v2 Strict Schemas for all agent outputs.
Pre-call RAG Grounding against Godot 4.6.1 concepts instead of legacy syntax.
Few-shot Prompting utilizing proven .gd and .tscn patterns.
Deterministic Validation Loop that applies self-correction patches up to 3 times before triggering a human checkpoint.
---

## 1) Product Goal

Deliver a **fully autonomous, zero-prototype** multi-agent game generation system that produces:

1. **Standalone executable by default** (`.exe` / `.apk` / `.zip`), or  
2. **Live-editable Godot project** via Godot Editor bridge,

with:

- **95%+ first-pass success**
- **<10 min P95 generation time**
- deterministic validation and retry behavior
- strict anti-hallucination controls

---

## 2) Scope

### In Scope (MVP)
- Godot 4.6.1 based generation pipeline
- Standalone export-first workflow
- Optional live bridge mode via WebSocket JSON-RPC
- Multi-agent orchestration (planning, coding, asseting, debugging, exporting)
- Schema-enforced outputs
- Headless validation loop with max 3 retries
- Core frontend progress dashboard
- 50+ prompt regression suite
- Launch-ready docs and installer path

### Out of Scope (Post-MVP)
- Large-scale MMO networking
- AAA-level fidelity expectations
- Full console certification workflows
- Unity parity (experimental only after MVP)

---

## 3) Architecture Summary (Hybrid)

### Default Path: Standalone
Prompt -> Planner -> Code/Asset agents -> Import -> Headless Validate -> Debug Loop (<=3) -> Export -> Package -> Deliverable artifact

### Optional Path: Live Bridge
Same generation core, but application done through editor bridge (WebSocket).  
If bridge fails or disconnects, automatic fallback to file mode without stopping run.

### Core Platform Components
- **Orchestration:** LangGraph state machine + CrewAI-style role boundaries
- **Model Router:** LiteLLM with local-first policy (DeepSeek-V3.2 via Ollama), fallback OpenRouter
- **RAG:** Chroma index over official Godot 4.6.1 docs/examples
- **Validation:** Godot headless check/import/run loop + log parser
- **Asset QA:** vision checks + deterministic asset constraints

---

## 4) Ground-Truth Integrations

- Godot 4.6.1 + export templates
- MarcuzziFranco bridge (`godot-bridge-mcp-public`) for editor live mode
- `docker-godot-headless` images for deterministic CI/headless operations
- Local generation stack:
  - DeepSeek-V3.2 (text/code)
  - FLUX.1 schnell (images)
  - Wan2.6 (video, optional)
  - TripoSR (3D, optional)
  - Stable Audio Open (audio, optional)

---

## 5) Operating Model

### Core Roles
- **Project Manager Agent:** requirements, scope discipline, milestone gating
- **Coordinator Agent:** task graph execution and dependency ordering
- **Coding Agent:** Godot scene/script generation under strict schemas
- **Asset Agents:** image/3D/audio/video generation and normalization
- **Importer Agent:** Godot resource import + scene wiring
- **Debugger Agent:** root-cause fixes from validation logs
- **Exporter Agent:** artifact build and packaging
- **QA/Validator Agent:** acceptance checks and final manifest generation

### Single Source of Truth
Every run is tracked in a strict `RunState` object and persisted to run artifacts.

### Non-Negotiable Policy
No run can be marked complete without passing validation and export acceptance gates.

---

## 6) Milestone Plan (6 Weeks)

### Phase 0 (Week 1) – Foundation
- repo structure, compose stack, template bootstraps, doc index
- deliverable: one-command startup baseline

### Phase 1 (Weeks 1-2) – Core Agent Reliability
- strict schemas, planning+coding+debugger agents
- anti-hallucination contracts enforced

### Phase 2 (Weeks 2-3) – Asset Pipeline
- generation, normalization, import hooks, quality gates

### Phase 3 (Weeks 3-4) – Validation/Export + Bridge
- deterministic retry loop + standalone export
- bridge integration + fallback safety

### Phase 4 (Weeks 4-5) – UX and Observability
- dashboard mode selector, live progress, logs, previews

### Phase 5 (Weeks 5-6) – Hardening & Launch
- 50+ test prompts, docs, demo, installer, release assets

---

## 7) Day-1 Supported Use Cases

1. 2D platformer
2. 3D FPS (small scope)
3. endless procedural runner/roguelike-lite
4. visual novel/dialogue-focused game
5. 2.5D parallax shooter
6. rhythm/music mini-game
7. cutscene-driven short narrative experience
8. multiplayer-lite (max 4 players)
9. XR prototype track
10. remix existing uploaded game project

---

## 8) Anti-Hallucination Framework (Mandatory)

1. **Strict schemas (Pydantic v2)** for all agent outputs  
2. **RAG pre-call grounding** against official docs/examples  
3. **Few-shot references** with working `.gd` / `.tscn` patterns  
4. **Validation loop** with root-cause debug patches (max 3 retries)  
5. **Asset semantic checks** against prompt intent  
6. **Human checkpoint** after retry exhaustion (never silent failure)

---

## 9) Reliability & SLO Targets

- P50 generation: < 6 min
- P95 generation: < 10 min
- first-pass success: >= 95%
- pass within <=3 retries: >= 99%
- bridge fallback continuity: >= 99.5%
- crash-free 2-minute smoke launch: >= 98%

---

## 10) Quality Gates (Definition of Done)

A run is **DONE** only if all conditions are true:

1. Headless validation pass
2. Export artifact exists at expected output path
3. Smoke run passes
4. Final manifest recorded
5. Replay bundle preserved (prompt, plan, logs, patches, metrics)

---

## 11) Risk Register (Top Risks + Controls)

1. **Model drift / invalid Godot syntax**  
   Control: schema lock + RAG + parser validation

2. **Bridge instability**  
   Control: heartbeat + retry-once + instant fallback to file mode

3. **Asset generation timeout/OOM**  
   Control: degrade resolution, retry budget, template fallback assets

4. **Export template mismatch**  
   Control: pre-bundled templates + startup verifier

5. **Complex project graph failure**  
   Control: chunked generation and deterministic node naming/IDs

---

## 12) Do’s & Don’ts

### Users
- **Do:** give concrete constraints and target style/mechanics
- **Do:** use live mode for rapid iteration
- **Don’t:** expect large-scale MMO/AAA constraints in MVP

### Developers
- **Do:** run validation before export every time
- **Do:** enforce schemas strictly
- **Don’t:** trust unvalidated model output
- **Don’t:** bypass retry/debug loop

---

## 13) Governance Rules

- No hidden failures: all errors serialized into run logs
- All milestone exits require acceptance evidence
- Any scope expansion must enter decision log first
- Security baseline: token-safe logs, isolated run directories, artifact checksums

---

## 14) Execution Discipline

The implementation proceeds milestone-by-milestone only.  
No jumping ahead unless current milestone acceptance criteria are satisfied.

Operational loop:

1. Plan milestone tasks
2. Implement scoped deliverables
3. Validate with objective checks
4. Update board and logs
5. Gate review
6. Advance only on pass

---

## 15) Immediate Work Order (Activated)

1. Stand up project-management system files
2. Implement Milestone 1 backbone:
   - contracts
   - orchestration skeleton
   - validation/debug loop
   - base template pass path
3. Record metrics baseline and progress logs
4. Move to Milestone 2 only after Milestone 1 acceptance pass

---

## 16) Success Criteria for Public Release

- 50-prompt suite passing at target threshold
- Standalone artifact verified on clean Windows machine
- Bridge mode validated with running editor
- End-user docs and demo video ready
- License and disclaimers included
- Reproducible setup with one-command bootstrap

---
