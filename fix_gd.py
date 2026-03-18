import os
path = r'E:\Projects\GAMEDEV\XClaw Agentic Godot Game Engine\templates\Starter-Kit-3D-Platformer\addons\xclaw_agentic_engine\xclaw_dock.gd'
with open(path, 'r') as f:
    text = f.read()

text = text.replace('@onready var api_key_input: LineEdit = \n/TabContainer/Config/ApiKeyHBox/ApiKeyInput', '@onready var api_key_input: LineEdit = /TabContainer/Config/ApiKeyHBox/ApiKeyInput')
text = text.replace('@onready var api_key_input: LineEdit = /TabContainer/Config/ApiKeyHBox/ApiKeyInput', '@onready var api_key_input: LineEdit = /TabContainer/Config/ApiKeyHBox/ApiKeyInput')

with open(path, 'w') as f:
    f.write(text)
