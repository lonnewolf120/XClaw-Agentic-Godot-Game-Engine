extends CharacterBody2D
# Hand-authored Phase-1 platformer controller (stands in for the AI's player script).
# Uses ONLY built-in input actions (ui_left / ui_right / ui_accept) so it always resolves
# and the test bot knows exactly which actions to synthesize.

const SPEED := 240.0
const JUMP_VELOCITY := -560.0
const GRAVITY := 1300.0

func _physics_process(delta: float) -> void:
	if not is_on_floor():
		velocity.y += GRAVITY * delta
	if is_on_floor() and Input.is_action_just_pressed("ui_accept"):
		velocity.y = JUMP_VELOCITY
	var dir := Input.get_axis("ui_left", "ui_right")
	velocity.x = dir * SPEED
	move_and_slide()
