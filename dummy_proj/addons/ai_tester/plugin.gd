@tool
extends EditorPlugin

func _enter_tree():
    var timer = get_tree().create_timer(1.0)
    timer.timeout.connect(_run_tests)

func assert_eq(a, b, msg=""):
    if a != b:
        printerr("ASSERT FAILED: ", a, " != ", b, " | ", msg)

func _run_tests():
    print("==============================================")
    print("--- LIVE EDITOR AI BATCH VALIDATION V1.6 ---")

    var root = Node2D.new()
    root.name = "MainNode"
    var p = PackedScene.new()
    p.pack(root)
    ResourceSaver.save(p, "res://test_scene.tscn")

    EditorInterface.open_scene_from_path("res://test_scene.tscn")

    var t2 = get_tree().create_timer(0.5)
    t2.timeout.connect(_run_tests_2)

func _run_tests_2():
    var ai = EditorAIActions.new()
    if EditorInterface.get_edited_scene_root() == null:
        print("Still no scene root!")
        get_tree().quit()
        return

    print("\n[PART 1] Undo stack cleanliness & Receipt Asserts")

    var b_batch = [{"action": "create_node", "parent_path": ".", "type": "Node2D", "name": "BaseMarker"}]
    var b_res = ai.apply_action_batch(b_batch)

    var invalid_batch = [
        {"action": "create_node", "parent_path": ".", "type": "Node2D", "name": "ShouldRollback"},
        {"action": "create_node", "parent_path": "/invalid/path", "type": "Node2D", "name": "WillFail"}
    ]
    var res_inv = ai.apply_action_batch(invalid_batch)
    assert_eq(res_inv[0].get("rolled_back", false), true, "First action must roll back")
    assert_eq(res_inv[0].get("committed", true), false, "First action must not be committed")
    assert_eq(res_inv[1].get("status"), "error", "Second action must have error")

    var preview_batch = [
        {"action": "create_node", "parent_path": ".", "type": "Node2D", "name": "PreviewNode"}
    ]
    var res_prev = ai.preview_action_batch(preview_batch)
    assert_eq(res_prev[0].get("preview_only", false), true, "Action must be preview only")
    assert_eq(res_prev[0].get("rolled_back", false), true, "Preview must be rolled back")
    assert_eq(res_prev[0].get("committed", true), false, "Preview must not be committed")

    var urman = EditorInterface.get_editor_undo_redo()
    var ur = urman.get_history_undo_redo(urman.get_object_history_id(EditorInterface.get_edited_scene_root()))

    ur.undo()
    var children_after_undo = []
    for c in EditorInterface.get_edited_scene_root().get_children():
        children_after_undo.append(c.name)
    assert_eq(children_after_undo.has("BaseMarker"), false, "Ghost entries check failed!")
    print("Undo cleanly passed! Ghost entries ignored. Children:", children_after_undo)

    ur.redo()

    print("\n[PART 2] Save/Reload Persistence")
    var valid_batch = [
        {"action": "create_node", "parent_path": ".", "type": "Node2D", "name": "AIPersist1"}
    ]
    var res_valid = ai.apply_action_batch(valid_batch)
    assert_eq(res_valid[0].get("committed", false), true, "Valid action must be committed")

    EditorInterface.save_scene()

    # Verify disk - FIXED CONSTANT enum
    var disk1 = ResourceLoader.load("res://test_scene.tscn", "", ResourceLoader.CACHE_MODE_IGNORE).instantiate()
    assert_eq(disk1.has_node("AIPersist1"), true, "Node MUST exist on disk after save.")
    print("Nodes persisted correctly to disk! Valid Commit saved.")

    ur.undo()
    EditorInterface.save_scene()
    var disk2 = ResourceLoader.load("res://test_scene.tscn", "", ResourceLoader.CACHE_MODE_IGNORE).instantiate()
    assert_eq(disk2.has_node("AIPersist1"), false, "Node MUST NOT exist on disk after undo + save.")
    print("Undo persisted correctly to disk! Reverted changes saved.")

    ur.redo()
    EditorInterface.save_scene()
    var disk3 = ResourceLoader.load("res://test_scene.tscn", "", ResourceLoader.CACHE_MODE_IGNORE).instantiate()
    assert_eq(disk3.has_node("AIPersist1"), true, "Node MUST exist on disk after redo + save.")
    print("Redo persisted correctly to disk! Remade changes saved.")

    disk1.queue_free()
    disk2.queue_free()
    disk3.queue_free()

    print("=================== V1.6 TESTS COMPLETE ===================")
    get_tree().quit()
