import sys

def patch_h():
    with open("editor/editor_ai_actions.h", "r", encoding="utf-8") as f:
        text = f.read()
    
    text = text.replace("bool apply_action_batch(const Array &p_batch);", "Array apply_action_batch(const Array &p_batch);")
    text = text.replace("bool preview_action_batch(const Array &p_batch);", "Array preview_action_batch(const Array &p_batch);")
    
    # inject class Node; at top to fix error C2065
    if "class Node;" not in text:
        text = text.replace("class EditorAIActions : public Object {", "class Node;\n\nclass EditorAIActions : public Object {")
        
    with open("editor/editor_ai_actions.h", "w", encoding="utf-8") as f:
        f.write(text)

patch_h()
print("Patched H")
