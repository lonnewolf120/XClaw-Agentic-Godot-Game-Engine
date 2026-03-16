# Token-Optimal Architecture for a Local Agentic Godot Fork

## Token-optimal multi-agent orchestration graph

Your ADR direction (three-tier context + explicit caching + strict tool schemas + deterministic validation) creates the right constraints for a token-optimal graph, because it forces the LLM to operate on *retrieved, bounded slices* rather than full-project dumps. fileciteturn0file0

A token-optimal orchestration graph should explicitly separate **retrieval** from **reasoning** and should treat the LLM as a *late-stage decision layer*. This mirrors how modern AI IDEs reduce “context pollution” by delegating retrieval to specialized mechanisms and reserving expensive reasoning for actual synthesis; for example, entity["company","Windsurf","ai code editor"] documents a dedicated “Fast Context” subagent that automatically triggers for searches, uses restricted tools (grep/read/glob), and performs parallel tool calls to return targeted results while conserving the main agent’s context budget. citeturn4view1turn4view2

### Recommended graph (local-first, token-bounded)

The following graph assumes your core runtime roles remain: Planner, Builder, Validator, Debugger. It also introduces **non-LLM “Context Router + Retriever” nodes** as first-class LangGraph nodes (or equivalent), because this is where most token waste is created or destroyed.

**Stages**
- **Intake**: Receive `{prompt, selection, mode}` from the editor UI. Persist run envelope and freeze “inputs for this attempt.”
- **Scope Context (non-LLM)**: Decide what you *might* need:
  - selection script(s)
  - owning scene(s) + instancing chain
  - relevant engine API slices (node types referenced)
  - recent run history if this is a retry
- **Retrieve Context (non-LLM)**: Fetch bounded slices:
  - lexical candidates + dependency graph walk (Tier 1)
  - vector top-K chunks (Tier 1.5)
  - engine API facts (Tier 2)
  - workspace memories/preferences (Tier 3)
  This node should be parallelized locally the same way Windsurf’s Fast Context emphasizes parallel tool calls and multi-search concurrency to finish retrieval quickly without burning LLM tokens. citeturn4view1
- **Plan (LLM, cheap-ish)**: Planner receives only:
  - user prompt + selection
  - retrieved slices (bounded)
  - “known constraints” (policy + schema)
  Output: a compact “intent plan” (targets, acceptance criteria, risks, context gaps).
- **Build (LLM, schema-bound)**: Builder produces `ActionBatch` with structured output. Keep temperature at/near 0 for tool determinism; this aligns with Vertex guidance that function/tool calls should be low-temperature for reliability. citeturn3view2turn3view1
- **Preview (non-LLM)**: Local diff generator turns ActionBatch into:
  - file-level diff preview
  - touched nodes/resources list
  - risk flags (“script patch touches core loop”, “scene UID edits”, etc.)
- **Approval Gate (UI / policy)**: Default is human approval (Cursor/Windsurf-like). Autopilot can be enabled for low-risk actions only.
- **Execute (non-LLM)**: Apply ActionBatch using a transaction:
  - path sandbox enforcement
  - allowlisted actions only
  - “undo package” recorded for rollback
- **Validate Static (non-LLM)**: Cheap checks (syntax parse, scene format sanity).
- **Validate Headless (non-LLM)**: Run pinned headless checks. Godot’s CLI docs emphasize headless export/CI workflows, and headless is a supported mode for editor-driven automation. citeturn1search7turn1search11
- **Pass → Commit**: Persist new project graph state + chunk index updates.
- **Fail → Debug Summarize (non-LLM)**:
  - extract minimal log snippet window
  - retrieve only the specific script/scene chunks implicated
- **Debug (LLM, schema-bound patch)**: Debugger produces a small patch ActionBatch/DebugPatch.
- **Retry Gate**: bounded retries (your ADR policy). fileciteturn0file0

### Token economics built into the graph

This graph is “token-optimal” because it forces three major savings mechanisms:

- **Explicit and implicit caching of stable prefixes**: Vertex documents that implicit caching is enabled by default and offers a 90% discount on cached tokens; it also documents explicit caching discounts and that explicit caches require storage billing. citeturn3view1turn3view2turn0search8  
- **Cached-token pricing is materially cheaper than uncached input**: Vertex pricing tables explicitly list lower “cached input tokens” pricing tiers (the actual numbers vary by model and context length). citeturn3view0  
- **Specialized retrieval to prevent context pollution**: Windsurf explicitly frames Fast Context as preventing irrelevant code ingestion and conserving the main model’s context budget, including parallel search behaviors and restricted toolsets. citeturn4view1

## Project intelligence graph structure

