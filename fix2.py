import sys
import re

with open("editor/editor_ai_actions.cpp", "r", encoding="utf-8") as f:
    text = f.read()

pattern = r'(\s*)return result;\s*\n\s*return result;\s*\}'
replacement = r'\1return result;\n\1}\n\n\1return result;\n}'

text = re.sub(pattern, replacement, text)

# Just to be extremely sure... I'll just append a brace if it's missing exactly there.
# Let's write a simpler regex:
pattern = r'(result\["error_code"\] = "UNDO_MANAGER_UNAVAILABLE";\s*result\["error"\] = "Platform EditorUndoRedoManager is null.";\s*return result;\s*)(return result;\s*\})'
replacement = r'\g<1>}\n\n\t\g<2>'

text = re.sub(pattern, replacement, text)

with open("editor/editor_ai_actions.cpp", "w", encoding="utf-8") as f:
    f.write(text)
