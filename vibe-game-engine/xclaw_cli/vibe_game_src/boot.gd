extends Node2D
# vibe_game boot scene — the real-play entry point (project main_scene).
# Hands the scene root to the GameManager autoload, which builds the menu/level.

func _ready() -> void:
	if has_node("/root/GameManager"):
		get_node("/root/GameManager").start(self)
