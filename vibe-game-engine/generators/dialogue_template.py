PROJECT_GODOT = """config_version=5

[application]

config/name="Vibe Dialogue Engine"
run/main_scene="res://scenes/main.tscn"
config/features=PackedStringArray("4.6", "Forward Plus")

[file_customization]
folder_colors={
"res://assets/": "red",
"res://scenes/": "blue",
"res://scripts/": "green",
"res://data/": "yellow"
}
"""

MAIN_SCENE = """[gd_scene load_steps=2 format=3 uid="uid://main_scene_003"]

[ext_resource type="Script" path="res://scripts/dialogue_manager.gd" id="1_manager"]

[node name="Main" type="Control"]
layout_mode = 3
anchors_preset = 15
script = ExtResource("1_manager")

[node name="Background" type="TextureRect" parent="."]
layout_mode = 1
anchors_preset = 15
grow_horizontal = 2
grow_vertical = 2

[node name="CharacterSprite" type="TextureRect" parent="."]
layout_mode = 1
anchors_preset = 7
anchor_left = 0.5
anchor_top = 1.0
anchor_right = 0.5
anchor_bottom = 1.0
offset_left = -150.0
offset_top = -400.0
offset_right = 150.0

[node name="DialogueBox" type="Panel" parent="."]
layout_mode = 1
anchors_preset = 12
anchor_top = 1.0
anchor_right = 1.0
anchor_bottom = 1.0
offset_top = -150.0

[node name="TextLabel" type="RichTextLabel" parent="DialogueBox"]
layout_mode = 1
anchors_preset = 15
grow_horizontal = 2
grow_vertical = 2
"""

MANAGER_SCRIPT = """extends Control

var current_line = 0
var dialogue_data = [
\t{"name": "Guide", "text": "Welcome to the narrative game template!"},
\t{"name": "Guide", "text": "Click or press Space to advance."},
\t{"name": "Guide", "text": "Enjoy building your story."}
]

func _ready():
\tprint("Dialogue Manager Initialized.")
\tshow_line(0)

func _input(event):
\tif event.is_action_pressed("ui_accept") or (event is InputEventMouseButton and event.pressed):
\t\tnext_line()

func show_line(idx):
\tif idx < dialogue_data.size():
\t\t$DialogueBox/TextLabel.text = dialogue_data[idx]["name"] + ": " + dialogue_data[idx]["text"]
\telse:
\t\t$DialogueBox/TextLabel.text = "--- End of Dialogue ---"

func next_line():
\tcurrent_line += 1
\tshow_line(current_line)
"""

DIALOGUE_FILES = {
    "project.godot": PROJECT_GODOT,
    "scenes/main.tscn": MAIN_SCENE,
    "scripts/dialogue_manager.gd": MANAGER_SCRIPT
}
