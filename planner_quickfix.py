import os
path = r'E:\Projects\GAMEDEV\XClaw Agentic Godot Game Engine\vibe-game-engine\agents\planner.py'
with open(path, 'r') as f:
    text = f.read()

import re
text = re.sub(r'contents = \[types\.Content\(role="user", parts=\[types\.Part\.from_text\(text=.*?\]\)\]', 'contents = [types.Content(role="user", parts=[types.Part.from_text(text=system + "\\\n" + initial_prompt)])]', text, flags=re.DOTALL)

with open(path, 'w') as f:
    f.write(text)
