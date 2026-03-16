@tool
extends EditorScript

# Stage 2 Native Node Topology Mutation Validation

func _run():
    print("\n================================================")
    print("=== Native Hook Stage 2: Node Topology ===")
    print("================================================\n")

    var ai_actions = ClassDB.instantiate("EditorAIActions")
    var root = EditorInterface.get_edited_scene_root()
    if not root:
        printerr("  ERROR: Open a scene first.")
        return

    # 1. create_node
    print("\n[1] Testing create_node...")
    ai_actions.begin_transaction("AI Create Node Test")
    
    var create_res = ai_actions.create_node(".", "Sprite2D", "TestAISprite")
    print("  create_node result: ", create_res)
    
    if create_res.get("status") == "success":
        ai_actions.commit_transaction()
        print("  SUCCESS: Node created! (Press Ctrl+Z to undo)")
    else:
        ai_actions.rollback_transaction()
        printerr("  ERROR: Expected success but got: ", create_res)

    # Note: Wait or check manually next steps. For testing script simplicity,
    # we just run these as separated operations you can toggle manually,
    # because testing them immediately after another relies on them existing in tree,
    # and EditorUndoRedoManager usually defers structural changes slightly.

    print("\n================================================")
    print("=== Stage 2 Execution Complete ===")
    print("Test create_node manually first. Then try rename and remove.")
    print("================================================\n")
