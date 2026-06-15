extends Node
# VibeCore Scout: Observation & Introspection Tool
# Analyzes the SceneTree at runtime and prints discovery data for the AI.

func _ready():
	# Wait a few frames for things to spawn
	await get_tree().create_timer(1.0).timeout
	discover()
	
	# If running headlessly for observation, quit after scouting
	if DisplayServer.get_name() == "headless":
		await get_tree().create_timer(1.0).timeout
		get_tree().quit()

func discover():
	print("\n--- VIBE_SCOUT_START ---")
	var root = get_tree().root
	var scan_data = {
		"timestamp": Time.get_unix_time_from_system(),
		"tree": _scan_node(root),
		"globals": _get_globals()
	}
	print(JSON.stringify(scan_data))
	print("--- VIBE_SCOUT_END ---\n")

func _scan_node(node: Node) -> Dictionary:
	var data = {
		"name": node.name,
		"type": node.get_class(),
		"path": str(node.get_path()),
		"pos": _get_pos(node),
		"child_count": node.get_child_count(),
		"children": []
	}
	
	# Only recurse 4 levels deep to keep logs lean
	if data.path.split("/").size() < 6:
		for child in node.get_children():
			# Skip internal Godot nodes
			if not child.name.begins_with("@@"):
				data.children.append(_scan_node(child))
				
	return data

func _get_pos(node: Node):
	if node is Node3D:
		return {"x": node.global_position.x, "y": node.global_position.y, "z": node.global_position.z}
	elif node is Control or node is Node2D:
		return {"x": node.global_position.x, "y": node.global_position.y}
	return null

func _get_globals() -> Dictionary:
	var globals = {}
	if has_node("/root/VibeState"):
		var state = get_node("/root/VibeState")
		globals["vibe_state"] = {
			"score": state.score,
			"health": state.player_health,
			"game_time": state.game_time
		}
	return globals
