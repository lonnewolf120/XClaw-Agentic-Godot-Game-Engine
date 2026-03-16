# Godot Fork Hook Plan

## Recommendation

Keep this order:

1. **Plugin-level hooks first**
2. **Native editor transaction hooks second**
3. **Engine-level semantic diff/runtime hooks third**

That gives you higher-fidelity benchmarking without forcing an early full fork commitment.

Your current architecture already depends on validation-first execution, rollback, bounded retries, and structured action schemas, which is consistent with the ADRs you’ve logged. 

---

# Godot Fork Hook Plan

## Layer A — Plugin-surface hooks you should use first

These already exist in Godot’s editor API and are the safest path to prototype-native behavior.

### 1. Selection and context capture

Use `EditorSelection` to anchor AI actions to what the developer has actually selected in the editor. That gives you high-fidelity context without broad project dumps.

### 2. Editor surface integration

Use `EditorInterface`/`EditorPlugin` as the shell for:

* chat dock
* diff preview
* proposal/apply actions
* scene/script refresh hooks

Godot’s editor plugin APIs are explicitly designed for editor extensions, and `EditorPlugin` is the correct entry point for tool behavior inside the editor.

### 3. Pre-run build gate

Use `EditorPlugin._build()` as the first native policy checkpoint:

* block run if there is a pending unreviewed proposal
* require validation before play/export
* enforce “apply through transaction only”

This is the cleanest native place to stop unsafe agent edits before runtime.

### 4. Apply-changes flush point

Use `EditorPlugin._apply_changes()` to flush pending editor-side state before any AI-triggered validation or play action. That helps keep editor state and benchmark state aligned.

### 5. Undo/redo integration

Use `EditorUndoRedoManager` through the editor plugin layer as the trust anchor for all AI edits. Godot documents this specifically for editor plugins.

---

## Layer B — First native fork hooks

These are the first C++ entry points I would add once the plugin path proves value.

## 1. Native ActionBatch transaction executor

### Goal

Move from:

* Python executor applying file/text mutations

To:

* native editor transaction executor applying semantic mutations

### Add

A C++ editor service like:

* `EditorAIActions::begin_transaction()`
* `EditorAIActions::apply_action_batch()`
* `EditorAIActions::preview_action_batch()`
* `EditorAIActions::rollback_transaction()`
* `EditorAIActions::commit_transaction()`

### Why

This is the single highest-value fork point.

It gives you:

* atomicity
* true undo/redo integration
* semantic node/property/signal changes
* less fragile file-text patching

---

## 2. SceneTree semantic mutation hooks

### Goal

Make AI edits operate on the same internal pathways as human editor actions.

### Add native mutation wrappers for:

* create node
* remove node
* reparent node
* rename node
* set property
* attach script
* connect signal
* instantiate packed scene

### Why

A game engine is graph-first.
Your executor should not stay text-first longer than necessary.

---

## 3. Semantic diff builder

### Goal

Stop representing changes only as text diffs.

### Add a native diff format like:

* created nodes
* deleted nodes
* property changes
* script attachment changes
* signal connection changes

### Why

For Godot, semantic diffs are far more trustworthy than raw `.tscn` or `.gd` diffs.

The TSCN format is text-based and represents scene trees, which makes it parseable, but native semantic diffs are still the better long-term abstraction for AI workflows.

---

# Layer C — Native validation and intelligence hooks

## 1. Native syntax/compile diagnostics API

### Goal

Stop relying only on headless log parsing for script correctness.

### Add

A callable editor/engine API that returns:

* parse errors
* line/column
* script path
* diagnostic class

### Why

Headless validation is necessary, but not enough.
Native diagnostics are cheaper and more precise.

---

## 2. Native signal graph introspection

### Goal

Expose signal topology directly from the engine/editor.

### Add

An API that can answer:

* what signals this node emits
* what signals are connected
* target callable validity
* signature compatibility

### Why

This will dramatically improve:

* plan validation
* tool scheduling
* debugger targeting

---

## 3. Runtime probe entry point

### Goal

Make your runtime probe a first-class engine feature, not an injected script trick.

### Add

A lightweight probe mode:

* fixed frame count
* error capture
* nodepath resolution failures
* signal/runtime exceptions
* compact structured probe report

### Why

Injected probe scripts are fine now, but a native probe mode will be far more reliable.

---

# Layer D — Project intelligence export hooks

## 1. Engine API fact exporter

### Goal

Stop scraping docs and text whenever possible.

### Add native JSON export for:

* class name
* inheritance
* properties
* methods
* signals
* enums

### Why

Godot’s runtime type system is a better ground truth than docs scraping.
This becomes your canonical Engine API index.

---

## 2. Scene/resource graph exporter

### Goal

Produce project intelligence directly from loaded editor state.

### Add native exporters for:

* scene → nodes
* node → script
* scene → instanced subscene
* scene/resource references
* signal graph
* autoload/input map links

### Why

This reduces parser fragility and improves retrieval quality.

---

# Migration plan

## Phase 1 — Now

Keep:

* plugin UI
* local orchestrator
* Python benchmark harness
* current retrieval and validation stack

Add:

* plugin-level `_build`, `_apply_changes`, selection integration, undo integration

## Phase 2 — First fork

Add:

* native ActionBatch executor
* semantic mutation wrappers
* semantic diff preview

This is the point where Python stops being the true executor.

## Phase 3 — Deep fork

Add:

* native diagnostics
* runtime probe mode
* graph export APIs
* engine fact exporter

This is where the fork becomes your moat.

---

# Decision rule: when to move from plugin to fork

Proceed to C++ fork work only if at least one of these is true:

* plugin path cannot guarantee atomic semantic edits
* undo/redo fidelity is insufficient
* text patching remains a top failure source
* runtime probe needs deeper engine state than plugin APIs expose
* benchmark evidence shows plugin-layer overhead/fragility is the bottleneck

If those are not true yet, stay plugin-first a little longer.

---

# My concrete recommendation

Yes, proceed with the Hook Plan — but start with this exact implementation order:

1. **EditorUndoRedoManager-backed ActionBatch bridge**
2. **SceneTree semantic mutation wrappers**
3. **Semantic diff preview API**
4. **Native diagnostics API**
5. **Runtime probe API**
6. **Project intelligence export APIs**

That is the highest-leverage sequence.

## Bottom line

The fork plan is worth designing now because it directly improves the fidelity of:

* long-session benchmarks
* rollback reliability
* semantic graph mutation
* trust in AI edits

But the correct stance is:

> **plugin-prove first, fork surgically where benchmarks show friction**

That is the most realistic path.

---

## Implementation Order & Decision Rules

**Concrete Implementation Order:**
1. EditorUndoRedoManager-backed ActionBatch bridge
2. SceneTree semantic mutation wrappers
3. Semantic diff preview API
4. Native diagnostics API
5. Runtime probe API
6. Project intelligence export APIs

**Decision Rule for Forking:**
Proceed to C++ fork work (Layer B+) ONLY if at least one of these is true:
*   Plugin path cannot guarantee atomic semantic edits.
*   Undo/redo fidelity is insufficient.
*   Text patching remains a top failure source.
*   Runtime probe needs deeper engine state than plugin APIs expose.
*   Benchmark evidence shows plugin-layer overhead/fragility is the bottleneck.