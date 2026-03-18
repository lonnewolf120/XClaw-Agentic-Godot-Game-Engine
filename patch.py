import re

with open("godot/editor/editor_ai_actions.cpp", "r", encoding="utf-8") as f:
    text = f.read()

replacement = """Array EditorAIActions::apply_action_batch(const Array &p_batch) {
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
        
        // Ensure standard fields if successful
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
        // To safely abort an action in Godot without memory leaks or missing DO states:
        // 1. Commit the action (executes it and validates internal tree dependencies).
        // 2. Immediately undo it to revert the scene.
        ur->commit_action(true);
        ur->undo();
    }
}
"""

text = re.sub(r'bool EditorAIActions::apply_action_batch.*?void EditorAIActions::commit_transaction\(\) \{', replacement + "\n\nvoid EditorAIActions::commit_transaction() {", text, flags=re.DOTALL)

with open("godot/editor/editor_ai_actions.cpp", "w", encoding="utf-8") as f:
    f.write(text)
