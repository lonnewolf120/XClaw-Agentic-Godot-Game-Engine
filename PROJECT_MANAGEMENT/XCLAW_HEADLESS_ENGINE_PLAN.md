# XClaw Headless Engine — Implementation Plan (v1)

**Created:** 2026-05-30
**Owner:** (you) + Claude
**Direction:** A CLI/headless, single-LLM, text-editing game generator for Godot 4.6. Decided over prior design discussion; pressure-tested by advisor.

---

## Lead assumption (VETOABLE — say so if you disagree)

**Build fresh and route around the broken legacy orchestration.** We do NOT revive
`scripts/create_game_from_prompt.py` / `orchestration/game_creation.py`. That path is
a trap: it drags in the committed validation-schema split (`game_creation`, `nodes/debug`,
`runtime_probe`, `tests`) AND even when fixed, `agents/coding_agent.generate_patches` is a
stub that writes a fixed `main.gd` — so you'd get a working skeleton with no real generation.

Fixing the legacy orchestration is a **separate optional track, not part of v1.**

## What "complete v1" means (definition of done)

> Natural-language prompt → LLM edits a **valid Kenney Starter-Kit template** as text
> (scripts first) → passes **headless Godot check**, self-correcting from real parse/script
> errors (retry cap N) → **exports a runnable artifact**.

## Architecture (one LLM, one tool loop, one headless gate)

```
prompt + project context (file tree + relevant file slices)
  → LLM emits tool calls: list_dir / read_file / write_file   [.gd as text]
  → apply full-file writes to an isolated copy of a Kenney template
  → godot --headless --path <ws> --import --check-only  (+ bounded smoke run)
  → parse errors → feed back to LLM → retry (cap N)
  → exporter_agent → runnable artifact
```

## Reuse (already aligned to current `contracts/validation.py`)

- `validation/headless_runner.py` — emits a correct `ValidationReport`; scrapes
  `Parse Error:` / `SCRIPT ERROR:` / `USER ERROR:` inline (so we don't need
  `tools/log_parser.py`, and its `\b` regex bug is off our path).
- `agents/exporter_agent.py` — export + checksum.
- `tools/template_catalog.py` — prompt→template scoring/selection.
- `contracts/` — strict Pydantic models.
- (optional) `store/run_store.py` (SQLite run log), `agents/llm_provider.py` (Gemini/CLI seam,
  cleaner than the Vertex `llm_manager`).

## Do NOT touch / fix (out of v1 scope)

`orchestration/game_creation.py`, `orchestration/nodes/debug.py`, `validation/runtime_probe.py`,
`orchestrator/graph.py` (SkeletonGraph), planner/coordinator/builder/coding_agent stubs,
`generators/*_template.py` (the `def`-instead-of-`func` scaffolds), `tests/`.

## Hard constraints / explicit non-goals for v1

- **Script edits against prebuilt template scenes only.** `.tscn` has `load_steps` counts,
  `ext_resource` id wiring, and node-path coupling that LLMs corrupt. Do scene changes in code
  (`_ready()` spawns) — NOT by rewriting `.tscn`. Freehand `.tscn`/`.tres` authoring is a later,
  gated phase.
- **No multi-agent ceremony.** One model, one loop. Add retrieval/planning only when the simple
  loop provably fails on a real task (documented decision point, not a default).
- **No asset generation.** Visual/audio stays human/tool-driven (keep referencing local Kenney
  assets, as `tools/asset_resolver.py` already does). The `sprite-sheet-creator/` tool stays separate.
- **No live editor bridge** (the `xclaw_agentic_engine` plugin path) in v1.

## New module location

`vibe-game-engine/xclaw_cli/` — self-contained package. Entry point `python -m xclaw_cli ...`.

---

## Phases (each gated on observable command output — a tracer bullet, not horizontal layers)

### Phase 0 — Environment proof (DO FIRST, before building anything)
Verify the command the whole thesis rests on actually works here.
- Locate a real Godot 4.6 binary (hardcoded ref was `D:\Software\Godot\Godot.exe`).
- Run `godot --headless --path <Starter-Kit-3D-Platformer> --import` then `--check-only`.
- **Gate:** clean exit code + parseable stdout. If Windows headless is flaky → switch to the
  Docker path (`robpc/godot-headless` / `docker-godot-headless/`). This is the evidence-based
  answer to the Linux question.

