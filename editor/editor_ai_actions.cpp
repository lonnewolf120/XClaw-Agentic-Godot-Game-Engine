/**************************************************************************/
/*  editor_ai_actions.cpp                                                 */
/**************************************************************************/
/*                         This file is part of:                          */
/*                             GODOT ENGINE                               */
/*                        https://godotengine.org                         */
/**************************************************************************/

#include "editor_ai_actions.h"
#include "editor/editor_undo_redo_manager.h"
#include "editor/editor_node.h"
#include "editor/editor_interface.h"
#include "scene/main/node.h"

EditorAIActions *EditorAIActions::singleton = nullptr;

EditorAIActions *EditorAIActions::get_singleton() {
	return singleton;
}

void EditorAIActions::_bind_methods() {
	ClassDB::bind_method(D_METHOD("begin_transaction", "name"), &EditorAIActions::begin_transaction);
	ClassDB::bind_method(D_METHOD("apply_action_batch", "batch"), &EditorAIActions::apply_action_batch);
	ClassDB::bind_method(D_METHOD("preview_action_batch", "batch"), &EditorAIActions::preview_action_batch);
	ClassDB::bind_method(D_METHOD("rollback_transaction"), &EditorAIActions::rollback_transaction);
	ClassDB::bind_method(D_METHOD("commit_transaction"), &EditorAIActions::commit_transaction);

	ClassDB::bind_method(D_METHOD("create_node", "parent_path", "type", "name"), &EditorAIActions::create_node);
	ClassDB::bind_method(D_METHOD("remove_node", "node_path"), &EditorAIActions::remove_node);
	ClassDB::bind_method(D_METHOD("reparent_node", "node_path", "new_parent_path"), &EditorAIActions::reparent_node);
	ClassDB::bind_method(D_METHOD("rename_node", "node_path", "new_name"), &EditorAIActions::rename_node);
	ClassDB::bind_method(D_METHOD("set_property", "node_path", "property", "value"), &EditorAIActions::set_property);
	ClassDB::bind_method(D_METHOD("attach_script", "node_path", "script_path"), &EditorAIActions::attach_script);
	ClassDB::bind_method(D_METHOD("connect_signal", "source_path", "signal", "target_path", "method"), &EditorAIActions::connect_signal);
	ClassDB::bind_method(D_METHOD("instantiate_packed_scene", "parent_path", "scene_path", "name"), &EditorAIActions::instantiate_packed_scene);

	ClassDB::bind_method(D_METHOD("get_script_diagnostics", "script_path"), &EditorAIActions::get_script_diagnostics);
	ClassDB::bind_method(D_METHOD("run_runtime_probe", "frame_count"), &EditorAIActions::run_runtime_probe);
}

void EditorAIActions::begin_transaction(const String &p_name) {
	if (EditorUndoRedoManager::get_singleton()) {
		EditorUndoRedoManager::get_singleton()->create_action(p_name);
	}
}

Array EditorAIActions::apply_action_batch(const Array &p_batch) {
    Array results;
    begin_transaction("AI Batch Apply");

    bool batch_failed = false;

    for (int i = 0; i < p_batch.size(); i++) {
        Dictionary action = p_batch[i];
        String action_name = action.get("action", "");
        Dictionary res;

        if (action_name == "create_node") {
            res = create_node(action.get("parent_path", ""), action.get("type", ""), action.get("name", ""));
        } else if (action_name == "remove_node") {
            res = remove_node(action.get("node_path", ""));
        } else if (action_name == "rename_node") {
            res = rename_node(action.get("node_path", ""), action.get("new_name", ""));
        } else if (action_name == "set_property") {
            res = set_property(action.get("node_path", ""), action.get("property", ""), action.get("value", Variant()));
        } else {
            res["status"] = "error";
            res["phase"] = "validation";
            res["error_code"] = "UNKNOWN_ACTION";
            res["error"] = vformat("Unknown action: %s", action_name);
        }

        res["action_index"] = i;
        res["action_type"] = action_name;
        
        if (String(res.get("status", "")) == "success") {
            res["phase"] = "execution";
        }

        results.push_back(res);

        if (String(res.get("status", "error")) == "error") {
            batch_failed = true;
            break;
        }
    }

    if (batch_failed) {
        rollback_transaction();
        for (int i = 0; i < results.size(); i++) {
            Dictionary r = results[i];
            r["committed"] = false;
            // Mark successful previous tasks as rolled back
            if (String(r.get("status", "")) == "success") {
                r["rolled_back"] = true;
            }
            results[i] = r;
        }
    } else {
        commit_transaction();
        for (int i = 0; i < results.size(); i++) {
            Dictionary r = results[i];
            r["committed"] = true;
            results[i] = r;
        }
    }

    return results;
}

