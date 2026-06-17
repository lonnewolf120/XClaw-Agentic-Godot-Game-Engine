import re

with open("editor/editor_ai_actions.cpp", "r") as f:
    text = f.read()

pattern = r'Dictionary err;\nerr\["error_code"\] = "NO_EDITOR_INTERFACE";\nerr\["error_string"\] = "EditorInterface is not available \(headless mode\?\)\.";\nArray ret;\nret\.push_back\(err\);\nreturn ret;'

repl = r'''Dictionary err;
err["error_code"] = "NO_EDITOR_INTERFACE";
err["error_string"] = "EditorInterface is not available (headless mode?).";
return err;'''

new_text = re.sub(pattern, repl, text)

with open("editor/editor_ai_actions.cpp", "w") as f:
    f.write(new_text)

print("regex matched:", new_text != text)
