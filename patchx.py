import re

with open("editor/editor_ai_actions.cpp", "r") as f:
    text = f.read()

pattern = r'''if \(!EditorInterface::get_singleton\(\)\) \{\nDictionary err;\nerr\["error_code"\] = "NO_EDITOR_INTERFACE";\nerr\["error_string"\] = "EditorInterface is not available \(headless mode\?\)\.";\nreturn err;\n\}\nNode \*root = EditorInterface::get_singleton\(\)->get_edited_scene_root\(\);'''

repl = r'''if (!EditorInterface::get_singleton() || !EditorNode::get_singleton()) {
Dictionary err;
err["error_code"] = "NO_EDITOR_NODE";
err["error_string"] = "EditorNode is not available (headless SceneTree script?).";
return err;
}
Node *root = EditorInterface::get_singleton()->get_edited_scene_root();'''

new_text = re.sub(pattern, repl, text)

print("Changed:", new_text != text)

with open("editor/editor_ai_actions.cpp", "w") as f:
    f.write(new_text)

