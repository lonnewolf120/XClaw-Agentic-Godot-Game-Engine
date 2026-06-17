@tool
extends SceneTree

func _init():
    print("--- Running Editor AI Batch Validation Tests ---")
    var ai = EditorAIActions.new()
    if not ai:
        printerr("Could not create EditorAIActions!")
        quit()
        return
    
    var batch1 = []
    batch1.append({"action": "create_node", "parent_path": ".", "type": "Node2D", "name": "AITest1"})
    var res1 = ai.apply_action_batch(batch1)
    print("\
Test 1 Result: ", _to_json(res1))
    
    var batch2 = []
    batch2.append({"action": "create_node", "parent_path": "/invalid/nonexistent", "type": "Node2D", "name": "AITest2"})
    var res2 = ai.apply_action_batch(batch2)
    print("\
Test 2 Result: ", _to_json(res2))
    
    var batch5 = []
    batch5.append({"action": "create_node", "parent_path": ".", "type": "Node2D", "name": "AITestPreview"})
    var res5 = ai.preview_action_batch(batch5)
    print("\
Test 5 Result: ", _to_json(res5))
    
    print("\
--- Tests Complete ---")
    quit()

# Helper to stringify an array of dicts for clean printing
func _to_json(data):
    var s = "[\
"
    for d in data:
        s += "  " + str(d) + ",\
"
    if data.size() > 0:
        s = s.substr(0, s.length() - 2) + "\
"
    s += "]"
    return s
