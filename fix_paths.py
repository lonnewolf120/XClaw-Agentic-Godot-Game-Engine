import os
path = r'E:\Projects\GAMEDEV\XClaw Agentic Godot Game Engine\templates\Starter-Kit-3D-Platformer\addons\xclaw_agentic_engine\xclaw_dock.gd'
with open(path, 'r') as f:
    text = f.read()

text = text.replace('\/TabContainer/Agent/ChatDisplay', '\/TabContainer/Agent/ChatDisplay')
text = text.replace('\/TabContainer/Agent/HBoxContainer/PromptInput', '\/TabContainer/Agent/HBoxContainer/PromptInput')
text = text.replace('\/TabContainer/Agent/HBoxContainer/SubmitBtn', '\/TabContainer/Agent/HBoxContainer/SubmitBtn')
text = text.replace('\/HeaderBar/Status', '\/HeaderBar/Status')
text = text.replace('\/HeaderBar/AutoApplyCheck', '\/HeaderBar/AutoApplyCheck')
text = text.replace('\/HeaderBar/ConnectionIndicator', '\/HeaderBar/ConnectionIndicator')
text = text.replace('\/TabContainer/Logs/LogTerminal', '\/TabContainer/Logs/LogTerminal')
text = text.replace('\/TabContainer/Config/BackendUrlHBox/BackendUrlInput', '\/TabContainer/Config/BackendUrlHBox/BackendUrlInput')

with open(path, 'w') as f:
    f.write(text.replace('\\$', '$'))

print('Fixed NodePaths!')
