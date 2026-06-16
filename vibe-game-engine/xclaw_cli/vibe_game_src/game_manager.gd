extends Node
# GameManager (autoload) — the spine of a schema-driven game.
#
# Reads res://game_spec.json and drives the state machine:
#   MENU -> PLAYING(level n) -> LEVEL_COMPLETE -> next | GAME_OVER -> restart -> ... | WON
#
# Owns two container children created under start()'s host node:
#   GameWorld (Node2D)  -> levels build into this; clear() frees exactly this subtree.
#   menus               -> CanvasLayers added to the host (freed explicitly).
# This keeps level nodes from ever becoming siblings of the VibeCore autoloads.

enum State { MENU, PLAYING, LEVEL_COMPLETE, GAME_OVER, WON }

const SPEC_PATH := "res://game_spec.json"
const FALL_MARGIN := 300.0

var spec: Dictionary = {}
var state: int = State.MENU
var current_level: int = 0

var host: Node = null
var world: Node2D = null
var menu_layer: CanvasLayer = null
var over_layer: CanvasLayer = null
var player: CharacterBody2D = null

var _spawn := Vector2.ZERO
var _dying := false
var _level_builder
var _menu_builder


func _ready() -> void:
	_level_builder = preload("res://vibe_game/level_builder.gd").new()
	_menu_builder = preload("res://vibe_game/menu_builder.gd").new()
	if has_node("/root/VibeEvents"):
		var ev := get_node("/root/VibeEvents")
		ev.goal_reached.connect(_on_goal_reached)
		ev.player_died.connect(_on_player_died)


func start(host_node: Node) -> void:
	host = host_node
	spec = _load_spec()
	world = Node2D.new()
	world.name = "GameWorld"
	host.add_child(world)
	_show_menu()


func _load_spec() -> Dictionary:
	if not FileAccess.file_exists(SPEC_PATH):
		push_error("GameManager: game_spec.json not found at " + SPEC_PATH)
		return {}
	var text := FileAccess.get_file_as_string(SPEC_PATH)
	var parsed = JSON.parse_string(text)
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("GameManager: game_spec.json is not a JSON object")
		return {}
	return parsed


func _levels() -> Array:
	return spec.get("levels", [])


func _clear_world() -> void:
	if world and is_instance_valid(world):
		for c in world.get_children():
			c.queue_free()
	player = null


func _clear_menus() -> void:
	if menu_layer and is_instance_valid(menu_layer):
		menu_layer.queue_free()
	menu_layer = null
	if over_layer and is_instance_valid(over_layer):
		over_layer.queue_free()
	over_layer = null


func _show_menu() -> void:
	state = State.MENU
	_clear_world()
	_clear_menus()
	menu_layer = _menu_builder.build_main_menu(host)


func begin_game() -> void:
	if has_node("/root/VibeState"):
		var st := get_node("/root/VibeState")
		st.reset_session()
		st.lives = int(spec.get("progression", {}).get("lives", 3))
	_clear_menus()
	goto_level(0)


func goto_level(idx: int) -> void:
	var levels := _levels()
	if idx < 0 or idx >= levels.size():
		return
	current_level = idx
	state = State.PLAYING
	_dying = false
	_clear_world()

	var level: Dictionary = levels[idx]
	var refs: Dictionary = _level_builder.build(level, world, spec.get("player", {}))
	player = refs.get("player")

	var sp: Dictionary = level.get("player_spawn", {"x": 0, "y": 0})
	_spawn = Vector2(float(sp.get("x", 0)), float(sp.get("y", 0)))

	if has_node("/root/VibeState"):
		get_node("/root/VibeState").level = idx + 1
	if has_node("/root/VibeEvents"):
		get_node("/root/VibeEvents").level_started.emit(String(level.get("name", "Level %d" % (idx + 1))))


func _on_goal_reached() -> void:
	if state != State.PLAYING:
		return
	if current_level + 1 < _levels().size():
		state = State.LEVEL_COMPLETE
		goto_level(current_level + 1)
	else:
		_win()


func _on_player_died() -> void:
	if state != State.PLAYING or _dying:
		return
	_dying = true
	if has_node("/root/VibeState"):
		var st := get_node("/root/VibeState")
		st.lives -= 1
		if st.lives <= 0:
			_game_over(false)
			return
	_respawn()


func _respawn() -> void:
	await get_tree().physics_frame
	if player and is_instance_valid(player):
		player.velocity = Vector2.ZERO
		player.global_position = _spawn
	_dying = false


func _win() -> void:
	state = State.WON
	if has_node("/root/VibeEvents"):
		var ev := get_node("/root/VibeEvents")
		ev.game_won.emit()
		ev.game_over.emit(true)
	_clear_world()
	over_layer = _menu_builder.build_game_over(host, true)


func _game_over(success: bool) -> void:
	state = State.GAME_OVER
	if has_node("/root/VibeEvents"):
		get_node("/root/VibeEvents").game_over.emit(success)
	_clear_world()
	over_layer = _menu_builder.build_game_over(host, success)


func restart() -> void:
	begin_game()


func quit_game() -> void:
	get_tree().quit()


func _physics_process(_delta: float) -> void:
	if state != State.PLAYING or player == null or not is_instance_valid(player) or _dying:
		return
	var levels := _levels()
	if current_level >= levels.size():
		return
	var bounds: Dictionary = levels[current_level].get("bounds", {"h": 720})
	var kill_y := float(bounds.get("h", 720)) + FALL_MARGIN
	if player.global_position.y > kill_y:
		if has_node("/root/VibeEvents"):
			get_node("/root/VibeEvents").player_died.emit()
