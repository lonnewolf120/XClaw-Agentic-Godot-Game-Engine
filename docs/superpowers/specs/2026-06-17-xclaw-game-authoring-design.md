# XClaw Game Authoring — Design Spec

**Date:** 2026-06-17
**Status:** Approved (design); implementation pending
**Author:** XClaw engine work (session continuation)
**Scope:** Strengthen `vibe-game-engine/xclaw_cli/` from a logic-script editor into a full game creator with an automated behavioral test gate.

---

## 1. Problem & Context

The working game-gen path is `vibe-game-engine/xclaw_cli/` (a clean single-LLM headless loop;
the legacy `orchestration/` paths are broken and routed around). On 2026-06-15 it was proven
end-to-end **live** and **keyless** via the `claude-code` provider: a "2D platformer double
jump" prompt produced genuinely correct double-jump logic, verified at runtime by an
independent behavioral harness.

**But** that output was *correct logic in an empty void.* Concretely, the `base_2d_platformer`
template is:

- `Player.tscn` = a bare `CharacterBody2D` + script — **no collision shape, no sprite**.
- `Main.tscn` = a `Node2D` with one Player instance — **no level geometry, no goal, no enemies**.
- `project.godot` `main_scene = res://scenes/Main.tscn`; `workspace.py` injects `vibe_core/`
  (VibeEvents / VibeState / VibeTraits / VibeHUD autoloads) at run time.

So there is nothing to *play*: no ground to stand on, no objective, no win/lose, no menus,
no progression. The current `SYSTEM_PROMPT` also forbids `.tscn` edits (correct — hand-edited
scene files are fragile), which means the AI cannot author a playable level the current way.

**Goal:** Let the engine author a **full playable game with progression** — main menu →
multiple levels → score → win + lose → game-over → restart — without hand-editing `.tscn`,
and **prove** it works with an automated behavioral gate (not just "it parsed").

## 2. Goals / Non-Goals

**Goals**
- AI authors a **validated `game_spec.json`** (levels, entities, objectives, progression as data)
  plus focused custom mechanic scripts (`.gd`).
- A human-written, tested-once **`vibe_game/` runtime** turns the GameSpec into a playable game
  (state machine, level builder, entity factory, menus), reusing existing VibeCore autoloads.
- An **agentic multi-step dev loop** drives generation → build → test → fix, keyless.
- An **auto behavioral test gate** reads the same GameSpec to derive and run assertions.
- Each phase ends in a **runnable proof**.

**Non-Goals (this scope)**
- 2D-first. 3D is a later seam (the existing `vibe_entity.gd` is 3D-only and unused here).
- Greybox only — no art/audio generation. Humans polish. (Consistent with existing philosophy.)
- The LLM still never hand-edits `.tscn` (it authors data + `.gd`).
- No save systems, no networking, no settings menus beyond restart/quit.
- "Full game w/ progression" = the vertical slice below scaled with more level *data* + a
  couple of enemy archetypes — **not** arbitrary genres.

## 3. Architecture Overview

Three collaborating parts, with a single shared contract (`game_spec.json`):

```
                 ┌──────────────────────────────────────────────────────┐
   NL prompt ──▶ │  Agentic loop (Python)   [Phase 2]                    │
                 │   draft spec + scripts → build → test → read → fix    │
                 └───────────────┬───────────────────────┬──────────────┘
                                 │ writes                 │ reads results
                                 ▼                        │
                 game_spec.json + scripts/*.gd            │
                                 │                        │
        injected at workspace ───┼────────────────────────┼───────────────
                                 ▼                        ▼
   ┌─────────────────────────────────────┐   ┌──────────────────────────────┐
   │ vibe_game/ runtime (tested once)    │   │ playtest_harness.gd  [Phase 3]│
   │  GameManager (state machine)        │   │  reads game_spec.json →       │
   │  LevelBuilder / EntityFactory       │   │  structural + reachability    │
   │  MenuBuilder   (reuses VibeCore)     │   │  checks → PASS/FAIL + reasons │
   └─────────────────────────────────────┘   └──────────────────────────────┘
                                 │                        │
                                 ▼                        ▼
                         Godot --headless (parse gate, then run)
```

**Why this shape:** LLMs are reliable at emitting *structured data* (positions, counts,
progression) and *small focused scripts*, and unreliable at emitting large correct `.tscn`
trees. So the creative surface is data + small scripts; the structural heavy lifting is
human-written, tested-once code. The test gate reads the *same data* the builder reads, so it
always knows what "done" means for a given game.

**Injection mechanism (grounded in `workspace.py`).** Today `prepare_workspace` copies the
template, then copies `vibe_core_src/` → `project/vibe_core/` and injects the four VibeCore
autoloads into `project.godot`. We extend this:

