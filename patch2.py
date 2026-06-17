import re

with open("editor/editor_ai_actions.cpp", "r") as f:
    content = f.read()

# Replace the incorrect patch
content = content.replace(
'''if (!EditorInterface::get_singleton()) {
ret["error_code"] = "NO_EDITOR_INTERFACE";
ret["error_string"] = "EditorInterface is not available (headless mode?).";
return ret;
}''',
'''if (!EditorInterface::get_singleton()) {
Dictionary err;
err["error_code"] = "NO_EDITOR_INTERFACE";
err["error_string"] = "EditorInterface is not available (headless mode?).";
Array ret;
ret.push_back(err);
return ret;
}''')

with open("editor/editor_ai_actions.cpp", "w") as f:
    f.write(content)
print("Replaced with Dictionary err!")