A project intelligence graph must unify **Godot’s scene/resource structure**, **script relationships**, **asset import state**, and **editor selection context** into a queryable model that supports both:
- retrieval (“what code matters for this edit?”), and
- correctness (“what does this change affect?”).

### Why this should be a graph, not just embeddings

Embeddings answer “which text is semantically similar,” but an agentic engine must also answer deterministic questions like:
- which scene instantiates this node?
- what script is attached to this node?
- what resources does this scene reference?
- what signals connect these nodes?
- what is the dependency blast radius?

Godot’s canonical scene format for text scenes is TSCN, which represents a “single scene tree,” is human-readable, and includes Godot 4 changes like string-based UIDs; the docs also point to the parser implementation location. citeturn3view5turn1search2  
That makes TSCN an ideal backbone for building an explicit scene dependency graph.

### Graph model (property graph)

Define typed nodes and edges (store in SQLite tables; you don’t need Neo4j locally). Recommended node types:

- **Project**
- **SceneFile** (`res://scenes/X.tscn`)
- **NodeInstance** (one per node entry in scene; stable key uses scene UID + node path)
- **ScriptFile** (`res://scripts/Y.gd`)
- **ResourceFile** (textures, fonts, audio, etc.)
- **InputAction** (project input map)
- **Autoload** (singleton)
- **SignalConnection**
- **ExportPreset** (later)

Key edges:

- `PROJECT_HAS_SCENE`
- `SCENE_CONTAINS_NODE`
- `NODE_ATTACHED_SCRIPT`
- `SCENE_REFERENCES_RESOURCE`
- `SCRIPT_PRELOADS_RESOURCE` / `SCRIPT_LOADS_RESOURCE`
- `SCENE_INSTANCES_SCENE` (PackedScene dependency)
- `NODE_EMITS_SIGNAL` / `NODE_LISTENS_SIGNAL` (materialize connections)
- `PROJECT_HAS_AUTOLOAD`
- `PROJECT_HAS_INPUT_ACTION`

### How to populate it efficiently

You have two practical paths:

- **Parse-based**: parse `.tscn` and `.gd` to extract structure. TSCN is explicitly specified and stable in docs, and includes details like “properties equal to default are not stored,” which you must account for. citeturn3view5  
- **Engine-introspection**: when inside the editor, your UI surface can access editor APIs and selected nodes. Godot exposes selection (`EditorSelection.get_selected_nodes()`), which gives you real-time “what the user means by ‘this’.” citeturn4view5turn4view7

A token-optimal system prefers engine-introspection when available (higher fidelity, smaller text), falling back to parsing when running in file-mode or headless.

### Incremental updates and “Cursor-style hashing”

Maintaining this graph efficiently requires incremental updates. entity["company","Cursor","ai code editor"] describes splitting files into syntactic chunks and caching embeddings by chunk content so unchanged chunks don’t require recomputation. citeturn4view0  
Apply the same principle to Godot projects:

- store `file_hash` per file
- store `chunk_hash` per extracted symbol/chunk (function/class or node block)
- update only changed chunks in both the graph and vector store

This keeps indexing cost sublinear as projects grow.

## Local vector DB schema for a Godot agent OS

Your vector store exists to serve “Tier 1.5 retrieval” between lexical search and full reasoning. It must be:
- local-first
- incremental
- tightly coupled to your project graph metadata

### Why SQLite + vector extension is the right baseline

For a local developer tool, embedding storage in the same SQLite DB as RunState and the project graph is operationally attractive (single file, atomic transactions). `sqlite-vec` explicitly positions itself as a small vector search extension that runs anywhere SQLite runs, storing/querying vectors in `vec0` virtual tables with metadata columns. citeturn3view4turn2search2  
`sqlite-vss` is another option based on FAISS, but it introduces heavier build dependencies. citeturn2search7turn2search3

### Embeddings model constraints

Vertex’s text embeddings guide notes `gemini-embedding-001` uses a 3072-dim vector, and it explicitly documents output dimensionality controls that can reduce storage space and downstream compute. citeturn3view3turn2search0  
This is important because local vector DB growth can become real (especially if you embed scene chunks + API docs + script chunks).

### Schema blueprint

Use two layers: metadata tables + vec tables.

**Metadata**
- `chunk`  
  - `chunk_id` (uuid)  
  - `project_id`  
  - `index_type` ENUM(`project`, `engine_api`, `memory`)  
  - `file_path` (nullable for memory)  
  - `symbol_kind` ENUM(`gd_func`, `gd_class`, `tscn_node`, `doc_fact`, `memory_note`)  
  - `symbol_name`  
  - `start_line`, `end_line`  
  - `chunk_hash` (sha256)  
  - `file_hash`  
  - `text_excerpt` (bounded; store full text optionally compressed)  
  - `updated_at`