1. Add a parallel source dir `xclaw_cli/vibe_game_src/` → copied to `project/vibe_game/`.
2. Inject a **`GameManager` autoload** (`*res://vibe_game/game_manager.gd`).
3. Set `run/main_scene` to a tiny **`res://vibe_game/boot.tscn`** (a single `Node2D` running
   `boot.gd`). `boot.gd` hands the root node to `GameManager`, which builds the menu/level
   into the tree.

Because the runtime builds *everything* from the GameSpec (including the player, via
`EntityFactory.spawn_player(spec.player.script)`), it is **template-independent**: the bare
`Player.tscn` / `Main.tscn` are no longer needed. Any 2D-dimension template (or even an empty
one) works, because geometry, collisions, visuals, camera, and HUD are all built at runtime.

## 4. The GameSpec (shared contract)

`game_spec.json` lives at the project root of a run. It is validated **before** any build.

```jsonc
{
  "meta":        { "title": "Greybox Quest", "dimension": "2d", "genre": "platformer" },
  "progression": { "lives": 3, "win": "clear_all_levels" },
  "player":      { "script": "res://scripts/player.gd",
                   "size": { "w": 32, "h": 48 }, "color": "#46c" },
  "levels": [
    {
      "name": "Level 1",
      "bounds":       { "w": 2000, "h": 720 },
      "player_spawn": { "x": 100, "y": 400 },
      "platforms":    [ { "x": 0,    "y": 600, "w": 800, "h": 40 },
                        { "x": 950,  "y": 520, "w": 200, "h": 24 } ],
      "hazards":      [ { "type": "spike", "x": 880, "y": 580, "w": 64, "h": 20 } ],
      "enemies":      [ { "type": "patroller", "x": 1200, "y": 560, "patrol": 200, "speed": 60 } ],
      "collectibles": [ { "type": "coin", "x": 500, "y": 520, "score": 10 } ],
      "goal":         { "x": 1900, "y": 560, "w": 48, "h": 64 },
      "input_plan":   [ {"action":"right","frames":120}, {"action":"jump","frames":1} ]
    }
  ]
}
```

**Field rules / validation** (a Python validator in `xclaw_cli/`, mirrored by a light GDScript
guard in the runtime):
- `meta.dimension` must be `"2d"` for this scope. `genre` is advisory.
- `levels[]` non-empty; each has `player_spawn`, ≥1 `platforms`, and a `goal`.
- **Coordinate convention: Godot 2D, y is DOWN-positive.** Larger `y` = lower on screen
  (ground platforms have larger `y` than the player spawn above them). The example above
  obeys this (`player_spawn.y=400` sits above `platform.y=600`). Both the AI prompt and the
  LevelBuilder assume this; it is a hard rule, not a convention to infer.
- All coordinates inside `bounds`. Numbers finite, sizes > 0.
- `player.script` must be a `res://` path the loop also wrote (cross-checked against writes).
- `hazards.type ∈ {spike, pit}`, `enemies.type ∈ {patroller, chaser}`,
  `collectibles.type ∈ {coin}` — the archetypes the EntityFactory knows. Unknown types fail
  validation (no silent drop).
- `input_plan` is **optional** — a per-level hint the test bot can replay (see §6).

**Input-action contract (critical — locks the AI, runtime, and test bot together).** The
template `project.godot` has **no `[input]` map** — only `[application]` and `[rendering]`.
The proven double-jump worked *only* because it used `ui_accept`, a Godot built-in. Therefore
**player controllers and the test bot use ONLY built-in input actions**: `ui_left`, `ui_right`,
`ui_up`, `ui_down`, `ui_accept` (always defined; mapped to arrows / space / enter). The AI
system prompt forbids inventing custom actions like `"move_right"` (they resolve to nothing and
break both the game *and* the bot silently). Consequence: we inject **zero** input-map config,
and the bot knows exactly which actions to synthesize.

The validator returns structured errors that feed back into the agentic loop, exactly like the
existing headless error markers do.

## 5. The `vibe_game/` Runtime (written once, tested)

Each unit has one purpose, a small interface, and explicit deps. All 2D.

- **`boot.gd` / `boot.tscn`** — main scene. `_ready()` → `GameManager.start(get_tree().root)`.
  *Deps:* GameManager. ~10 lines.

