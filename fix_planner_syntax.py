import os
path = r'E:\Projects\GAMEDEV\XClaw Agentic Godot Game Engine\vibe-game-engine\agents\planner.py'
with open(path, 'r') as f:
    text = f.read()

import re
text = re.sub(r'text=system \+ ".*?\n"\s*\+ initial_prompt', 'text=system + "\\\n" + initial_prompt', text, flags=re.DOTALL)

with open(path, 'w') as f:
    f.write(text)
print('Fixed planner syntax')
