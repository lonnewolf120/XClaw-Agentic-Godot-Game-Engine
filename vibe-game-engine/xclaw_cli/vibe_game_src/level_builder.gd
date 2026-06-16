extends RefCounted
# LevelBuilder — turns one level dict from the GameSpec into live nodes under a parent.
#
# Coordinate convention (matches gamespec.py): Godot 2D, y DOWN-positive.
#   - platforms / hazards / goal: (x, y) is the TOP-LEFT corner, plus (w, h) size.
#   - enemies / collectibles / player_spawn: (x, y) is the CENTER.

const PLAYER_LAYER := 1
const PLATFORM_LAYER := 2

var _factory


func _init() -> void:
	_factory = preload("res://vibe_game/entity_factory.gd").new()


func build(level: Dictionary, parent: Node, player_spec: Dictionary) -> Dictionary:
	for p in level.get("platforms", []):
		parent.add_child(_make_platform(p))
	for hz in level.get("hazards", []):
		parent.add_child(_make_hazard(hz))
	for c in level.get("collectibles", []):
		parent.add_child(_make_coin(c))
	for e in level.get("enemies", []):
		var enemy: Area2D = _factory.spawn_enemy(e)
		enemy.position = Vector2(float(e.get("x", 0)), float(e.get("y", 0)))
		parent.add_child(enemy)

	if level.has("goal"):
		parent.add_child(_make_goal(level["goal"]))

	var spawn: Dictionary = level.get("player_spawn", {"x": 0, "y": 0})
	var player: CharacterBody2D = _factory.spawn_player(player_spec)
	player.position = Vector2(float(spawn.get("x", 0)), float(spawn.get("y", 0)))
	parent.add_child(player)

	var cam := Camera2D.new()
	cam.enabled = true
	player.add_child(cam)
	cam.make_current()

	return {"player": player, "camera": cam}


func _make_platform(p: Dictionary) -> StaticBody2D:
	var w := float(p.get("w", 100))
	var h := float(p.get("h", 20))
	var body := StaticBody2D.new()
	body.collision_layer = PLATFORM_LAYER
	body.collision_mask = 0
	body.position = Vector2(float(p.get("x", 0)) + w / 2.0, float(p.get("y", 0)) + h / 2.0)
	var col := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = Vector2(w, h)
	col.shape = shape
	body.add_child(col)
	body.add_child(_rect_visual(w, h, Color(0.30, 0.32, 0.38)))
	return body


func _make_area_rect(w: float, h: float, color: Color) -> Area2D:
	var area := Area2D.new()
	area.collision_layer = 0
	area.collision_mask = PLAYER_LAYER
	area.monitoring = true
	var col := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = Vector2(w, h)
	col.shape = shape
	area.add_child(col)
	area.add_child(_rect_visual(w, h, color))
	return area


func _make_hazard(h: Dictionary) -> Area2D:
	var w := float(h.get("w", 48))
	var hh := float(h.get("h", 20))
	var area := _make_area_rect(w, hh, Color(0.9, 0.4, 0.1))
	area.position = Vector2(float(h.get("x", 0)) + w / 2.0, float(h.get("y", 0)) + hh / 2.0)
	area.set_script(load("res://vibe_game/parts/hazard.gd"))
	return area


func _make_goal(g: Dictionary) -> Area2D:
	var w := float(g.get("w", 48))
	var h := float(g.get("h", 64))
	var area := _make_area_rect(w, h, Color(0.2, 0.8, 0.35))
	area.position = Vector2(float(g.get("x", 0)) + w / 2.0, float(g.get("y", 0)) + h / 2.0)
	area.set_script(load("res://vibe_game/parts/goal.gd"))
	return area


func _make_coin(c: Dictionary) -> Area2D:
	var area := _make_area_rect(24, 24, Color(0.95, 0.85, 0.2))
	area.position = Vector2(float(c.get("x", 0)), float(c.get("y", 0)))
	area.set_script(load("res://vibe_game/parts/coin.gd"))
	area.set("amount", int(c.get("score", 10)))
	return area


func _rect_visual(w: float, h: float, color: Color) -> ColorRect:
	var r := ColorRect.new()
	r.size = Vector2(w, h)
	r.position = Vector2(-w / 2.0, -h / 2.0)
	r.color = color
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return r
