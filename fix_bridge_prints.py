import os

path = r'E:\Projects\GAMEDEV\XClaw Agentic Godot Game Engine\vibe-game-engine\api\plugin_bridge.py'
with open(path, 'r') as f:
    text = f.read()

text = text.replace('logger.info(f"Generating proposal for: {req.prompt}")', 'logger.info(f"Generating proposal for: {req.prompt}"); print(f"*** NEW PROPOSAL REQUEST: {req.prompt} ***")')

with open(path, 'w') as f:
    f.write(text)
print("Updated bridge prints")
