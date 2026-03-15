# Game Dev Haven MVP Plan

**Project:** XClaw Agentic Godot Game Engine  
**Date:** 2026-03-16  
**Intent:** Build the most creator-friendly prompt-to-game platform, where anyone can ship a dream game without engine expertise.

---

## 1) Product Vision

XClaw MVP becomes a complete game creation platform with five promises:

1. You can describe a game in plain language and get a playable build fast.
2. You can see, edit, and iterate your game live from one studio surface.
3. You can import assets, templates, and references without workflow friction.
4. You can collaborate, replay, and recover every run.
5. You can publish and share your game from the same platform.

---

## 2) MVP Feature Set (Actionable)

## F1 - Creator Studio (All-in-one Workspace)

What users get:

1. Prompt composer with game mode presets (FPS, racing, city builder, platformer, narrative).
2. Live game viewport with refresh/reload/fullscreen controls.
3. File diff view, scene tree inspector, execution timeline, and log dock.
4. Device preview modes and responsive preview controls.

Code to take/adapt:

1. `bolt.diy/app/components/workbench/Workbench.client.tsx`
2. `bolt.diy/app/components/workbench/Preview.tsx`
3. `bolt.diy/app/components/workbench/DiffView.tsx`
4. `bolt.diy/app/components/workbench/EditorPanel.tsx`
5. `bolt.diy/app/components/workbench/InspectorPanel.tsx`

XClaw implementation instructions:

1. Keep existing Next.js app shell in `vibe-game-engine/dashboard-nextjs/src/components/studio/studio-layout.tsx`.
2. Port preview controls pattern from bolt into `vibe-game-engine/dashboard-nextjs/src/components/studio/godot-player.tsx`:
   - Add reload, fullscreen, device-size selector, and preview status badges.
3. Create `vibe-game-engine/dashboard-nextjs/src/components/studio/diff-panel.tsx`:
   - Use bolt diff UX pattern for changed files and line-level additions/deletions.
4. Create `vibe-game-engine/dashboard-nextjs/src/components/studio/editor-panel.tsx`:
   - Read generated file content and show focused code block or script preview.
5. Create `vibe-game-engine/dashboard-nextjs/src/components/studio/inspector-panel.tsx`:
   - Render scene node hierarchy and generated script metadata.
6. Wire all panels from studio layout with collapsible panes.

Definition of done:

1. One screen can launch run, monitor generation, inspect files, and preview game.

## F2 - Smart Prompt Engine (Dream-to-Plan)

What users get:

1. Prompts are expanded into actionable build plans automatically.
2. Long conversations stay coherent without degrading output quality.
3. Users can ask for refactors and style shifts without losing prior intent.

Code to take/adapt:

1. `vibesdk/worker/agents/utils/conversationCompactifier.ts`
2. `vibesdk/worker/agents/utils/codebaseContext.ts`
3. `vibesdk/worker/agents/tools/toolkit/regenerate-file.ts` (pattern)

XClaw implementation instructions:

1. Create `vibe-game-engine/orchestration/context_compactifier.py`:
   - Port compactification logic: turn-count threshold, token-estimate threshold, preserve recent messages.
2. Create `vibe-game-engine/orchestration/context_selector.py`:
   - Port context filtering idea to include only relevant files (exclude noise files).
3. Extend game generation coordinator to emit plan checkpoints:
   - `intent_parsed`, `template_selected`, `scene_generated`, `scripts_generated`, `playtest_ready`.
4. Add run metadata fields for summary and selected-context file list.

Definition of done:

1. Long sessions remain stable and regenerate targeted files without full reset.

## F3 - Template and Asset Universe

What users get:

1. Template marketplace style selector with starter kits and tags.
2. Asset policy hints (safe/free/local-first) and missing asset auto-fallback.
3. Guided import flow for users bringing external content.

Code to take/adapt:

1. `vibesdk/worker/agents/utils/templates.ts`
2. `vibesdk/worker/agents/utils/templateCustomizer.ts`
3. `bolt.diy/app/components/chat/chatExportAndImport/*` (interaction pattern)