- **`game_manager.gd`** (autoload) — the spine. Owns `enum State { MENU, PLAYING,
  LEVEL_COMPLETE, GAME_OVER, WON }`, `current_level`, and lives/score via VibeState. Loads &
  validates `game_spec.json`. **Owns two container children it creates under `start(root)`'s
  node: a `GameWorld` node (levels build into this) and a `MenuLayer` (`CanvasLayer`, menus
  build into this).** This makes teardown unambiguous: `clear()` frees the one `GameWorld`
  subtree — level nodes are never siblings of the VibeCore autoloads or the boot node.
  Reacts to VibeEvents: `goal_reached` → next level or `WON`; `player_died` → lose a life →
  respawn or `GAME_OVER`. `restart()` → back to level 1, reset VibeState. Drives
  MenuBuilder/LevelBuilder on transitions. **Owns the fall-off-screen lose check**: each frame
  in `PLAYING`, if `player.global_position.y > level.bounds.h + FALL_MARGIN`, emit
  `player_died` (falling is a primary lose condition and needs a clear owner).
  *Interface:* `start(root)`, `goto_level(i)`, `restart()`, `state` (read).
  *Deps:* VibeState, VibeEvents, LevelBuilder, MenuBuilder.

- **`level_builder.gd`** — `build(level: Dictionary, parent: Node) -> Node`. Spawns greybox
  `StaticBody2D` platforms (`CollisionShape2D` + `ColorRect`), `Area2D` hazards/goal/coins
  (with `body_entered` → emit the right VibeEvents), enemies via EntityFactory, positions the
  player at `player_spawn`, attaches a `Camera2D` that follows the player. `clear()` tears down
  the previous level. *Deps:* EntityFactory, VibeEvents.

