extends CharacterBody3D
class_name VibeEntity
# VibeCore: Optimized Base Entity
# Provides standardized components for health, damage, and presence.

@export_group("Vibe Physics")
@export var movement_speed: float = 5.0
@export var acceleration: float = 10.0

@export_group("Vibe Combat")
@export var max_health: float = 100.0
@onready var health: float = max_health

func take_damage(amount: float):
	health -= amount
	if has_node("/root/VibeEvents"):
		get_node("/root/VibeEvents").health_changed.emit(self, health, max_health)
	
	if health <= 0:
		die()

func die():
	# Override this for custom death logic (animations, effects)
	print("[VibeEntity] Died: ", name)
	queue_free()

func _physics_process(_delta):
	# Subclasses should implement actual logic
	pass
