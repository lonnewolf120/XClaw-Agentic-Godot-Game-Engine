# Vibe Game Engine – Master Plan & Operating Model (v1.1)

**Project:** Vibe Game Engine (Godot 4.6.1 Hybrid Edition)  
**Date:** March 14, 2026  
**Owner:** Project Manager + Coordinator Multi-Agent System  
**Mission:** Convert natural-language game ideas into playable outputs in under 10 minutes with production reliability.

---

## 1) Product Goal

Deliver a **fully autonomous, zero-prototype** multi-agent game generation system that produces:

1. **Standalone executable by default** (`.exe` / `.apk` / `.zip`), or  
2. **Live-editable Godot project** via Godot Editor bridge,

with:

- **60-75% first-pass success (90-95% after automatic retries)**
- **8-12 min P50 generation time (P95 15-25 min)**
- deterministic validation and retry behavior
- strict anti-hallucination controls

---

## 2) Scope

### In Scope (MVP)
- Godot 4.6.1 based generation pipeline
- Standalone export-first workflow
- Optional live bridge mode via WebSocket JSON-RPC
- Multi-agent orchestration (Planner, Builder, Validator, Debugger only)
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

### Optional Path: Live Bridge & Native AI Extension
Same generation core, but application done through editor bridge (WebSocket) and ultimately a fully embedded **Godot Editor Plugin**.  
Users run Godot naturally, using a dockable XClaw chat panel to dynamically alter the active Scene Tree without external text-diffing.

### The 6-Layer Engine Architecture
1. **Godot Native Plugin Layer:** Dock UI, selection context service, diff preview, undo/redo adapter. (Treated as an execution surface, not the source of truth).
2. **Backend Services (Logical Split):** Python FastAPI divided into: API Service, Orchestrator, Worker Runner, and Artifact/Run Store.
3. **Knowledge/Context Layer (Two Stores):** 
   - *Project Intelligence Store:* parsed scene graphs, successful patterns, resource IDs.
   - *Public Knowledge Store:* Godot 4.6.1 docs chunks via Chroma.
4. **Execution Layer:** Strict JSON Action Schemas mapping to deterministic engine commands.
5. **Validation Layer (Tiered):** 1) Static schema/path checks -> 2) Editor-safe node checks -> 3) Headless smoke test -> 4) Export probes.
6. **Observability & Infrastructure:** RunState persistence store, task queues, telemetry for costs/latency, and caching.

### Core Platform Components
- **Orchestration:** LangGraph state machine (strict workflow, no unstructured agent banter).
- **Model Router:** LiteLLM using Task-Type Routing (small local for retrieval/summaries, strong local/cloud for planner/debugger).
- **RAG:** Chroma index (assistive grounding, focusing primarily on templates and local context first).
- **Validation:** Tiered docker-godot-headless check/import/run loops.
- **Asset QA:** 2D sizes/formats normalization only (No 3D/video in MVP).

---

## 4) Ground-Truth Integrations

- Godot 4.6.1 + export templates
- MarcuzziFranco bridge (`godot-bridge-mcp-public`) for editor live mode
- `docker-godot-headless` images for deterministic CI/headless operations
- Local generation stack:
  - DeepSeek-V3.2 (text/code via Ollama)
  - FLUX.1 schnell (2D UI/sprites only)
  - (Note: No 3D, video, or complex audio generation in MVP)

---

## 5) Operating Model

### Core Roles (Strict 4-Role Architecture)
- **Planner Agent:** Creates the blueprint, translates ideas to actionable constraints, selects templates. 
- **Builder Agent:** Handles coding (GDScript) and 2D asset ingestion per strict JSON schemas. 
- **Validator Agent:** Executes the tiered checks (static, editor-safe, headless, export).
- **Debugger Agent:** Receives structured logs, plans patches, submits targeted diffs.
*(Note: 'Coordinator' and 'PM' logic are handled infrastructurally in LangGraph and API services, not as distinct AI personalities).*

### Agent Communication Protocol (RunState + Action Plan Bus)
Agents **must not** chat arbitrarily. They communicate exclusively through a structured RunState object:
- **RunState Storage:** Backed by persistent store, enabling resumable partial applied steps and trace replay.
- **Message Types (Strict JSON):**
  - Planner -> LangGraph: PLAN_MESSAGE (tasks, roles, goals)
  - Builder -> LangGraph: ACTION_SCHEMA_MESSAGE (batch of deterministic actions)
  - Validator -> Debugger: VALIDATION_RESULT (status, structured errors)
  - Debugger -> LangGraph: DEBUG_PATCH (diff patches)
- **Rules:** No agent calls tools directly. LangGraph workflow nodes schedule execution.

### Fundamental Infrastructure Needs (MVP Base)
1. **Run-State Store:** Database tracking full job progress (prompt -> plan -> action -> validation -> artifact).
2. **Queueing & Backpressure:** Job queues and GPU worker pools to isolate tasks.
3. **Caching:** Storing retrieved chunks, validated action bundles, and asset transforms to reduce retry costs.
4. **Telemetry:** Structured metrics tracking tokens/step, per-agent latency, and validation-failure taxonomy.

### Single Source of Truth
Every run is tracked in a strict `RunState` object and persisted to run artifacts.

