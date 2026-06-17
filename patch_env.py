import re

with open("editor/editor_ai_actions.cpp", "r") as f:
    text = f.read()

pattern = r'''if \(\!EditorInterface::get_singleton\(\) \|\| \!EditorNode::get_singleton\(\)\) \{\nDictionary err;\nerr\["error_code"\] = "NO_EDITOR_NODE";\nerr\["error_string"\] = "EditorNode is not available \(headless SceneTree script\?\)\.";\nreturn err;\n\}'''

repl = r'''if (!EditorInterface::get_singleton() || !EditorNode::get_singleton()) {
Dictionary err;
err["error_code"] = "NO_EDITOR_NODE";
err["error_string"] = "EditorNode is not available (headless environment).";
        err["environment"] = "headless";
        err["editor_services_available"] = false;
        err["phase"] = "validation";
return err;
}'''

new_text = re.sub(pattern, repl, text)

print("Changed:", new_text != text)

with open("editor/editor_ai_actions.cpp", "w") as f:
    f.write(new_text)