### Phase 1 — Tracer bullet (thinnest full-loop slice)
Hardcode everything except the apply→check loop.
- Copy Starter-Kit-3D-Platformer to an isolated workspace.
- Make ONE bounded, known-good edit in code (e.g. raise `player.gd` `jump_strength`).
- Apply → headless check → confirm PASS.
- **Gate:** loop runs end-to-end and produces a modified, still-valid project. No LLM yet.

### Phase 2 — Self-correction loop
- Inject a deliberate parse error; confirm the loop *reads the headless error* and a
  fix step removes it; enforce retry cap N then stop.
- **Gate:** loop converges from an injected `Parse Error:` to a passing check within N tries.

### Phase 3 — Real LLM in the loop
- Wire `agents/llm_provider.py` (Gemini key) and/or local Ollama as the generator.
- Implement the tool-call loop (`list_dir`/`read_file`/`write_file`), borrowing the *pattern*
  from `godot-ai-autonomous-agent/ai_tool_manager.gd` but headless + full-file writes.
- Context = file tree + relevant file slices (bounded).
- **Gate:** an arbitrary *script-level* NL prompt yields a valid project that passes headless check.

### Phase 4 — Template selection + run isolation + logging
- Use `tools/template_catalog.py` to pick the template from the prompt.
- Isolated `runs/<id>/` workspace; write a run bundle (reuse `store/run_store.py` or JSON).
- **Gate:** prompt selects the right template; isolated run dir + bundle written.

### Phase 5 — Export
- Reuse `agents/exporter_agent.py` → runnable artifact (Windows preset / Docker).
- **Gate:** produces a `.exe`/`.pck` that launches.

### Phase 6 — DEFERRED (only after 1–5 are solid)
Freehand `.tscn`/`.tres` editing, richer scene generation, optional retrieval/planning,
optional legacy-orchestration repair.

---

## Progress log
- 2026-05-30: Plan created. Starting Phase 0.
- 2026-05-30: **Phase 0 PROVEN (Windows-native, no Docker needed for v1).** Godot 4.6.1 at
  `D:\Software\Godot\Godot.exe` (the `_console.exe` wrapper is broken — looks for a missing
  sibling). `--headless --path <ws> --import` imports + exits 0. `--headless --path <ws> --editor
  --quit` loads project & scripts: clean = no error lines; injected `func broken(:` →
  `SCRIPT ERROR: Parse Error: Expected parameter name.` + `Failed to load script ...`.
  KEY: **exit code stays 0 even on parse error → the gate must scrape stdout/stderr** for
  `SCRIPT ERROR:` / `Parse Error:` / `USER ERROR:` / `Failed to load script`. Linux/Docker only
  needed later for reproducible CI/export, not the core loop.
- 2026-05-30: **Phase 1 PASS** — `xclaw_cli/` foundation built (`config`, `headless.GodotHeadless`,
  `workspace`, `edits`, `loop`). `phase1_tracer` proves via Python subprocess: import OK, valid
  edit passes, injected parse error in a *referenced* script (player.gd) is caught.
- 2026-05-30: **Gate decision (important).** The gate is `--headless --editor --quit` (faithful
  project context: autoloads registered, scripts loaded as the game uses them). Tried a bare
  `--script` validator that force-loads every `.gd` to also catch ORPHAN scripts — REJECTED: in a
  bare SceneTree, autoloads aren't registered, so every script referencing the `Audio` autoload
  false-fails ("Identifier not found: Audio"). v1 contract: a script is validated when it's wired
  into a scene (which is also when it affects the game); unwired orphans are intentionally not gated.
- 2026-05-30: **Phase 2 PASS** — self-correction loop (`loop.run_loop`) converges from a real
  headless error and respects the retry cap (test mutates the *referenced* player.gd).