- **`entity_factory.gd`** — `spawn_player(player_spec) -> CharacterBody2D` (builds body +
  `CollisionShape2D` + `ColorRect`, attaches the AI's `player.script`), and
  `spawn_enemy(enemy_spec) -> Node` for archetypes `patroller` (ping-pong over `patrol` range)
  and `chaser` (move toward player). Enemy behavior uses VibeTraits where natural.
  *Deps:* VibeTraits, VibeEvents.

- **`menu_builder.gd`** — `build_main_menu()` (title + Start/Quit) and `build_game_over(won)`
  (result + Retry/Quit) as a `CanvasLayer`. Buttons call back into GameManager.
  *Deps:* GameManager.

- **Reused as-is:** VibeState (extended with `lives`, `level`, `add_score`), VibeEvents
  (extended with `goal_reached`, `player_died`, `coin_collected`, `level_started`, `game_won`),
  VibeHUD (score/lives), `scout.gd` (introspection, used by the gate).

**AI's remaining surface:** (1) `game_spec.json`; (2) `scripts/player.gd` (the controller);
(3) any *novel* enemy/mechanic script. Everything structural is the tested runtime.

## 6. Auto Test Gate (`playtest_harness.gd`)

Generalized from the proven double-jump harness. Reads the **same** `game_spec.json`, runs the
**real** GameManager headless, and emits a machine-parseable verdict
(`VIBE_TEST RESULT verdict=PASS ...`) that `headless.py` scrapes.

**Structural checks (deterministic):**
- Main menu builds; Start → `PLAYING`.
- Each level builds with a player + a goal + the expected counts of platforms/enemies/hazards/coins.
- HUD present.
- `player_died` decrements lives; reaching 0 → `GAME_OVER`.
- `goal_reached` on a non-final level → next level loads; on the final level → `WON`.
- `GAME_OVER` → `restart()` → back to level 1 with reset state.

**Reachability check (pragmatic, honest):**
- A scripted **bot** drives the player toward each level's `goal` using only the built-in
  actions (`ui_right`/`ui_left`/`ui_accept`, synthesized via `InputEventAction` +
  `Input.parse_input_event`, exactly like the proven double-jump harness). If `input_plan` is
  present, the bot **replays it** first (deterministic); otherwise it falls back to a heuristic
  (move toward `goal.x`; jump on a fixed cadence / when horizontally stuck).
- Reaching the goal within a per-level frame budget ⇒ `reachable = PASS`.

**Honest limit (stated, not buried):** this proves *structural completeness + correct
progression + the mechanic fires + at least one automated path to each goal exists.* It does
**not** prove "fun," nor "winnable by every path," nor balance. Given this project's documented
PoC-claim-vs-reality history, the gate claims exactly that and no more. A green gate means
"structurally complete game that an automated player can progress through," not "good game."

The existing `headless.py` caveat still applies (timeout-as-success on the raw smoke run); the
playtest harness is the *real* signal because it asserts an explicit verdict rather than
relying on absence of crash.

## 7. Agentic Creation Loop (Phase 2)

Upgrade the one-shot `generator` into a deterministic **multi-step tool loop** in Python,
driving the keyless `claude-code` provider (provider-agnostic; not the `claude` CLI's own
agent — we keep control for determinism and reproducibility).

Per step the model returns a JSON action; the Python loop executes it and feeds back the result:
- `write_file(path, content)` / `read_file(path)` / `list_dir()` — sandboxed to the run dir.
- `validate_spec()` — runs the §4 validator → structured errors.
- `run_headless()` — parse/import gate + scout (existing `headless.py`).
- `run_playtest()` — the §6 gate → verdict + per-check reasons.
- `done()` — model asserts completion; loop accepts only if the last `run_playtest()` is green.

Loop: draft `game_spec.json` + `scripts/player.gd` → `validate_spec` → `run_headless` →
`run_playtest` → feed failures back → iterate to green or a step cap. The run bundle records
the full action transcript + final verdict.

## 8. Phasing (each phase ends in a runnable proof)

**Phase 1 — Schema + runtime + 2D vertical slice, NO LLM.**
Build the GameSpec validator, the `vibe_game/` runtime, and the playtest harness. Prove them
with a **hand-authored** `game_spec.json` for a 2-level platformer (menu → 2 greybox levels
with platforms + 1 patroller + spikes + goal → score → lose on fall/enemy → game-over →
restart). **Phase 1 proves the scaffold + gate plumbing — NOT automated platforming.** So the
hand-authored geometry must be clearable by a *trivial* bot: hold `ui_right`, press `ui_accept`
on a fixed cadence. No level requires gap-edge detection or frame-precise jumps (that's Phase 3
work). Design test of the whole reachability model: **if the hand-authored `input_plan` cannot
clear the hand-authored level, stop and rethink reachability before any LLM enters.**
*Acceptance:* one command builds the workspace and the playtest harness prints `verdict=PASS`
for both levels, menu, transitions, and restart — with **zero model variance**.

**Phase 2 — Agentic loop.**
Wire the multi-step tool loop so a natural-language prompt yields `game_spec.json` +
`player.gd`, iterating against the gate, keyless. *Acceptance:* `python -m xclaw_cli --prompt
"..." --provider claude-code` produces a full game whose playtest harness reports `verdict=PASS`.

**Phase 3 — Harden (depth + breadth).**
Stronger bot/`input_plan` reachability, a 2nd enemy archetype (`chaser`), more transition
checks, and a multi-prompt reliability batch reporting a real success rate. *Acceptance:* a
documented batch run with a measured pass rate across N prompts and at least two enemy
archetypes exercised.

## 9. First Vertical Slice (the concrete Phase 1 target)

A 2-level greybox platformer:
- **Menu:** title + Start + Quit.
- **Level 1:** flat ground + 2 floating platforms, 1 spike, 1 patroller, 1 coin, a goal at the
  right edge.
- **Level 2:** a longer run with a pit the player clears with a jump (positioned so a
  fixed-cadence `input_plan` jump clears it — no gap-edge detection needed), 1 patroller, a goal.
- **Score** from coins; **lives = 3**; falling off-screen or touching spike/enemy costs a life
  and respawns; 0 lives → game-over → Retry returns to Level 1.
- Clearing Level 2's goal → "You Win".

This exercises every runtime component and every gate check on real data.

## 10. Risks & Mitigations

- **Reachability is heuristic, not a proof.** *Mitigation:* `input_plan` replay for
  determinism; the gate's claim is explicitly bounded (§6).
- **Runtime is the single point of trust.** *Mitigation:* Phase 1 tests it exhaustively with a
  hand-authored spec before any model variance enters.
- **Godot headless quirks** (exit code unreliable, timeout-as-success). *Mitigation:* the
  playtest asserts an explicit `verdict=` marker; we parse that, not exit codes.
- **Scope creep into "make it fun."** *Mitigation:* §2 non-goals + §6 honest-limit statement.
- **Template coupling.** *Mitigation:* runtime builds everything from the spec, so it is
  template-independent; the bare template just supplies `project.godot` + boot scene.

## 11. File-Level Change Map

- **New:** `xclaw_cli/vibe_game_src/{boot.gd, boot.tscn, game_manager.gd, level_builder.gd,
  entity_factory.gd, menu_builder.gd, playtest_harness.gd}`.
- **New:** `xclaw_cli/gamespec.py` (validator + dataclasses).
- **New (Phase 1 fixture):** a hand-authored `game_spec.json` + `scripts/player.gd` under a
  test run / fixture dir.
- **Edit:** `xclaw_cli/workspace.py` — copy `vibe_game_src/`, inject GameManager autoload, set
  boot main_scene.
- **Edit:** `vibe_core_src/{global_state.gd, events.gd}` — add `lives`/`level`/`add_score` and
  the new signals.
- **Edit (Phase 2):** `xclaw_cli/{generator.py, loop.py}` — multi-step tool loop; new system
  prompt teaching the GameSpec contract.
- **Edit:** `xclaw_cli/headless.py` — a `run_playtest()` entrypoint that injects + runs
  `playtest_harness.gd` and parses the verdict.

---

*Done = a natural-language prompt produces a structurally complete, automatically-verified
playable game with menus, multiple levels, score, and game-over/restart — keyless — and the
green signal comes from an explicit behavioral verdict, not absence of a crash.*
