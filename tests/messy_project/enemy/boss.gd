extends CharacterBody2D
signal health_changed(new_health)

var current_health = 1000

func _physics_process(delta):
    # This intentionally has a parse error for the debugger to find
    if get_global_mouse_position()
        print("mouse")
    
func take_damage(amt):
    current_health -= amt 
    emit_signal("health_changed", current_health)
