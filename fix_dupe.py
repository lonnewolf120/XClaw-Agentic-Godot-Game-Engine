import os
import re
path = r'E:\Projects\GAMEDEV\XClaw Agentic Godot Game Engine\templates\Starter-Kit-3D-Platformer\addons\xclaw_agentic_engine\xclaw_dock.gd'
with open(path, 'r') as f:
    text = f.read()

text = text.replace('"options": { "api_key": api_key_input.text },\n        "options": { "api_key": api_key_input.text }', '"options": { "api_key": api_key_input.text }')

with open(path, 'w') as f:
    f.write(text)
print("deduped")
