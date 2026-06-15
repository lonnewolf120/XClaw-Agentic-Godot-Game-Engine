extends Node
# VibeCore: MoveTrait
# Adds basic WASD/Arrow movement to the parent node.

@export var speed: float = 10.0
var parent: Node3D

func _ready():
	parent = get_parent() as Node3D
	if not parent:
		set_process(false)
		print("[MoveTrait] Error: Parent must be Node3D")

func _process(delta):
	var input_dir = Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	var direction = Vector3(input_dir.x, 0, input_dir.y).normalized()
	if direction:
		parent.global_translate(direction * speed * delta)
