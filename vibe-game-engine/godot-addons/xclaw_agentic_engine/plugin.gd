@tool
extends EditorPlugin

var dock: Control
var has_pending_proposals: bool = false

func _enter_tree() -> void:
    # Initialization of the plugin goes here.
    # Instantiate the dock control
    dock = preload("res://addons/xclaw_agentic_engine/xclaw_dock.tscn").instantiate()
    
    # Pass reference to plugin to dock
    if dock.has_method("set_plugin"):
        dock.set_plugin(self)
        
    # Add the loaded scene to the bottom/right dock
    add_control_to_dock(DOCK_SLOT_RIGHT_BL, dock)


func _exit_tree() -> void:
    # Clean-up of the plugin goes here.
    if dock:
        remove_control_from_docks(dock)
        dock.queue_free()

# ==============================================================================
# Phase 1: Layer A - Plugin-Surface Hooks
# ==============================================================================

# 3. Pre-run build gate
func _build() -> bool:
    # Block run if there is a pending unreviewed proposal
    if has_pending_proposals:
        printerr("[XClaw Agentic Engine] Blocked Run: You have pending unreviewed AI proposals. Please accept or reject them first.")
        return false
    return true

# 4. Apply-changes flush point
func _apply_changes() -> void:
    # Flush pending editor-side state before any AI-triggered validation or play action
    if dock and dock.has_method("flush_pending_changes"):
        dock.flush_pending_changes()

# 5. Undo/redo integration
func execute_ai_action_batch(action_name: String, batch: Array) -> void:
    var undo_redo = get_undo_redo()
    if not undo_redo:
        printerr("[XClaw] No UndoRedo manager available.")
        return
        
    undo_redo.create_action(action_name)
    
    for pair in batch:
        if pair.has("do_method") and pair["do_method"] is Callable:
            var do_callable: Callable = pair["do_method"]
            var do_args: Array = [do_callable.get_object(), do_callable.get_method()]
            do_args.append_array(do_callable.get_bound_arguments())
            undo_redo.add_do_method.callv(do_args)
        if pair.has("do_property") and pair.has("node") and pair.has("property"):
            undo_redo.add_do_property(pair["node"], pair["property"], pair["do_property"])
            
        if pair.has("undo_method") and pair["undo_method"] is Callable:
            var undo_callable: Callable = pair["undo_method"]
            var undo_args: Array = [undo_callable.get_object(), undo_callable.get_method()]
            undo_args.append_array(undo_callable.get_bound_arguments())
            undo_redo.add_undo_method.callv(undo_args)
        if pair.has("undo_property") and pair.has("node") and pair.has("property"):
            undo_redo.add_undo_property(pair["node"], pair["property"], pair["undo_property"])
            
        if pair.has("do_reference"):
            undo_redo.add_do_reference(pair["do_reference"])
        if pair.has("undo_reference"):
            undo_redo.add_undo_reference(pair["undo_reference"])
            
    undo_redo.commit_action()

# 1. Selection and context capture
func get_ai_context_from_selection() -> Dictionary:
    var interface = get_editor_interface()
    var selection = interface.get_selection().get_selected_nodes()
    
    var context = {
        "selected_nodes": [],
        "active_scene": ""
    }
    
    var root = interface.get_edited_scene_root()
    if root:
        context["active_scene"] = root.scene_file_path
        
    for node in selection:
        var node_info = {
            "name": node.name,
            "class": node.get_class(),
            "path": str(root.get_path_to(node)) if root else str(node.get_path()),
            "script": ""
        }
        var script = node.get_script()
        if script:
            node_info["script"] = script.resource_path
            
        context["selected_nodes"].append(node_info)
        
    return context


