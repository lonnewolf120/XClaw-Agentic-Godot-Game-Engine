import sys

script = """@tool
extends SceneTree

func _init():
\tprint("--- Running Editor AI Batch Validation Tests ---")
\tvar ai = EditorAIActions.new()
\tif not ai:
\t\tprinterr("Could not create EditorAIActions!")
\t\tquit()
\t\treturn
\t
\t# In headless, EditorInterface::get_edited_scene_root() is going to be null.
\t# Our code returns NO_SCENE_ROOT, which we can assert as proper validation failure.
\t# Test 1: All valid actions -> Must succeed and commit.
\tvar batch1 = []
\tbatch1.append({"action": "create_node", "parent_path": ".", "type": "Node2D", "name": "AITest1"})
\tbatch1.append({"action": "rename_node", "node_path": "./AITest1", "new_name": "AITest1Renamed"})
\tvar res1 = ai.apply_action_batch(batch1)
\tprint("\\nTest 1 Result: ", _to_json(res1))
\t
\tvar batch2 = []
\tbatch2.append({"action": "create_node", "parent_path": "/invalid/nonexistent", "type": "Node2D", "name": "AITest2"})
\tvar res2 = ai.apply_action_batch(batch2)
\tprint("\\nTest 2 Result: ", _to_json(res2))
\t
\tvar batch5 = []
\tbatch5.append({"action": "create_node", "parent_path": ".", "type": "Node2D", "name": "AITestPreview"})
\tvar res5 = ai.preview_action_batch(batch5)
\tprint("\\nTest 5 Result: ", _to_json(res5))
\t
\tprint("\\n--- Tests Complete ---")
\tquit()

# Helper to stringify an array of dicts for clean printing
func _to_json(data):
\tvar s = "[\\n"
\tfor d in data:
\t\ts += "  " + str(d) + ",\\n"
\tif data.size() > 0:
\t\ts = s.substr(0, s.length() - 2) + "\\n"
\ts += "]"
\treturn s
"""

with open("tests/test_editor_ai_batch.gd", "w", encoding="utf-8") as f:
    f.write(script)
