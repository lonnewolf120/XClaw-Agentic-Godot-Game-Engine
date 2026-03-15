# XClaw Agentic Godot Game Engine - QA & AI Integration Plan

To fully leverage the capabilities of AI agents alongside the Godot engine and to ensure seamless and reliable game creation, we must address existing stability risks, integrate robust automation, and provide guardrails around AI generation.

## 1. Stabilize the Godot-MCP Bridge (Live Mode)
*Current Gap*: Disconnections and placeholder logic in the WebSockets/JSON-RPC integration reduce real-time editing capability.
**Action Plan:**
- **Reconnect Logic & Resilience:** Implement an exponential backoff reconnect strategy for WebSocket disconnections in the `bridge_service`.
- **Throttled State Synchronization:** Debounce the sync between Godot's live scene tree and the Agent's state representation to prevent network flooding during heavy prompt-driven generation.
- **Failover to File-based mode:** Solidify the automatic fallback (ADR-001) that seamlessly transitions to the file-based pipeline when live connection unrecoverably fails.

## 2. Refine the AI Agent Orchestration & Guardrails
*Current Gap*: Complex scene graphs cause AI context drift, and debugging loops can result in total failure if not resolved within 3 retries.
**Action Plan:**
- **Enhanced RAG Knowledge Base:** Inject deterministic, manually curated Godot 4 `tscn` and `gd` code snippets into the RAG vector store for specific complex patterns (e.g., CharacterBody3D, NavigationRegion3D).
- **Chunked Graph Generation:** When creating complex mechanics, force the Coordinator Agent to break the task into discrete, linearly named chunk processes (e.g., generate Map first, then Player, then Enemies).
- **Human-in-the-Loop Escalation:** Build a user-facing review UI (`needs_human` queue) when the Debugger agent exhausts its 3 retry limits, allowing the developer to provide a quick manual fix to resume the AI sequence.

## 3. Headless Validation and CI Tests
*Current Gap*: Deterministic checks require a robust pipeline to prevent broken builds from reaching the exporter.
**Action Plan:**
- **Pre-Agent Static Analysis:** Use tools like `gdlint` or a pre-flight schema checker before code is passed to the import pipeline.
- **Headless BDD Tests:** Run Godot headless integration tests (via `barichello/godot-ci:4.6.1`) that verify essential game loop characteristics (e.g., scene loads without errors, player instantiates successfully).
- **Automated Regression Suite:** Develop a baseline template suite (e.g., testing `Starter-Kit-3D-Platformer`) that is continually rebuilt by the AI agents on PRs to catch degradation in AI logic.

## 4. Asset Generation Consistency
*Current Gap*: Asset agents (ComfyUI/FLUX.1) face OOM and format drift, breaking the pipeline.
**Action Plan:**
- **Resource Monitoring & Capping:** Ensure the asset generation agents track local VRAM/RAM. If thresholds are breached, gracefully degrade resolution or step count.
- **Fallback Asset Library:** When generation fails twice, instantly fallback to the 32 pre-bundled template-safe placeholder assets (ADR-008) to ensure the game remains functional/testable while logging a placeholder warning.
- **Format Normalization:** Enforce strict python-side conversion and compression (e.g., converting all AI audio down to standard `.ogg` and AI images to optimized `.png`/`.webp` sizes before Godot import).

## 5. Scope Management for Multi-Agent
*Current Gap*: Multiplayer networking and massive scoped features cause massive AI hallucinations (ADR-009).
**Action Plan:**
- **Strict Pydantic Enforcement:** Lock the Project Manager (Scope) agent to Pydantic schemas that explicitly forbid generating unsupported edge-case features (e.g., generic MMO logic vs high-level 4-player max).
- **Pre-baked Templates:** Provide the "Starter Kits" (`Starter-Kit-3D-Platformer`, `Starter-Kit-FPS`, etc.) as heavily weighted priors into the prompt. Instead of making the agent invent an FPS controller from scratch, prompt it to instantiate and *modify* the existing FPS starter kit.

## 6. Telemetry and Dashboard
**Action Plan:**
- Finalize the `dashboard_server.py` and `dashboard-nextjs` integration to visually map the LangGraph state machine. This allows the developer to watch the project manager delegate tasks to the coding/asset agents in real-time, visualizing token usage, retry loops, and Godot headless test outputs.