- 2026-05-30: **Phase 3 PASS** — real LLM tool loop. `llm.py` is a multi-provider abstraction
  (`anthropic` [default], `gemini`, `ollama`, `fake`); `generator.LLMGenerator` builds bounded
  context (file tree + all `.gd` contents + prior errors) → one model call per attempt →
  full-file writes. `engine.generate()` orchestrates + writes `run_bundle.json`. CLI:
  `python -m xclaw_cli --prompt "..." [--provider anthropic] [--model ...]`.
  - **Claude provider** added via `/claude-api` skill (official `anthropic` SDK, installed
    0.105.2): default `claude-opus-4-8`, `thinking={"type":"adaptive"}`, structured-output
    `json_schema` for the `{summary, writes[]}` shape, prompt-cached system block. Pass
    `--model claude-haiku-4-5` for cheaper runs (cost is the user's call).
  - Gemini reached the API correctly but the key has **0 free-tier quota** for gemini-2.0-flash
    (429 RESOURCE_EXHAUSTED, limit 0) — integration is correct, key lacks quota.
  - Verified WITHOUT a live key: `phase3_fake_test` (deterministic full pipeline) and
    `phase3_anthropic_shape_test` (mocks the SDK, asserts exact request shape + drives loop/gate
    to a passing edit) both PASS; CLI no-key path errors cleanly (exit 2, provider-aware tip).
  - **To run live:** `set ANTHROPIC_API_KEY=...` (or `ant auth login`), then the CLI command above.
  - Remaining: Phase 4 (template selection via `tools/template_catalog.py` + run isolation/logging)
    and Phase 5 (export via `agents/exporter_agent.py`).
- 2026-05-31: **SDK shape verified against the *installed* anthropic 0.105.2** (closing the
  one gap the mock couldn't): grepped the package source — `thinking={"type":"adaptive"}`
  (`ThinkingConfigAdaptiveParam`), `output_config={"format":{"type":"json_schema","schema":...}}`
  (`OutputConfigParam.format: JSONOutputFormatParam`), all in the **non-beta** `messages.create`.
  The mock shape test was circular (asserted the kwargs we chose); the installed-source grep is
  ground truth. Only the live network round-trip remains user-blocked (needs `ANTHROPIC_API_KEY`).
  NOTE: the engine runs under `vibe-game-engine/.venv` (Python 3.10), where `anthropic` 0.105.2
  is installed — NOT the system Python.
- 2026-05-31: **Phase 4 PASS** — template selection + run isolation + bundle.
  - **Proof-driven candidate set:** ran the headless gate on the non-Kenney scaffolds
    (`base_2d_platformer`, `topdown_shooter`, `endless_runner`, `micro_fps_3d`, `platformer_base`)
    — **all PASS**. The "broken `def`-vs-`func`" issue is in `generators/*_template.py` (codegen),
    NOT these checked-in template dirs. So selection draws from the full valid set; without the
    2D scaffolds a "2D platformer" prompt would have no valid target (all 5 Kenney kits are 3D).
  - **Deliberate deviation from the reuse list:** built self-contained `xclaw_cli/catalog.py`
    instead of reusing `tools/template_catalog.select_template_from_prompt`. That fn returns
    `../templates/X` path strings (two path styles in one catalog) our single `TEMPLATES_DIR`
    can't cleanly validate or feed to `prepare_workspace`. We reuse the *data*
    (`config/template_catalog.json`), normalize by basename, keep only entries with a valid
    `project.godot` under `TEMPLATES_DIR`, and score (dimension + tag overlap + light desc
    overlap). Scoring guards: bare `2d`/`3d` tags skipped so they don't double-count with the
    dimension score (the bug that would let `micro_fps_3d` beat Kenney FPS); squashed-substring
    tag match (`top-down`~`topdown`, `bullet`~`bullets`, `first person shooter`) with a length
    guard so short tags (`car`) can't false-match inside words (`scary`); Kenney kits win ties.
  - **Baseline gate:** `engine.generate` headless-checks the *selected pristine* template before
    the LLM loop; on failure falls back to `Starter-Kit-3D-Platformer` (turns "is this template
    valid?" into the existing gate, not a hardcoded allowlist). Import is done once for the
    baseline, then `run_loop(import_first=False)`.
  - **Run bundle** now records `template`, `requested_template`, `selection_reason`,
    `baseline_ok`, `fallback_from`. CLI `--template` is now optional (auto-select when omitted).
  - Verified (no key/network): `phase4_selection_test` (8 NL prompts → expected folder, incl. the
    FPS tag-collision and a 2D-never-resolves-to-3D guard) and `phase4_engine_test` (mocked SDK +
    **real Godot**: auto-select → baseline gate → loop → bundle with selection metadata, isolated
    `runs/<id>/`). Both PASS; phase3_fake + phase3_anthropic_shape still PASS (no regression).
  - Remaining: Phase 5 (export via `agents/exporter_agent.py`).
