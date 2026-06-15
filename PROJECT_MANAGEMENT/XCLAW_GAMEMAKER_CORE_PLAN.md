# XClaw GameMaker Core: Outcome-Driven Implementation Plan

## Objective
Transition XClaw from a "script-patcher" to a **Fully Functional Game Maker**. The core philosophy is **Observed Outcomes**: the engine must generate logic, observe game behavior in a headless run, and self-correct based on runtime data, not just syntax.

---

## 1. Phase Architecture & Deliverables

### Phase 1: The "Scout" (Observability)
**Goal**: Give the AI "eyes" to see the project structure and runtime behavior.
*   **Deliverable 1.1**: `xclaw_cli/scout.gd` (Runtime Probe).
    *   *Function*: Scans the SceneTree, lists all active nodes, their types, and current property values.
*   **Deliverable 1.2**: `headless.py` expansion (`detect_scout_output`).
    *   *Outcome*: The AI context prompt will now include: *"Project has a MeshInstance3D named 'Ship'. At runtime, the player moved from X:0 to X:5."*

### Phase 2: Trait-vibe Architecture (Organization)
**Goal**: Ensure modularity and prevent the AI from breaking user scenes.
*   **Deliverable 2.1**: `vibe_core/traits/` (Class library).
    *   *Examples*: `HealthTrait.gd`, `MovementTrait.gd`, `DamageTrait.gd`.
*   **Deliverable 2.2**: `vibe_core/trait_applier.gd`.
    *   *Outcome*: Instead of editing the player scene, the AI writes: `TraitApplier.add_trait(player_node, "MovementTrait")`. This protects user-made visuals.

### Phase 3: The Verification Loop (Test-Driven AI)
**Goal**: Automated "Playtesting" as a gate for success.
*   **Deliverable 3.1**: `engine.py` "Validation Feedback" loop.
*   **Deliverable 3.2**: `xclaw_cli/phase7_verification_test.py`.
    *   *Outcome*: If the user prompt is "Make gravity stronger," the engine runs the game for 5s. If `scout.gd` reports `Velocity.y` didn't increase, the check **FAILS** and the AI is told *why* it failed at runtime.

### Phase 4: UI & State Integration (Integration)
**Goal**: Making the generated systems "feel" like a game.
*   **Deliverable 4.1**: `vibe_core/ui/hud/`.
    *   *Function*: A standardized, auto-expanding HUD.
*   **Deliverable 4.2**: `VibeEvents` and `VibeState` wiring.
    *   *Outcome*: AI-generated items automatically appear in the HUD inventory because they follow the `VibeCore` protocol.

---

## 2. Expectations & Success Metrics

| Metric | Baseline (Now) | Target (Fully Functional) |
| :--- | :--- | :--- |
| **Verification** | Syntax Check only | **Behavior Check** (Nodes moved? Damage dealt?) |
| **Organization** | Script Patching | **Trait-Based Injection** (Non-destructive) |
| **Context** | File Tree only | **Runtime Reflection** (Scene Tree + Property Map) |
| **Deliverable** | Modified .gd file | **Verified Project Artifact** + Export |

---

## 3. Technical Constraints (Optimization)
*   **Zero-Dependency**: Every `vibe_core` script must run without external plugins.
*   **Performance**: Use Godot's `_physics_process` and low-level `Array` operations for pathing.
*   **Safety**: All AI writes are sandboxed to `res://scripts/ai/` and `res://vibe_core/traits/`.

## 4. User Review Required (IMPORTANT)
> [!IMPORTANT]
> To enable Phase 1 (Scouting), the AI will need to add a temporary script to your `MainScene` to observe it. This happens headlessly in the `runs/` directory and does **not** affect your master copy.

> [!WARNING]
> This plan assumes you are handling the **Visual Layer** (Models/Animations) and the AI is handling the **System Layer**. You must name your nodes clearly for the "Scout" tool to identify them.

---

## 5. Execution Order
1.  **P1**: Implement `scout.gd` and the Python Parser.
2.  **P2**: Build the `Trait` library and injector.
3.  **P3**: Wire the self-correction loop in `engine.py`.
4.  **P4**: Implement the standard HUD.

---

## Phases 6 & 7: Implementation Summary [COMPLETED]

The XClaw engine has been successfully upgraded into a fully outcome-driven GameMaker.

### Final Achievements:
- [x] **VibeCore Framework**: Standardized signal bus (`vibe_events.gd`), global state (`vibe_state.gd`), and modular traits.
- [x] **Behavioral Loop**: Implemented `smoke_test()` in `headless.py` and combined it with `scout.gd` to observe runtime node behavior.
- [x] **LLM Evolution**: Native integration with **Gemini 3.5 Flash** using Enterprise v1 API and ADC support.
- [x] **Persistence**: Created `XCLAW_SYSTEM_CONTEXT.md` to ensure state continuity for future agent sessions.

**XClaw is now 100% functional and ready for agentic game creation.**
