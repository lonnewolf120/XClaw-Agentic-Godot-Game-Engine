@tool
extends RefCounted

var plugin: EditorPlugin

func _init(p_plugin: EditorPlugin):
    plugin = p_plugin

# Expected action schema:
# {
#   "type": "create_node" | "set_property" | "attach_script" | "connect_signal",
#   "params": { ... }
# }
func validate_and_build_batch(actions: Array) -> Dictionary:
    var callables_batch = []
    var nodes_touched = []
    var files_touched = []
    
    var current_scene = EditorInterface.get_edited_scene_root()
    if not current_scene:
        return {"status": "error", "error": "No scene currently open in editor."}
        
    for action in actions:
        var type = action.get("type", "")
        var params = action.get("params", {})
        
        var result = {}
        if type == "create_node":
            result = _validate_create_node(current_scene, params)
        elif type == "set_property":
            result = _validate_set_property(current_scene, params)
        elif type == "attach_script":
            result = _validate_attach_script(current_scene, params)
        elif type == "connect_signal":
            result = _validate_connect_signal(current_scene, params)
        else:
            return {"status": "error", "error": "Unknown action type: " + str(type)}
            
        if result.get("status") == "error":
            return {"status": "error", "error": result.get("error"), "failed_action": action}
            
        callables_batch.append(result.get("transaction_pair"))
        if result.has("node_touched"):
            nodes_touched.append(result["node_touched"])
        if result.has("file_touched"):
            files_touched.append(result["file_touched"])
            
    return {
        "status": "success",
        "batch": callables_batch,
        "nodes_touched": nodes_touched,
        "files_touched": files_touched,
        "actions_executed": actions.size()
    }

# ==============================================================================
# Mutator Validators and Builders
# ==============================================================================

# Params: parent_path, node_type, node_name
func _validate_create_node(scene_root: Node, params: Dictionary) -> Dictionary:
    var parent_path = params.get("parent_path", "")
    var node_type = params.get("node_type", "Node")
    var node_name = params.get("node_name", "NewNode")
    
    var parent = null
    if parent_path == "." or parent_path == "":
        parent = scene_root
    else:
        parent = scene_root.get_node_or_null(parent_path)
        
    if not parent:
        return {"status": "error", "error": "Parent node not found: " + str(parent_path)}
        
    if not ClassDB.class_exists(node_type):
        return {"status": "error", "error": "Invalid node class: " + str(node_type)}
        
    var new_node = ClassDB.instantiate(node_type)
    new_node.name = node_name
    
    # We must preserve the transaction pairing safely
    var do_func = Callable(self, "_do_create_node").bind(parent, new_node, scene_root)
    var undo_func = Callable(self, "_undo_create_node").bind(parent, new_node)
    
    return {
        "status": "success",
        "transaction_pair": { "do_method": do_func, "undo_method": undo_func, "do_reference": new_node },
        "node_touched": str(parent.get_path()) + "/" + node_name
    }

func _do_create_node(parent: Node, new_node: Node, owner_node: Node) -> void:
    if not new_node.is_inside_tree():
        parent.add_child(new_node)
    if new_node.owner == null:
        new_node.owner = owner_node

func _undo_create_node(parent: Node, new_node: Node) -> void:
    if new_node.is_inside_tree():
        parent.remove_child(new_node)

# Params: node_path, property_name, new_value
func _validate_set_property(scene_root: Node, params: Dictionary) -> Dictionary:
    var node_path = params.get("node_path", "")
    var property_name = params.get("property_name", "")
    var new_value = params.get("new_value", params.get("value", null))
    
    var node = scene_root if (node_path == "." or node_path == "") else scene_root.get_node_or_null(node_path)
    
    if not node:
        return {"status": "error", "error": "Node not found: " + str(node_path)}
        
    # Check if property exists. get() returning null could just be value is null, so check via get_property_list
    var prop_exists = false
    for p in node.get_property_list():
        if p["name"] == property_name:
            prop_exists = true
            break
            
    if not prop_exists:
        return {"status": "error", "error": "Property '" + property_name + "' not found on node."}
        
    var old_value = node.get(property_name)
    
    # Use Godot's UndoRedo property system directly where possible
    return {
        "status": "success",
        "transaction_pair": { 
            "node": node,
            "property": property_name,
            "do_property": new_value,
            "undo_property": old_value
        },
        "node_touched": str(node.get_path())
    }

# Params: node_path, script_path
func _validate_attach_script(scene_root: Node, params: Dictionary) -> Dictionary:
    var node_path = params.get("node_path", "")
    var script_path = params.get("script_path", "")
    
    var node = scene_root if (node_path == "." or node_path == "") else scene_root.get_node_or_null(node_path)
    if not node:
        return {"status": "error", "error": "Node not found for script attach."}
        
    if not ResourceLoader.exists(script_path):
        return {"status": "error", "error": "Script resource does not exist at path: " + script_path}
        
    var new_script = ResourceLoader.load(script_path)
    if not new_script is Script:
        return {"status": "error", "error": "Resource is not a script: " + script_path}
        
    var old_script = node.get_script()
    
    return {
        "status": "success",
        "transaction_pair": {
            "node": node,
            "property": "script",
            "do_property": new_script,
            "undo_property": old_script
        },
        "node_touched": str(node.get_path()),
        "file_touched": script_path
    }

# Params: source_node_path, signal_name, target_node_path, method_name
func _validate_connect_signal(scene_root: Node, params: Dictionary) -> Dictionary:
    var source_path = params.get("source_node_path", params.get("source_node", ""))
    var signal_name = params.get("signal_name", "")
    var target_path = params.get("target_node_path", params.get("target_node", ""))
    var method_name = params.get("method_name", "")
    
    var source = scene_root if source_path in ["", "."] else scene_root.get_node_or_null(source_path)
    var target = scene_root if target_path in ["", "."] else scene_root.get_node_or_null(target_path)
    
    if not source:
        return {"status": "error", "error": "Source node not found"}
    if not target:
        return {"status": "error", "error": "Target node not found"}
        
    if not source.has_signal(signal_name):
        return {"status": "error", "error": "Signal '" + signal_name + "' does not exist on source."}
        
    # Validation constraint: We do not check target.has_method strictly because scripts might be attached in the same batch,
    # but we can check if it's already connected.
    var conn_callable = Callable(target, method_name)
    var is_connected = source.is_connected(signal_name, conn_callable)
    
    if is_connected:
        return {"status": "error", "error": "Signal is already connected"}
        
    var do_func = Callable(self, "_do_connect_signal").bind(source, signal_name, target, method_name)
    var undo_func = Callable(self, "_undo_connect_signal").bind(source, signal_name, target, method_name)
    
    return {
        "status": "success",
        "transaction_pair": { "do_method": do_func, "undo_method": undo_func },
        "node_touched": str(source.get_path())
    }

func _do_connect_signal(source: Node, sig_name: String, target: Node, method_name: String) -> void:
    var c = Callable(target, method_name)
    # Using PERSIST flag so the connection saves to the packed scene
    if not source.is_connected(sig_name, c):
        source.connect(sig_name, c, Object.CONNECT_PERSIST)

func _undo_connect_signal(source: Node, sig_name: String, target: Node, method_name: String) -> void:
    var c = Callable(target, method_name)
    if source.is_connected(sig_name, c):
        source.disconnect(sig_name, c)

