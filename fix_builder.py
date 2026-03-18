import os
path = r'E:\Projects\GAMEDEV\XClaw Agentic Godot Game Engine\vibe-game-engine\agents\builder.py'
with open(path, 'r') as f:
    text = f.read()

import re
text = re.sub(r'user_prompt = f"Plan:(.*?)"\n\n        contents = \[', r'user_prompt = f\"\"\"Plan:\1\"\"\"\n\n        contents = [', text, flags=re.DOTALL)

with open(path, 'w') as f:
    f.write(text)
