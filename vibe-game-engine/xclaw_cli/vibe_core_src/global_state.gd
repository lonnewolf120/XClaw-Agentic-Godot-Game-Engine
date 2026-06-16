extends Node
# VibeCore: Central State Management
# Holds the "Truth" of the game session.

var score: int = 0:
	set(v):
		score = v
		if has_node("/root/VibeEvents"):
			get_node("/root/VibeEvents").score_changed.emit(score)

var player_health: float = 100.0:
	set(v):
		player_health = clamp(v, 0, max_player_health)
		if has_node("/root/VibeEvents"):
			get_node("/root/VibeEvents").health_changed.emit(null, player_health, max_player_health)

var max_player_health: float = 100.0
var is_game_active: bool = false
var game_time: float = 0.0

# --- vibe_game runtime (schema-driven authoring) ---
var lives: int = 3:
	set(v):
		lives = v
		if has_node("/root/VibeEvents"):
			get_node("/root/VibeEvents").lives_changed.emit(lives)
var level: int = 1  # current level number, 1-based (for HUD / progression display)

func add_score(amount: int) -> void:
	score += amount

func _process(delta):
	if is_game_active:
		game_time += delta

func reset_session():
	score = 0
	player_health = max_player_health
	game_time = 0.0
	lives = 3
	level = 1
	is_game_active = true
	print("[VibeState] Session Reset")