### Non-Negotiable Policy
No run can be marked complete without passing validation and export acceptance gates.

---

## 6) Milestone Plan (Restructured for Reliability)

### Phase 0 (Week 1) – Deterministic Generator Skeleton
- **Goal:** Prompt -> working Godot project -> headless run success
- **Deliverable:** CLI generator only (no UI), single planner/coder agent, strict action schema v0, template-based assets only, headless validation command. Prove baseline determinism.

### Phase 1 (Weeks 2-3) – Reliability Engine
- **Goal:** Make generation stable before making it smart
- **Deliverable:** Debugger agent loop (max 2 retries), structured error classification, deterministic node naming, validation schema, 10-prompt regression suite, run telemetry, export artifact builder. (No asset AI, no editor plugin yet).

### Phase 2 (Weeks 4-5) – Agent Scaling + Asset Layer Lite
- **Goal:** Improve capability without breaking reliability
- **Deliverable:** Multi-agent orchestration (planner+coder+debugger), simple sprite/texture generation only, asset normalization pipeline, project chunking, local model router integration, cost tracking per run.

### Phase 3 (Week 6+) – Native Editor Plugin (XClaw)
- **Goal:** Move from batch generator -> interactive system
- **Deliverable:** Godot dock plugin UI, selection-context extraction, action diff preview, undo grouping execution layer, live apply mode, bridge fallback.

---

## 7) True MVP Supported Use Cases (3 Flagships)

1. **2D Platformer** (movement, jump physics, 1 enemy type, health system, simple UI)
2. **Endless Runner** (procedural obstacle spawning, score system, game over loop, camera follow)
3. **Dialogue / Narrative Game** (scene switching, dialogue system, branching choice, audio trigger)

*(Note: FPS, XR, rhythm, video generation, multiplayer, and complex 3D asset generation are explicitly out of scope for the MVP to maintain reliability over complexity)*

---

## 8) Anti-Hallucination Framework (Mandatory)

1. **Strict Action Schemas (Pydantic v2):** LLMs must return structured execution JSON (`create_node`, `attach_script`), **never** raw unvalidated GDScript for `eval` execution.
2. **Selection-Driven Grounding:** The prompt anchors automatically to whatever node/scene the game developer currently has selected in the Editor UI.
3. **Safe Auto-Fix with Undo Stack:** All changes execute grouping via Godot's `EditorUndoRedoManager` so an entire AI step can be Ctrl+Z reversed natively.
4. **Validation loop** with root-cause debug patches (max 3 retries)  
5. **Asset semantic checks** against prompt intent  
6. **Human checkpoint** after retry exhaustion (never silent failure)

---

## 9) Reliability & SLO Targets
(Realistically calibrated for highly complex multi-agent reasoning steps)

- P50 generation: 8–12 min
- P95 generation: 15–25 min
- first-pass success: 60–75%
- success after automatic retries (<=2): 90–95%
- bridge fallback continuity: >= 99.5%
- crash-free 2-minute smoke test launch: >= 95%

## 10) Execution Cost Model (Estimated per generation)

- **LLM Tokens:** ~1.5M tokens (Planner/Coder/Debugger) -> ~$0.50 (OpenRouter fallback / local savings)
- **Asset GPU Time:** ~30-60s for 3-5 images (FLUX) -> ~$0.30 
- **Validation CPU:** 30-90s headless Docker verification -> ~$0.02
- **Storage/Bandwidth:** ~$0.03
- **Total Estimated Cost:** **~$0.85 per generation**
- *Constraint:* Strict tracking prevents runaway GPU cycles or unbounded retry loops.

---

## 11) Quality Gates (Definition of Done)

A run is **DONE** only if all conditions are true:

1. Headless validation pass
2. Export artifact exists at expected output path
3. Smoke run passes
4. Final manifest recorded
5. Replay bundle preserved (prompt, plan, logs, patches, metrics)

---

## 12) Risk Register (Top Risks + Controls)

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

## 13) Do’s & Don’ts

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

## 14) Governance Rules

- No hidden failures: all errors serialized into run logs
- All milestone exits require acceptance evidence
- Any scope expansion must enter decision log first
- Security baseline: token-safe logs, isolated run directories, artifact checksums

---

## 15) Execution Discipline

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

## 16) Immediate Work Order (Activated)

1. Stand up project-management system files (Completed)
2. Lock Contracts: Implement RunState and core message schemas (PLAN_MESSAGE, ACTION_SCHEMA_MESSAGE, etc.).
3. Implement Action Schema v0 (create_node, ttach_script, etc.).
4. Define validation-tier failure taxonomy.
5. Implement Phase 0 Deterministic Generator Skeleton:
   - standalone CLI pipeline
   - single baseline template
   - minimal LangGraph orchestration
6. Advance to Phase 1 only after Phase 0 outputs a runnable project on one command.

---

## 17) Success Criteria for Public Release

- 50-prompt suite passing at target threshold
- Standalone artifact verified on clean Windows machine
- Bridge mode validated with running editor
- End-user docs and demo video ready
- License and disclaimers included
- Reproducible setup with one-command bootstrap

---

## 18) Final Statement

This document is the authoritative operating plan for delivery.  
Execution must remain aligned to milestone gates, quality contracts, and reliability targets.  
No prototype shortcuts; only production-track implementation accepted.