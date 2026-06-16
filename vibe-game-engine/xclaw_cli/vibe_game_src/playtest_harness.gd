extends Node2D
# Auto playtest gate. Runs the REAL GameManager headless, reads the SAME game_spec.json,
# and verifies structural completeness + correct progression + reachability under a bot.
#
# Honest limit: this proves the game is structurally complete, progresses correctly, the
# jump mechanic fires, and at least one automated path reaches each goal. It does NOT prove
# "fun" or "winnable by every path". A green verdict = "an automated player can progress it".
#
# Emits one machine-parseable line the Python gate scrapes:
#   VIBE_TEST RESULT verdict=PASS checks=.. failed=[]

# Mirror of GameManager.State (avoids fragile cross-script enum access on a Node-typed ref).
const ST_MENU := 0
const ST_PLAYING := 1
const ST_LEVEL_COMPLETE := 2
const ST_GAME_OVER := 3
const ST_WON := 4

var _checks: Array = []         # [{name, ok}]
var _goal_hit := false
var _died_count := 0
var _coin_total := 0

# bot input state
var _jump_down := false
var _jump_timer := 0


func _ready() -> void:
	await get_tree().process_frame
	var ev := get_node_or_null("/root/VibeEvents")
	if ev:
		ev.goal_reached.connect(func(): _goal_hit = true)
		ev.player_died.connect(func(): _died_count += 1)
		ev.coin_collected.connect(func(a): _coin_total += a)

	var gm := get_node_or_null("/root/GameManager")
	if gm == null:
		_emit_verdict_missing("GameManager autoload missing")
		return

	gm.start(self)
	await _frames(2)
	await _run_all(gm)
	_emit_verdict()


# ---------------------------------------------------------------- test sequence
func _run_all(gm: Node) -> void:
	var levels: Array = gm.spec.get("levels", [])
	_check("has_levels", levels.size() >= 1)
	_check("menu_builds", gm.menu_layer != null and _menu_ok(gm.menu_layer))

	# jump mechanic fires on ui_accept (deterministic, geometry-independent)
	gm.begin_game()
	await _wait_built(gm)
	_check("jump_works", await _jump_fires(gm))

	# reachability: a forward bot reaches each level's goal (fresh game per level)
	for i in range(levels.size()):
		gm.begin_game()
		await _wait_built(gm)
		gm.goto_level(i)
		await _wait_built(gm)
		_check("reach_level_%d" % i, await _run_bot(gm, 1200))

	# coin scores
	if _level_has(gm, 0, "collectibles"):
		gm.begin_game()
		await _wait_built(gm)
		var pre_score := _score(gm)
		_coin_total = 0
		_teleport_to_group("coin", gm)
		await _frames(6)
		_check("coin_scores", _score(gm) > pre_score and _coin_total > 0)

	# hazard kills + costs a life
	if _level_has(gm, 0, "hazards"):
		_check("hazard_kills", await _death_costs_life("hazard", gm))

	# enemy kills + costs a life
	if _level_has(gm, 0, "enemies"):
		_check("enemy_kills", await _death_costs_life("enemy", gm))

	# falling off the bottom kills + costs a life
	_check("fall_kills", await _fall_costs_life(gm))

	# progression: clear every level in order ends in WON
	_check("progression_and_win", await _progression(gm))

	# game over after lives drained
	_check("game_over", await _game_over_on_drain(gm))

	# restart returns to level 1 with reset lives
	gm.restart()
	await _wait_built(gm)
	_check("restart", gm.state == ST_PLAYING and gm.current_level == 0 and _lives(gm) == _spec_lives(gm))


# ---------------------------------------------------------------- check helpers
func _jump_fires(gm: Node) -> bool:
	var p = gm.player
	if p == null:
		return false
	var g := 0
	while not p.is_on_floor() and g < 120:
		await get_tree().physics_frame
		g += 1
	var y0: float = p.global_position.y
	_set_action("ui_accept", true)
	await get_tree().physics_frame
	_set_action("ui_accept", false)
	var min_y := y0
	for k in range(45):
		await get_tree().physics_frame
		if is_instance_valid(p):
			min_y = min(min_y, p.global_position.y)
	return min_y < y0 - 10.0


func _run_bot(gm: Node, budget: int) -> bool:
	# Phase-1 levels are flat / step-down, so a forward run reaches the goal. The jump
	# mechanic is verified independently by `jump_works`, keeping reachability deterministic.
	_goal_hit = false
	_set_action("ui_right", true)
	var f := 0
	while f < budget and not _goal_hit:
		await get_tree().physics_frame
		f += 1
	_set_action("ui_right", false)
	return _goal_hit