Array EditorAIActions::preview_action_batch(const Array &p_batch) {
    Array results;
    begin_transaction("AI Batch Preview");
    
    bool batch_failed = false;

    for (int i = 0; i < p_batch.size(); i++) {
        Dictionary action = p_batch[i];
        String action_name = action.get("action", "");
        Dictionary res;

        if (action_name == "create_node") res = create_node(action.get("parent_path", ""), action.get("type", ""), action.get("name", ""));
        else if (action_name == "remove_node") res = remove_node(action.get("node_path", ""));
        else if (action_name == "rename_node") res = rename_node(action.get("node_path", ""), action.get("new_name", ""));
        else if (action_name == "set_property") res = set_property(action.get("node_path", ""), action.get("property", ""), action.get("value", Variant()));
        else { res["status"] = "error"; res["error_code"] = "UNKNOWN_ACTION"; res["phase"] = "validation"; } 

        res["action_index"] = i;
        res["action_type"] = action_name;
        res["preview_only"] = true;
        
        if (String(res.get("status", "")) == "success") {
            res["phase"] = "execution";
        }

        results.push_back(res);

        if (String(res.get("status", "error")) == "error") {
            batch_failed = true;
            break;
        }
    }
    
    rollback_transaction();

    for (int i = 0; i < results.size(); i++) {
        Dictionary r = results[i];
        r["committed"] = false;
        if (String(r.get("status", "")) == "success") {
            r["rolled_back"] = true; 
        }
        results[i] = r;
    }

    return results;
}

void EditorAIActions::rollback_transaction() {
    if (EditorUndoRedoManager *ur = EditorUndoRedoManager::get_singleton()) {
        ur->commit_action(true);
        ur->undo();
    }
}

void EditorAIActions::commit_transaction() {
	if (EditorUndoRedoManager::get_singleton()) {
		EditorUndoRedoManager::get_singleton()->commit_action();
	}
}

