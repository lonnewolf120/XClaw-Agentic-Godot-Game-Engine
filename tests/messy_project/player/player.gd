extends CharacterBody2D
signal health_changed(new_health)

var speed = 100

func _physics_process(delta):
    # Messy empty function
    pass

func take_damage(amt):
    # Undefined variable reference bug to trigger Debugger
    current_health -= amt 
    emit_signal("health_changed", current_health)
