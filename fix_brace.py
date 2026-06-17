import sys

with open("editor/editor_ai_actions.cpp", "r", encoding="utf-8") as f:
    text = f.read()

target = """        } else {
                result["status"] = "error";
                result["phase"] = "execution";
                result["error_code"] = "UNDO_MANAGER_UNAVAILABLE";
                result["error"] = "Platform EditorUndoRedoManager is null.";
                return result;

        return result;
}"""

replacement = """        } else {
                result["status"] = "error";
                result["phase"] = "execution";
                result["error_code"] = "UNDO_MANAGER_UNAVAILABLE";
                result["error"] = "Platform EditorUndoRedoManager is null.";
                return result;
        }

        return result;
}"""
text = text.replace(target, replacement)

with open("editor/editor_ai_actions.cpp", "w", encoding="utf-8") as f:
    f.write(text)