Dictionary EditorAIActions::create_node(const String &p_parent_path, const String &p_type, const String &p_name) {
	Dictionary result;

	if (!EditorInterface::get_singleton() || !EditorNode::get_singleton()) {
Dictionary err;
err["error_code"] = "NO_EDITOR_NODE";
err["error_string"] = "EditorNode is not available (headless environment).";
        err["environment"] = "headless";
        err["editor_services_available"] = false;
        err["phase"] = "validation";
return err;
}
Node *root = EditorInterface::get_singleton()->get_edited_scene_root();
	if (!root) {
		result["status"] = "error";
		result["phase"] = "validation";
		result["error_code"] = "NO_SCENE_ROOT";
		return result;
	}

	Node *parent = nullptr;
	if (p_parent_path == "." || p_parent_path.is_empty()) {
		parent = root;
	} else {
		parent = root->get_node_or_null(NodePath(p_parent_path));
	}

	if (!parent) {
		result["status"] = "error";
		result["phase"] = "validation";
		result["error_code"] = "NODE_NOT_FOUND";
		result["error"] = vformat("Parent node not found: %s", p_parent_path);
		return result;
	}

	if (!ClassDB::class_exists(p_type)) {
		result["status"] = "error";
		result["phase"] = "validation";
		result["error_code"] = "INVALID_CLASS";
		result["error"] = vformat("Node class not found: %s", p_type);
		return result;
	}

	Node *new_node = Object::cast_to<Node>(ClassDB::instantiate(p_type));
	if (!new_node) {
		result["status"] = "error";
		result["phase"] = "execution";
		result["error_code"] = "INSTANTIATION_FAILED";
		result["error"] = vformat("Failed to instantiate node of type: %s", p_type);
		return result;
	}

	new_node->set_name(p_name);

	if (EditorUndoRedoManager *ur = EditorUndoRedoManager::get_singleton()) {
		ur->add_do_method(parent, "add_child", new_node, true);
		ur->add_do_method(new_node, "set_owner", root);
		ur->add_do_reference(new_node);

		ur->add_undo_method(parent, "remove_child", new_node);
	} else {
		memdelete(new_node);
		result["status"] = "error";
		result["phase"] = "execution";
		result["error_code"] = "UNDO_MANAGER_UNAVAILABLE";
		return result;
	}

	result["status"] = "success";
	result["node_touched"] = String(parent->get_path()) + "/" + p_name;

	return result;
}

Dictionary EditorAIActions::remove_node(const String &p_node_path) {
	Dictionary result;
	if (!EditorInterface::get_singleton() || !EditorNode::get_singleton()) {
Dictionary err;
err["error_code"] = "NO_EDITOR_NODE";
err["error_string"] = "EditorNode is not available (headless environment).";
        err["environment"] = "headless";
        err["editor_services_available"] = false;
        err["phase"] = "validation";
return err;
}
Node *root = EditorInterface::get_singleton()->get_edited_scene_root();
	if (!root) {
		result["status"] = "error";
		result["phase"] = "validation";
		result["error_code"] = "NO_SCENE_ROOT";
		return result;
	}

	Node *target = root->get_node_or_null(NodePath(p_node_path));
	if (!target || target == root) {
		result["status"] = "error";
		result["phase"] = "validation";
		result["error_code"] = "NODE_NOT_FOUND_OR_IS_ROOT";
		result["error"] = vformat("Cannot remove node at path: %s", p_node_path);
		return result;
	}

	Node *parent = target->get_parent();

	if (EditorUndoRedoManager *ur = EditorUndoRedoManager::get_singleton()) {
		ur->add_do_method(parent, "remove_child", target);

		ur->add_undo_method(parent, "add_child", target, true);
		ur->add_undo_method(target, "set_owner", root);
		ur->add_undo_reference(target);
	} else {
		result["status"] = "error";
		result["phase"] = "execution";
		result["error_code"] = "UNDO_MANAGER_UNAVAILABLE";
		return result;
	}

	result["status"] = "success";
	result["node_touched"] = target->get_path();
	return result;
}

void EditorAIActions::reparent_node(const String &p_node_path, const String &p_new_parent_path) {
	// TODO
}

Dictionary EditorAIActions::rename_node(const String &p_node_path, const String &p_new_name) {
	Dictionary result;

	if (!EditorInterface::get_singleton() || !EditorNode::get_singleton()) {
Dictionary err;
err["error_code"] = "NO_EDITOR_NODE";
err["error_string"] = "EditorNode is not available (headless environment).";
        err["environment"] = "headless";
        err["editor_services_available"] = false;
        err["phase"] = "validation";
return err;
}
Node *root = EditorInterface::get_singleton()->get_edited_scene_root();
	if (!root) {
		result["status"] = "error";
		result["phase"] = "validation";
		result["error_code"] = "NO_SCENE_ROOT";
		return result;
	}

	Node *target = root->get_node_or_null(NodePath(p_node_path));
	if (!target) {
		result["status"] = "error";
		result["phase"] = "validation";
		result["error_code"] = "NODE_NOT_FOUND";
		return result;
	}

	if (p_new_name.is_empty()) {
		result["status"] = "error";
		result["phase"] = "validation";
		result["error_code"] = "INVALID_NAME";
		return result;
	}

	String old_name = target->get_name();

	if (EditorUndoRedoManager *ur = EditorUndoRedoManager::get_singleton()) {
		ur->add_do_method(target, "set_name", p_new_name);
		ur->add_undo_method(target, "set_name", old_name);
	} else {
		result["status"] = "error";
		result["phase"] = "execution";
		result["error_code"] = "UNDO_MANAGER_UNAVAILABLE";
		return result;
	}

	result["status"] = "success";
	result["node_touched"] = target->get_path();
	result["old_value"] = old_name;
	result["new_value"] = p_new_name;

	return result;
}

