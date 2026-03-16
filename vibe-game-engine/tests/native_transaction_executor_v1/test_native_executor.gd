@tool
extends EditorScript

# Native Hook Validation Path v1 Verification

func _run():
    print("\n================================================")
    print("=== Native Hook Validation Path v1 ===")
    print("================================================\n")
    
    # 1. GDScript visibility
    print("[1] Checking GDScript Visibility...")
    if not ClassDB.class_exists("EditorAIActions"):
        printerr("  ERROR: EditorAIActions class not found! Did you recompile Godot?")
        return
    else:
        print("  SUCCESS: EditorAIActions class is registered in ClassDB.")
        
    var ai_actions = ClassDB.instantiate("EditorAIActions")
    if not ai_actions:
        printerr("  ERROR: Could not instantiate EditorAIActions.")
        return
        
    print("  SUCCESS: EditorAIActions instantiated safely.")
    
    if not ai_actions.has_method("begin_transaction"):
        printerr("  ERROR: Method 'begin_transaction' not found.")
        return

    print("  SUCCESS: Methods bound correctly.")
    
    var editor_interface = EditorInterface
    var root = editor_interface.get_edited_scene_root()
    if not root:
        printerr("\n  ERROR: Please open a scene in the editor first to test transactions.")
        return
        
    # 2. Transaction sanity (Valid case)
    print("\n[2] Testing valid transaction (set_property)...")
    ai_actions.begin_transaction("AI Set Property Test")
    
    # We will test setting the editor_description on the root node
    var target_property = "editor_description"
    var old_desc = root.editor_description
    var new_desc = str(old_desc) + " (modified by AI executor hook)"
    
    var result = ai_actions.set_property(".", target_property, new_desc)
    print("  set_property result: ", result)
    
    if result.get("status") == "success":
        ai_actions.commit_transaction()
        print("  SUCCESS: Transaction committed.")
        
        if root.editor_description == new_desc:
            print("  SUCCESS: Property was actually changed in the editor!")
        else:
            printerr("  ERROR: Property was not changed!")
    else:
        ai_actions.rollback_transaction()
        printerr("  ERROR: Transaction failed unexpectedly.")

    # 3. Failure path (Invalid property)
    print("\n[3] Testing failure path (invalid property)...")
    ai_actions.begin_transaction("AI Invalid Property Test")
    
    var fail_result = ai_actions.set_property(".", "non_existent_property_123", "value")
    print("  Invalid set_property result: ", fail_result)
    
    if fail_result.get("status") == "error":
        ai_actions.rollback_transaction()
        if fail_result.get("error_code") == "PROPERTY_NOT_FOUND" and fail_result.get("phase") == "validation":
            print("  SUCCESS: Invalid property failed with correct error_code and phase.")
        else:
            printerr("  ERROR: Invalid property failed but missing expected structures: %s" % fail_result)
    else:
        ai_actions.commit_transaction()
        printerr("  ERROR: Invalid property did not return error status!")

    # 4. Failure path (Invalid node path)
    print("\n[4] Testing failure path (invalid node path)...")
    ai_actions.begin_transaction("AI Invalid Node Path Test")

    var node_fail_result = ai_actions.set_property("NonExistentNode/Path123", "editor_description", "value")
    print("  Invalid node path result: ", node_fail_result)

    if node_fail_result.get("status") == "error":
        ai_actions.rollback_transaction()
        if node_fail_result.get("error_code") == "NODE_NOT_FOUND" and node_fail_result.get("phase") == "validation":
            print("  SUCCESS: Invalid node path failed with correct error_code and phase.")
        else:
            printerr("  ERROR: Invalid node path failed but missing expected structures: %s" % node_fail_result)
    else:
        ai_actions.commit_transaction()
        printerr("  ERROR: Invalid node path did not return error status!")

    print("\n================================================")
    print("=== Test Complete ===")
    print("If successful, press Ctrl+Z / Ctrl+Y in Godot to verify Undo/Redo works!")
