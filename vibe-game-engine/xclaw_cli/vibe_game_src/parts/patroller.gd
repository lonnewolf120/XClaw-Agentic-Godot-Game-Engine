extends Area2D
# Patrolling enemy. Ping-pongs horizontally around its start x; lethal on contact.
# Motion is a deterministic function of elapsed physics time (reproducible in the gate).

var range_px: float = 120.0
var speed: float = 60.0
var _origin_x: float = 0.0
var _t: float = 0.0

func _ready() -> void:
	monitoring = true
	add_to_group("enemy")
	_origin_x = global_position.x
	body_entered.connect(_on_body_entered)

func _physics_process(delta: float) -> void:
	_t += delta
	var omega: float = speed / max(range_px, 1.0)
	global_position.x = _origin_x + sin(_t * omega) * range_px

func _on_body_entered(body: Node) -> void:
	if body.is_in_group("player") and has_node("/root/VibeEvents"):
		get_node("/root/VibeEvents").player_died.emit()
