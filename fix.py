import os
path = r'E:\Projects\GAMEDEV\XClaw Agentic Godot Game Engine\templates\Starter-Kit-3D-Platformer\addons\xclaw_agentic_engine\xclaw_dock.gd'
with open(path, 'r') as f:
    text = f.read()

text = text.replace(
    'if log_terminal:\n        log_terminal.text = "[color=gray]System initialized.[/color]"',
    'if log_terminal:\n        log_terminal.text = "[color=gray]System initialized.[/color]"\n    setup_connections()'
)

with open(path, 'w') as f:
    f.write(text)
print('Fixed!')
