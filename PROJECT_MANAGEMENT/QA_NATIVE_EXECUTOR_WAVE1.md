# CURRENT STATE & CONTEXT FOR CONTINUATION

**Timestamp:** March 17, 2026
**Current Focus:** Implementing Phase 1 of the Godot Fork Hook Plan (Native Transaction Executor v1).

### What Has Been Done So Far:
1. **Plugin-Level Hooks Established (`godot-addons/xclaw_agentic_engine/plugin.gd`):**
   - Bootstrapped `xclaw_dock.gd` into Godot UI.
   - Built a pre-run build gate (`_build()`) to lock editor compilation when an AI proposal is pending.
   - Created the apply-changes flush point (`_apply_changes()`).
   - Integrated Godot's `EditorUndoRedoManager` to safely wrap AI mutations in atomistic single-step transactions.
2. **Local Python RPC Bridge (`api/plugin_bridge.py` & `xclaw_dock.gd`):**
   - Established a secure, minimal `HTTP POST` channel locally on `127.0.0.1:8000`.
   - Godot securely sends node context via `EditorInterface.get_selection().get_selected_nodes()`.
   - Python returns an atomic `ActionBatch` payload simulating a plan consisting of strict action endpoints.
3. **Native Transaction Executor v1 (`mutation_executor.gd`):**
   - Implemented an internal Godot execution class mapping the **Wave 1 Semantic Actions**: `create_node`, `set_property`, `attach_script`, and `connect_signal`.
   - Before any engine commit, it validates parents, nodes, script cast safety, signal emissions, and parameters internally (e.g., via `ClassDB.class_exists`, `ResourceLoader.exists`).
   - Passes clean Callable `do_methods` and `undo_methods` up to the Plugin's native UndoRedo queue mapping.
4. **Scaffolded Test Directories:**
   - Created `vibe-game-engine/tests/native_transaction_executor_v1/` to hold the subsequent Godot integration tests for these scripts.

### What Remains Undone (The Immediate Next Steps):
We successfully implemented the architectural bridge, but the implementation is only partially proven. We *must now prove* the following via automated/manual testing:
1. **Batch Atomicity:** A mixed-batch failure (e.g., valid > invalid > valid) results in *zero commits* safely.
2. **Undo Fidelity:** Validate the 4 core actions correctly reverse state cleanly using `Ctrl+Z` logic natively in Godot's environment.
3. **Receipt Generation:** Accurately print receipts that log precisely what Godot did locally vs. what it bounced.
4. **Integration Test Generation:** Begin creating GDScript integration tests inside `tests/native_transaction_executor_v1/` mapped to the 20 conditions outlined below. 

***

# Milestone: Native Transaction Executor v1 Verification Matrix 

This is a **meaningful milestone**.
You now have the first genuinely important native loop:
> **Prompt → structured action batch → Godot-side semantic validation → native Undo/Redo execution**

That is the point where the project starts becoming an **AI-native editor workflow**, not just a Python tool driving file patches.

## What is strong here

### 1. The trust boundary is correct
Python is only returning **structured intent**, while Godot is doing:
* validation
* instantiation
* property checks
* script/resource checks
* signal checks
* transaction commit

That is the right split.

### 2. You chose the right Wave 1 actions
These 4 actions are exactly the right starting set:
* `create_node`
* `set_property`
* `attach_script`
* `connect_signal`

They are high-value and still semantically manageable.

### 3. Plugin-side validation is now real
The big improvement is not just Undo/Redo. It is that Godot itself is now judging class validity, node/path existence, property legitimacy, script resource correctness, and signal validity. That reduces the chance of the model inventing nonsense that survives too long.

### 4. Undo/Redo is now on the real side of the boundary
This matters a lot. Native rollback is one of the biggest trust levers for a tool like this.

---

# What is still unproven

## 1. Batch atomicity under mixed actions
You should verify real behavior when a batch contains 3 valid actions and 1 invalid action in the middle. Proof is needed that nothing commits partially, editor state is unchanged, and receipt is accurate.

## 2. Undo fidelity for all 4 actions
Not just “Ctrl+Z works once,” but: apply > undo > redo > save scene > reopen scene > confirm state is correct.

## 3. Selection/path stability
NodePath-based operations often get tricky when nodes are renamed, parents move, scene ownership is odd, or instanced scenes are involved.

## 4. Receipt accuracy
Your receipt system now matters a lot. It should reflect the **actual engine mutations**, not what was merely requested.

---

# Wave 1 Verification Matrix

Use this to verify the 4 native semantic actions. Fits the validation-first, rollback-safe architecture direction. 

---

## 1. Pass criteria

**Apply correctness:** Expected mutation happens, no unexpected side effects, receipt matches actual applied changes.
**Rejection correctness:** Invalid action is rejected before commit, no partial mutation is left behind, receipt/error reflects true failure reason.
**Undo/Redo correctness:** Undo fully restores prior state, redo re-applies exact same state, no duplicate connections / orphan nodes / stale properties.
**Batch atomicity:** If one action in a batch is invalid, **none** of the batch commits.

---

## 2. Test matrix by action

### A. `create_node`
* **A1. valid create:** valid `parent_path`, `node_type`, `node_name`. Expect node, undo removes, redo restores.
* **A2. invalid parent:** nonexistent `parent_path`. Expect fail, no commit.
* **A3. invalid class:** fake `node_type`. Expect fail, no commit.
* **A4. duplicate node name:** create node with name already present. Expect rename or reject.
* **A5. invalid owner/scene context:** node that should not own/save correctly. Expect safe reject.

### B. `set_property`
* **B1. valid property:** valid target, property, compatible value. Expect changes, undo restores.
* **B2. missing property:** fake property name. Expect fail.
* **B3. incompatible value type:** wrong type. Expect fail or safe coercion.
* **B4. wrong target class:** valid name on wrong class. Expect reject.
* **B5. idempotent set:** set to current value. Expect no-op/success.

### C. `attach_script`
* **C1. valid attach:** valid node, `.gd` path. Expect attach, undo removes, redo reattaches.
* **C2. missing script file:** nonexistent file. Expect fail.
* **C3. wrong resource type:** not a script. Expect reject.
* **C4. replace existing script:** node already has script. Expect old preserved for undo.
* **C5. attach to incompatible node:** assumes missing methods. Expect attach succeeds but logs parsing issue.

### D. `connect_signal`
* **D1. valid connection:** valid source, signal, target callable. Expect connection, undo disconnects.
* **D2. missing signal:** nonexistent signal. Expect fail.
* **D3. duplicate connection:** connection exists. Expect reject or skip.
* **D4. invalid target:** target exists, callable invalid. Expect fail.
* **D5. cross-node valid connection:** target/source on different branches. Expect connection.

### M. Mixed batch atomicity
* **M1. all-valid batch:** full commit, full undo, full redo.
* **M2. invalid first action:** zero actions commit.
* **M3. invalid middle action:** zero actions commit. (Key atomicity test)
* **M4. invalid last action:** zero actions commit.
* **M5. conflicting batch:** (e.g. set property on node just failed to create). Deterministic reject.

---

## 3. Recommended Implementation Order (Next Generation Steps)
1. `create_node` GDScript tests
2. `set_property` GDScript tests
3. `attach_script` GDScript tests
4. `connect_signal` GDScript tests
5. mixed batch atomicity
6. receipt accuracy
7. persistence after save/reload