XClaw implementation instructions:

1. Create template registry service `vibe-game-engine/templates/registry.json` and loader module.
2. Add template metadata UI in dashboard under `studio/template-picker` panel.
3. Implement per-template setup instructions in run workspace before generation.
4. Add fallback asset pack mapping for common failures (missing texture/model/audio).

Definition of done:

1. User can pick a template and get predictable first playable output quickly.

## F4 - Instant Playtest Loop

What users get:

1. One-click "Play Now" from prompt output.
2. Automatic preview refresh when run artifacts update.
3. Quick replay of previous successful runs.

Code to take/adapt:

1. `bolt.diy/app/routes/webcontainer.preview.$id.tsx`
2. `bolt.diy/app/lib/stores/previews.ts`
3. `bolt.diy/app/components/workbench/PortDropdown.tsx`

XClaw implementation instructions:

1. Add preview channel events in dashboard API:
   - `preview_ready`, `preview_refresh_requested`, `preview_failed`.
2. Wire iframe lifecycle in `godot-player.tsx`:
   - clear src, reassign on refresh, show health indicator.
3. Add historical preview dropdown for past runs.
4. Add fallback screenshot or log mode when live preview unavailable.

Definition of done:

1. Users can iterate prompt -> playtest -> tweak prompt without page reload.

## F5 - Collaboration and Share

What users get:

1. Run replay links and downloadable run bundles.
2. Shareable "build card" with prompt, template, and preview.
3. Team handoff path (download source or export package).

Code to take/adapt:

1. `vibesdk/src/hooks/use-github-export.ts` (export workflow pattern)
2. `bolt.diy/app/routes/api.github-*` (integration patterns)
3. `bolt.diy/app/components/chat/chatExportAndImport/*`

XClaw implementation instructions:

1. Add `POST /api/runs/{id}/share` endpoint to generate signed share payload.
2. Add "Share Build" modal in studio.
3. Add "Download Source" and "Download Export Artifact" actions to run cards.
4. Add run replay route that restores timeline/log/preview context.

Definition of done:

1. A user can create, replay, share, and hand off a game from the platform UI.

## F6 - Creator Onboarding and Prompt UX

What users get:

1. Starter prompts and challenge cards.
2. Guided prompt scaffolding for non-technical users.
3. Inline coaching for better prompts.

Code to take/adapt:

1. `vibesdk/samplePrompts.md`
2. `bolt.diy/app/routes/_index.tsx` (landing flow idea)

XClaw implementation instructions:

1. Add starter prompt chips under studio composer.
2. Add mode-specific prompt templates (Racing, FPS, City Builder, Narrative).
3. Add live prompt quality hints before run submission.

Definition of done:

1. New users can produce a playable output without reading docs first.

## F7 - XClaw Native Godot AI Extension

What users get:

1. **Selection-aware scene surgery:** The agent detects the currently selected node/scene, understands the context hierarchy, and injects exactly what is needed (nodes, scripts, signals).
2. **Action plans instead of raw text answers:** The AI output is a strict, deterministic JSON execution schema (`create_node`, `connect_signal`, `set_property`) that eliminates file text-formatting hallucinations.
3. **Safe Auto-Fix & Undo Stack Integration:** Every generation cycle groups its actions using Godot's native `EditorUndoRedoManager`. A developer can press `Ctrl+Z` to perfectly revert a bad AI generation.
4. **Multiple UX Flows:** Ask mode (preview), Agent mode (multi-step plan), Edit-Selection mode (local target), and Repair mode (log-driven fixing) running locally.

Code to take/adapt:

1. `godot-bridge-mcp-public/godot-addon/` (baseline for WebSocket networking into Editor plugins).
2. `EditorInterface` and `EditorUndoRedoManager` APIs in GDScript.

XClaw implementation instructions:

1. Create `vibe-game-engine/godot-addons/xclaw_agentic_engine/` containing a fully typed `EditorPlugin`.
2. Construct the Dock UI using Godot Control nodes for the chat panel, history, and "Agent Plan Preview".
3. Implement an Executor Layer that safely parses the JSON schema from the Python backend and calls native operations (`add_child`, `set_meta`, `ScriptEditor.goto_line`).
4. Implement a Selection Context service that serializes the current tree snapshot to feed the prompt before sending to LangChain.

