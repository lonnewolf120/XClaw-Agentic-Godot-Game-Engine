extends RefCounted
# EntityFactory — builds the "actors" (player + enemies) as code-only nodes.
# No .tscn authoring: collision shapes and greybox visuals are generated here.
#
# Collision layers (bitmask values):
#   1 = player   2 = platforms   4 = enemies

const PLAYER_LAYER := 1
const PLATFORM_LAYER := 2
const ENEMY_LAYER := 4


func _rect_shape(w: float, h: float) -> RectangleShape2D:
	var s := RectangleShape2D.new()
	s.size = Vector2(w, h)
	return s


func _visual(w: float, h: float, color: Color) -> ColorRect:
	var r := ColorRect.new()
	r.size = Vector2(w, h)
	r.position = Vector2(-w / 2.0, -h / 2.0)
	r.color = color
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return r


func _parse_color(v) -> Color:
	if v is Color:
		return v
	if v is String and v != "":
		return Color(v)
	return Color(0.3, 0.55, 0.85)


func spawn_player(player_spec: Dictionary) -> CharacterBody2D:
	var size_spec: Dictionary = player_spec.get("size", {})
	var w: float = float(size_spec.get("w", 32))
	var h: float = float(size_spec.get("h", 48))

	var body := CharacterBody2D.new()
	body.name = "Player"
	body.collision_layer = PLAYER_LAYER
	body.collision_mask = PLATFORM_LAYER
	body.add_to_group("player")

	var col := CollisionShape2D.new()
	col.shape = _rect_shape(w, h)
	body.add_child(col)
	body.add_child(_visual(w, h, _parse_color(player_spec.get("color", "#4a90d9"))))

	var script_path: String = String(player_spec.get("script", ""))
	if script_path != "" and ResourceLoader.exists(script_path):
		body.set_script(load(script_path))
	return body


func spawn_enemy(enemy_spec: Dictionary) -> Area2D:
	var t: String = String(enemy_spec.get("type", "patroller"))
	var w := 40.0
	var h := 40.0

	var area := Area2D.new()
	area.name = "Enemy"
	area.collision_layer = ENEMY_LAYER
	area.collision_mask = PLAYER_LAYER
	area.monitoring = true

	var col := CollisionShape2D.new()
	col.shape = _rect_shape(w, h)
	area.add_child(col)
	area.add_child(_visual(w, h, Color(0.85, 0.25, 0.25)))

	# 'patroller' moves; 'chaser' lands in Phase 3 — until then it is a static hazard.
	area.set_script(load("res://vibe_game/parts/patroller.gd"))
	if t == "patroller":
		area.set("range_px", float(enemy_spec.get("patrol", 120)))
		area.set("speed", float(enemy_spec.get("speed", 60)))
	else:
		area.set("range_px", 0.0)
		area.set("speed", 0.0)
	return area
