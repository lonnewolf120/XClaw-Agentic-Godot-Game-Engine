extends CharacterBody2D

const SPEED := 220.0

func _physics_process(_delta: float) -> void:
    var direction := Vector2(
        Input.get_action_strength("ui_right") - Input.get_action_strength("ui_left"),
        Input.get_action_strength("ui_down") - Input.get_action_strength("ui_up")
    )
    if direction.length() > 1.0:
        direction = direction.normalized()

    velocity = direction * SPEED
    move_and_slide()