Definition of done:

1. Developer specifies "Make this top-down enemy chase the player node" while having the Enemy selected. The AI successfully builds the movement loop, adds a NavigationAgent child node, and the user can `Ctrl+Z` the whole operation if they don't like it.

---

## 3) 30-60-90 Day Build Plan

## Days 1-30 (Core Creator Experience)

Deliver:

1. F1 Creator Studio base.
2. F4 Instant Playtest loop.
3. F6 Onboarding prompt UX.

Mandatory outputs:

1. Studio route as default homepage.
2. Playtest works from latest run.
3. Prompt chips and game mode presets live.

## Days 31-60 (Generation Intelligence + Content Scale)

Deliver:

1. F2 Smart Prompt Engine.
2. F3 Template and Asset Universe.

Mandatory outputs:

1. Conversation compactification active.
2. Template picker with metadata and auto-setup.
3. Asset fallback behaviors visible in timeline.

## Days 61-90 (Social and Shipping Layer)

Deliver:

1. F5 Collaboration and Share.
2. Publish flow from dashboard to export artifact handoff.

Mandatory outputs:

1. Replay/share links.
2. Download source and artifact paths.
3. Public demo flow: prompt -> build -> play -> share.

---

## 4) Engineering Task Breakdown (Execution Instructions)

## FE Stream

1. Build studio panels:
   - `studio-layout.tsx` (master split layout)
   - `godot-player.tsx` (preview lifecycle)
   - `prompt-interface.tsx` (mode presets + chips)
   - `console-dock.tsx` (logs)
   - `node-inspector.tsx` (scene metadata)
   - new: `diff-panel.tsx`, `editor-panel.tsx`, `share-modal.tsx`
2. Implement state stores for preview, logs, run timeline.
3. Add routes:
   - `/studio`
   - `/studio/run/[id]`
   - `/studio/share/[id]`

## BE/Orchestration Stream

1. Add context compactifier and selector modules.
2. Extend run model with generation checkpoints and share metadata.
3. Add preview event endpoints and run replay endpoint.
4. Add export/share APIs.

## Content/Template Stream

1. Create template registry and tag taxonomy.
2. Add fallback asset packs and import defaults.
3. Add template onboarding snippets and quick-start prompts.

## Integration Stream

1. Wire frontend stores to run/job APIs.
2. Wire preview iframe to run artifact updates.
3. Ensure replay route restores timeline + logs + preview URL.

---

## 5) Concrete Command Checklist

1. `cd vibe-game-engine/dashboard-nextjs && npm install`
2. `npm run dev` and validate studio route loads.
3. `npm run build` to validate production build.
4. `cd vibe-game-engine && python -m pytest tests -q`
5. Run one full prompt cycle and confirm:
   - run appears in timeline
   - preview updates
   - logs stream
   - share/download actions appear

---

## 6) MVP Success Metrics (Creator-Centric)

1. Time-to-first-playable: <= 5 minutes for starter prompts.
2. Iteration latency: <= 60 seconds from prompt tweak to updated preview.
3. First-session success: >= 70% new users reach playable output.
4. Share conversion: >= 40% successful runs produce replay/share artifact.
5. Return usage: >= 30% users perform >= 3 prompt iterations in a session.

---

## 7) Immediate Next 12 Tasks

1. Implement preview controls in `godot-player.tsx`.
2. Add mode presets and starter chips in `prompt-interface.tsx`.
3. Add real run binding in studio launch action.
4. Add live timeline event store.
5. Add diff panel and file-change list.
6. Add editor panel with selected generated file.
7. Add share modal and run share endpoint.
8. Add replay route with run hydration.
9. Add context compactifier in orchestration layer.
10. Add context selector in orchestration layer.
11. Add template registry JSON + loader.
12. Add fallback asset pack mapping and display in inspector.

This plan is product-first and execution-ready for a dream-game creation platform.
