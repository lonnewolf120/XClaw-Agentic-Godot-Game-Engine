extends Area2D
# Hazard (spike / pit trigger). Touching it (player only) kills the player.

func _ready() -> void:
	monitoring = true
	add_to_group("hazard")
	body_entered.connect(_on_body_entered)

func _on_body_entered(body: Node) -> void:
	if body.is_in_group("player") and has_node("/root/VibeEvents"):
		get_node("/root/VibeEvents").player_died.emit()
