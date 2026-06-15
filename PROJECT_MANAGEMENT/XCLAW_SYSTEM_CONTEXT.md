# XClaw Master System Context

> **Date Created**: June 1, 2026
> **Last Status**: Phase 7 Integration (GameMaker Core) Complete.

## 1. Engine Identity & Philosophy
XClaw is a **Headless LLM-Driven Godot Game Maker**.
- **Role Separation**: The USER manages visuals/scenes. The AI manages logic/mechanics.
- **Outcome Driven**: Every change is verified via syntax and behavioral playtesting.
- **Premium Default**: Uses the **VibeCore** framework to ensure all games have high-quality HUDs, signal buses, and global state management.

## 2. Technical Stack
- **Orchestrator**: Python 3.10+ CLI (`xclaw_cli`).
- **Runtime**: Godot 4.3+ (Headless).
- **LLM**: Gemini 3.5 Flash / Gemini 3.1 Pro (via Google GenAI SDK v1).
- **Authentication**: Supports Application Default Credentials (ADC) and Enterprise API Keys.

## 3. Architecture (The VibeCore)
The engine automatically injects the `vibe_core/` library into every project:
- `vibe_events.gd`: Global Event Bus (Signals).
- `vibe_state.gd`: Centralized data (Score, Health, Timers).
- `vibe_hud.gd`: Automated premium UI overlay.
- `trait_applier.gd`: Logic injector for non-destructive scene modification.
- `scout.gd`: Introspection tool that reports the SceneTree to the AI.

## 4. Verification Loop
The engine uses a 4-step safety gate:
1. **Syntax Check**: `godot --headless --check-only`.
2. **Behavioral Smoke Test**: 8-second execution to detect runtime crashes.
3. **Scout Verification**: Confirms logic-relevant nodes (Player, Enemies) are present.
4. **Self-Correction**: Iterates based on error logs and scout data.

## 5. Directory Structure
- `xclaw_cli/`: Core Python logic.
- `vibe-game-engine/templates/`: Starter kits for different genres.
- `vibe-game-engine/vibe_core_src/`: Source for the Godot framework.
- `PROJECT_MANAGEMENT/`: Plans, walkthroughs, and logs.

## 6. Handover Notes for Future Agents
- **Trait-First**: Do not modify user `.tscn` files. Always use `VibeTraits` to attach logic.
- **JSON Contracts**: The LLM must return structured JSON in the `FileWrite` format.
- **ADC Mode**: If `GEMINI_API_KEY` is missing, fallback to ADC using project `parents-care-453403`.
- **Godot Path**: Godot executable is currently at `D:\Software\Godot\Godot.exe`.