**Vectors**
- `chunk_vec` (vec0 virtual table)
  - `chunk_id`
  - `embedding` (float vector)
  - `project_id` (partition key)
  - `index_type` (partition key)

**Lexical support**
- `chunk_fts` (FTS5)
  - `chunk_id`
  - `text`
  - `symbol_name`
  - `file_path`

### Retrieval algorithm (token-optimal)

- lexical search first (`chunk_fts`)
- if low confidence, vector top-K from `chunk_vec`
- if still ambiguous, expand using project graph neighborhood:
  - siblings in same scene
  - attached script chunks
  - instancing parent scenes

This mirrors Windsurf’s documented strategy: default context uses current/open file context, plus indexed codebase retrieval for relevant snippets, rather than brute-force sending everything. citeturn4view2turn4view1

## Godot fork modification points that unlock “AI-native” behavior

You can deliver Stage 2 via plugin + daemon, but for your “Godot fork like Cursor forked VS Code” endgame, there are a few high-leverage engine/editor integration points that matter most.

### High-leverage plugin-level hooks (works in a fork too)

- **Selection and state capture**: `EditorSelection.get_selected_nodes()` enables “edit what I selected.” citeturn4view5  
- **Editor surface access**: `EditorInterface` exposes access to editor subsystems like EditorFileSystem and ScriptEditor, enabling deep integration without brittle scraping. citeturn4view7turn1search8  
- **Pre-run build gate**: `EditorPlugin._build()` can abort a run if it returns false; this is a natural place to enforce “pending proposal not applied” or “validation required.” citeturn4view4  
- **Apply pending changes before saves/runs**: `EditorPlugin._apply_changes()` is designed for ensuring pending editor state is flushed; this is useful for “agent applies changes” workflows. citeturn4view4  
- **Undo/redo integration**: Godot explicitly recommends editor plugins use `EditorUndoRedoManager` through `EditorPlugin.get_undo_redo()` to integrate with editor undo history; this is essential for trust in AI edits. citeturn4view6turn1search1

These points let you ship a “Cursor-class” UX surface: propose, preview diff, apply transaction, undo.

### Fork-level modification points that become your moat

A fork becomes valuable when you want AI workflows to be *first-class* rather than “an addon.”

The most important fork-level additions:

- **Native ActionBatch executor in-engine**: move schema execution from Python into Godot C++ (or core editor code) so node/resource edits are applied through the same internal code paths as human edits. This improves correctness, undo atomicity, and performance.
- **Engine API introspection exporter**: Godot’s type database (ClassDB) is the authoritative source of node properties/methods/signals; adding an official “API facts dump” (JSON) avoids scraping docs and reduces token payload sizes.
- **Scene-aware diff builder**: build diffs at the semantic level (node/property/signal), not only file-text. This is the key difference between “AI IDE” text patches and “AI engine” graph patches.
- **Validation signal improvements**: Godot CLI headless workflows can exhibit quirks (including imports and quit timing issues), and the Godot issue tracker is full of headless edge cases. citeturn1search3turn1search19  
  Your current “log-aware validation” approach is consistent with the need to treat output logs as authoritative rather than relying purely on exit codes.

### When a standalone engine becomes necessary

A standalone “vibe engine” only becomes rational if:
- you cannot get stable, atomic semantic diffs and undo integration inside the Godot editor architecture, or
- you cannot expose enough introspection hooks to build a project intelligence graph without brittle parsing.

Given Godot’s existing editor plugin model (selection, undo, build hooks, editor filesystem access), the research evidence strongly suggests the Godot fork path is feasible and should remain the primary trajectory. citeturn4view4turn4view6turn4view7

## Implementation sequence for the next stage

A practical “next stage” implementation sequence that preserves token efficiency:

- Implement the orchestration graph nodes exactly as described: Scope → Retrieve → Plan → Build → Preview → Execute → Validate → Debug loop.
- Materialize the project intelligence graph first for:
  - scenes (`.tscn`) and attached scripts
  - instancing edges
  - resource references
  using the official TSCN spec as the parsing baseline. citeturn3view5
- Introduce sqlite-vec as the first vector store layer (single-file local DB) and drive it with chunk hashing and incremental updates as per Cursor’s described indexing approach. citeturn4view0turn3view4
- Keep explicit Vertex caches small and short-lived unless cache-hit telemetry proves net savings; Vertex explicitly documents default cache TTL (60 minutes) and the presence of storage costs for explicit caches. citeturn3view2turn3view1
- Add the engine/plugin “transaction + undo” integration early via EditorUndoRedoManager; it is the trust anchor that turns AI edits from “dangerous automation” into “reviewable, reversible workflow.” citeturn4view6turn1search1