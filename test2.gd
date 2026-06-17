@tool
extends SceneTree

func _init():
    print("--- Testing create_node ---")
    var ai = EditorAIActions.new()
    print("AI object created")
    var res1 = ai.create_node(".", "Node2D", "AITest1")
    print("Test 1 Result: ", res1)
    print("--- Done ---")
    quit()
