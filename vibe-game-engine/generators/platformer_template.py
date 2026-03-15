PROJECT_GODOT = """config_version=5

[application]

config/name="Vibe Platformer"
run/main_scene="res://scenes/main.tscn"
config/features=PackedStringArray("4.6", "Forward Plus")

[file_customization]
folder_colors={
"res://assets/": "red",
"res://scenes/": "blue",
"res://scripts/": "green"
}
"""

MAIN_SCENE = """[gd_scene load_steps=2 format=3 uid="uid://main_scene_001"]

[ext_resource type="Script" path="res://scripts/game_manager.gd" id="1_manager"]

[node name="Main" type="Node2D"]
script = ExtResource("1_manager")

[node name="Level" type="Node2D" parent="."]

[node name="Ground" type="StaticBody2D" parent="Level"]
position = Vector2(0, 600)

[node name="CollisionShape2D" type="CollisionShape2D" parent="Level/Ground"]
# Placeholder for shape

[node name="PlayerSpawn" type="Marker2D" parent="."]
position = Vector2(100, 500)
"""

PLAYER_SCENE = """[gd_scene load_steps=2 format=3 uid="uid://player_scene_001"]

[ext_resource type="Script" path="res://scripts/player.gd" id="1_player"]

[node name="Player" type="CharacterBody2D"]
script = ExtResource("1_player")

[node name="Sprite2D" type="Sprite2D" parent="."]
# Placeholder for texture

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
# Placeholder for shape

[node name="Camera2D" type="Camera2D" parent="."]
current = true
"""

PLAYER_SCRIPT = """extends CharacterBody2D

const SPEED = 300.0
const JUMP_VELOCITY = -400.0

var gravity = ProjectSettings.get_setting("physics/2d/default_gravity")

def _physics_process(delta):
\tvar dir = Input.get_axis("ui_left", "ui_right")
\tif dir:
\t\tvelocity.x = dir * SPEED
\telse:
\t\tvelocity.x = move_toward(velocity.x, 0, SPEED)

\tif not is_on_floor():
\t\tvelocity.y += gravity * delta
\telif Input.is_action_just_pressed("ui_accept"):
\t\tvelocity.y = JUMP_VELOCITY

\tmove_and_slide()
"""

GAME_MANAGER_SCRIPT = """extends Node

func _ready():
\tprint("Game Manager Initialized. Platformer scaffold ready.")
"""

PLATFORMER_FILES = {
    "project.godot": PROJECT_GODOT,
    "scenes/main.tscn": MAIN_SCENE,
    "scenes/player.tscn": PLAYER_SCENE,
    "scripts/player.gd": PLAYER_SCRIPT,
    "scripts/game_manager.gd": GAME_MANAGER_SCRIPT
}
