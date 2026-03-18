import os

files = [
    r'E:\Projects\GAMEDEV\XClaw Agentic Godot Game Engine\vibe-game-engine\agents\planner.py',
    r'E:\Projects\GAMEDEV\XClaw Agentic Godot Game Engine\vibe-game-engine\agents\builder.py'
]

for path in files:
    with open(path, 'r') as f:
        text = f.read()

    text = text.replace('response_schema=PlanMessage', '')
    text = text.replace('response_schema=ActionBatch', '')
    text = text.replace(',\n            \n        )', '\n        )')
    text = text.replace(',\n            \n', '\n')
    text = text.replace('config = types.GenerateContentConfig(\n            response_mime_type="application/json",\n            \n        )', 'config = types.GenerateContentConfig(\n            response_mime_type="application/json"\n        )')
    text = text.replace('config = types.GenerateContentConfig(\n            response_mime_type=\'application/json\',\n            \n        )', 'config = types.GenerateContentConfig(\n            response_mime_type=\'application/json\'\n        )')
    
    with open(path, 'w') as f:
        f.write(text)

print("Removed schema enforcement to prevent 400 error")
