extends Area2D
# Chasing enemy. Tracks the player's X position (keeps its own Y, so a ledge-placed chaser
# stays off the ground path), capped slower than the player so it can be out-run. Lethal on contact.

var speed: float = 70.0
var _player: Node2D = null

func _ready() -> void:
	monitoring = true
	add_to_group("enemy")
	body_entered.connect(_on_body_entered)

func _physics_process(delta: float) -> void:
	if _player == null or not is_instance_valid(_player):
		var players := get_tree().get_nodes_in_group("player")
		_player = players[0] if not players.is_empty() else null
	if _player == null:
		return
	var dx: float = _player.global_position.x - global_position.x
	if abs(dx) > 2.0:
		global_position.x += signf(dx) * speed * delta

func _on_body_entered(body: Node) -> void:
	if body.is_in_group("player") and has_node("/root/VibeEvents"):
		get_node("/root/VibeEvents").player_died.emit()
