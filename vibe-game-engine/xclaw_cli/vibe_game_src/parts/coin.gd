extends Area2D
# Scoring collectible. Picked up once by the player.

@export var amount: int = 10
var _taken := false

func _ready() -> void:
	monitoring = true
	add_to_group("coin")
	body_entered.connect(_on_body_entered)

func _on_body_entered(body: Node) -> void:
	if _taken or not body.is_in_group("player"):
		return
	_taken = true
	if has_node("/root/VibeState"):
		get_node("/root/VibeState").add_score(amount)
	if has_node("/root/VibeEvents"):
		get_node("/root/VibeEvents").coin_collected.emit(amount)
	queue_free()
