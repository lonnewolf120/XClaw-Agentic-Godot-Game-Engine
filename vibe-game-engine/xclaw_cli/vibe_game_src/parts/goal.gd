extends Area2D
# Level goal. Touching it (player only) ends the level.

func _ready() -> void:
	monitoring = true
	add_to_group("goal")
	body_entered.connect(_on_body_entered)

func _on_body_entered(body: Node) -> void:
	if body.is_in_group("player") and has_node("/root/VibeEvents"):
		get_node("/root/VibeEvents").goal_reached.emit()
