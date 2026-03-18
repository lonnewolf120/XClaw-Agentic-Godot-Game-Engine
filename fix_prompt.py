import os
import re

path = r'E:\Projects\GAMEDEV\XClaw Agentic Godot Game Engine\vibe-game-engine\agents\builder.py'
with open(path, 'r') as f:
    text = f.read()

text = text.replace('Build the JSON ActionBatch."""""', 'Build the JSON ActionBatch."""')
with open(path, 'w') as f:
    f.write(text)