func _death_costs_life(group: String, gm: Node) -> bool:
	gm.begin_game()
	await _wait_built(gm)
	var pre := _lives(gm)
	_died_count = 0
	if not _teleport_to_group(group, gm):
		return false
	await _frames(10)
	return _died_count > 0 and _lives(gm) == pre - 1


func _fall_costs_life(gm: Node) -> bool:
	gm.begin_game()
	await _wait_built(gm)
	var pre := _lives(gm)
	_died_count = 0
	var bounds: Dictionary = gm.spec.get("levels", [])[0].get("bounds", {"h": 720})
	gm.player.global_position = Vector2(100, float(bounds.get("h", 720)) + 800.0)
	await _frames(10)
	return _died_count > 0 and _lives(gm) == pre - 1


func _progression(gm: Node) -> bool:
	gm.begin_game()
	await _wait_built(gm)
	var n: int = gm.spec.get("levels", []).size()
	for i in range(n):
		if gm.current_level != i:
			return false
		if not _teleport_to_group("goal", gm):
			return false
		await _frames(8)
	return gm.state == ST_WON


func _game_over_on_drain(gm: Node) -> bool:
	gm.begin_game()
	await _wait_built(gm)
	var guard := 0
	while _lives(gm) > 0 and guard < 30:
		if not _teleport_to_group("hazard", gm):
			break
		await _frames(10)
		guard += 1
	return gm.state == ST_GAME_OVER


# ---------------------------------------------------------------- primitives
func _wait_built(gm: Node) -> void:
	var g := 0
	while (gm.player == null or not is_instance_valid(gm.player)) and g < 40:
		await get_tree().physics_frame
		g += 1
	await get_tree().physics_frame
	await get_tree().physics_frame


func _teleport_to_group(group: String, gm: Node) -> bool:
	var nodes := get_tree().get_nodes_in_group(group)
	if nodes.is_empty() or gm.player == null or not is_instance_valid(gm.player):
		return false
	gm.player.global_position = nodes[0].global_position
	return true


func _pump_jump() -> void:
	if _jump_timer > 0:
		_jump_timer -= 1
		return
	if _jump_down:
		_set_action("ui_accept", false)
		_jump_down = false
		_jump_timer = 18
	else:
		_set_action("ui_accept", true)
		_jump_down = true
		_jump_timer = 3


func _set_action(action: String, pressed: bool) -> void:
	var ev := InputEventAction.new()
	ev.action = action
	ev.pressed = pressed
	Input.parse_input_event(ev)


func _menu_ok(layer: CanvasLayer) -> bool:
	return _find_button(layer, "StartButton") != null and _find_button(layer, "QuitButton") != null


func _find_button(node: Node, n: String) -> Node:
	if node.name == n and node is Button:
		return node
	for c in node.get_children():
		var r := _find_button(c, n)
		if r:
			return r
	return null


func _level_has(gm: Node, idx: int, key: String) -> bool:
	var levels: Array = gm.spec.get("levels", [])
	if idx >= levels.size():
		return false
	var arr = levels[idx].get(key, [])
	return arr is Array and arr.size() > 0


func _frames(n: int) -> void:
	for i in range(n):
		await get_tree().physics_frame


func _score(gm: Node) -> int:
	var st := get_node_or_null("/root/VibeState")
	return int(st.score) if st else 0


func _lives(gm: Node) -> int:
	var st := get_node_or_null("/root/VibeState")
	return int(st.lives) if st else 0


func _spec_lives(gm: Node) -> int:
	return int(gm.spec.get("progression", {}).get("lives", 3))


# ---------------------------------------------------------------- verdict
func _check(name: String, ok: bool) -> void:
	_checks.append({"name": name, "ok": ok})
	print("VIBE_TEST CHECK %s=%s" % [name, "PASS" if ok else "FAIL"])


func _emit_verdict() -> void:
	var failed: Array = []
	for c in _checks:
		if not c.ok:
			failed.append(c.name)
	var verdict := "PASS" if failed.is_empty() else "FAIL"
	print("VIBE_TEST RESULT verdict=%s checks=%d failed=%s" % [verdict, _checks.size(), str(failed)])
	get_tree().quit()


func _emit_verdict_missing(reason: String) -> void:
	print("VIBE_TEST RESULT verdict=FAIL checks=0 failed=[%s]" % reason)
	get_tree().quit()
