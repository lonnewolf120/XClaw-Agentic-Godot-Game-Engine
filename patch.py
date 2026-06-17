import re

with open("editor/editor_ai_actions.cpp", "r") as f:
    content = f.read()

content = re.sub(
    r'\tNode \*root = EditorInterface::get_singleton\(\)->get_edited_scene_root\(\);',
    r'\tif (!EditorInterface::get_singleton()) {\n\t\tret["error_code"] = "NO_EDITOR_INTERFACE";\n\t\tret["error_string"] = "EditorInterface is not available (headless mode?).";\n\t\treturn ret;\n\t}\n\tNode *root = EditorInterface::get_singleton()->get_edited_scene_root();',
    content
)

with open("editor/editor_ai_actions.cpp", "w") as f:
    f.write(content)
print("Replaced with regex!")