Dictionary EditorAIActions::set_property(const String &p_node_path, const String &p_property, const Variant &p_value) {
	Dictionary result;

	if (!EditorInterface::get_singleton() || !EditorNode::get_singleton()) {
Dictionary err;
err["error_code"] = "NO_EDITOR_NODE";
err["error_string"] = "EditorNode is not available (headless environment).";
        err["environment"] = "headless";
        err["editor_services_available"] = false;
        err["phase"] = "validation";
return err;
}
Node *root = EditorInterface::get_singleton()->get_edited_scene_root();
	if (!root) {
		result["status"] = "error";
		result["phase"] = "validation";
		result["error_code"] = "NO_SCENE_ROOT";
		result["error"] = "No edited scene root open in the editor.";
		return result;
	}

	Node *target = nullptr;
	if (p_node_path == "." || p_node_path.is_empty()) {
		target = root;
	} else {
		target = root->get_node_or_null(NodePath(p_node_path));
	}

	if (!target) {
		result["status"] = "error";
		result["phase"] = "validation";
		result["error_code"] = "NODE_NOT_FOUND";
		result["error"] = vformat("Node not found: %s", p_node_path);
		result["node_path"] = p_node_path;
		return result;
	}

	// Validate property existence
	bool prop_exists = false;
	List<PropertyInfo> plist;
	target->get_property_list(&plist);
	for (const PropertyInfo &p : plist) {
		if (p.name == p_property) {
			prop_exists = true;
			break;
		}
	}

	if (!prop_exists) {
		result["status"] = "error";
		result["phase"] = "validation";
		result["error_code"] = "PROPERTY_NOT_FOUND";
		result["error"] = vformat("Property '%s' not found on node.", p_property);
		result["node_path"] = p_node_path;
		result["property"] = p_property;
		return result;
	}

	Variant old_value = target->get(p_property);

	if (EditorUndoRedoManager *ur = EditorUndoRedoManager::get_singleton()) {
		ur->add_do_property(target, p_property, p_value);
		ur->add_undo_property(target, p_property, old_value);
	} else {
		result["status"] = "error";
		result["phase"] = "execution";
		result["error_code"] = "UNDO_MANAGER_UNAVAILABLE";
		result["error"] = "Platform EditorUndoRedoManager is null.";
		return result;

		}


		return result;
}

void EditorAIActions::attach_script(const String &p_node_path, const String &p_script_path) {
	// TODO
}

void EditorAIActions::connect_signal(const String &p_source_path, const String &p_signal, const String &p_target_path, const String &p_method) {
	// TODO
}

Node *EditorAIActions::instantiate_packed_scene(const String &p_parent_path, const String &p_scene_path, const String &p_name) {
	return nullptr; // TODO
}

Array EditorAIActions::get_script_diagnostics(const String &p_script_path) {
	return Array(); // TODO
}

Dictionary EditorAIActions::run_runtime_probe(int p_frame_count) {
	return Dictionary(); // TODO
}

EditorAIActions::EditorAIActions() {
	singleton = this;
}

EditorAIActions::~EditorAIActions() {
	singleton = nullptr;
}
