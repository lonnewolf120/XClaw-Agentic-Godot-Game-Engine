import os
path = r'E:\Projects\GAMEDEV\XClaw Agentic Godot Game Engine\templates\Starter-Kit-3D-Platformer\addons\xclaw_agentic_engine\xclaw_dock.gd'
with open(path, 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.startswith('@onready var chat_display'):
        new_lines.append('@onready var chat_display: RichTextLabel = ' + chr(36) + 'VBoxContainer/TabContainer/Agent/ChatDisplay\n')
    elif line.startswith('@onready var prompt_input'):
        new_lines.append('@onready var prompt_input: LineEdit = ' + chr(36) + 'VBoxContainer/TabContainer/Agent/HBoxContainer/PromptInput\n')
    elif line.startswith('@onready var submit_btn'):
        new_lines.append('@onready var submit_btn: Button = ' + chr(36) + 'VBoxContainer/TabContainer/Agent/HBoxContainer/SubmitBtn\n')
    elif line.startswith('@onready var status_lbl'):
        new_lines.append('@onready var status_lbl: Label = ' + chr(36) + 'VBoxContainer/HeaderBar/Status\n')
    elif line.startswith('@onready var auto_apply_check'):
        new_lines.append('@onready var auto_apply_check: CheckButton = ' + chr(36) + 'VBoxContainer/HeaderBar/AutoApplyCheck\n')
    elif line.startswith('@onready var connection_indicator'):
        new_lines.append('@onready var connection_indicator: ColorRect = ' + chr(36) + 'VBoxContainer/HeaderBar/ConnectionIndicator\n')
    elif line.startswith('@onready var log_terminal'):
        new_lines.append('@onready var log_terminal: RichTextLabel = ' + chr(36) + 'VBoxContainer/TabContainer/Logs/LogTerminal\n')
    elif line.startswith('@onready var backend_url_input'):
        new_lines.append('@onready var backend_url_input: LineEdit = ' + chr(36) + 'VBoxContainer/TabContainer/Config/BackendUrlHBox/BackendUrlInput\n')
    else:
        new_lines.append(line)

with open(path, 'w') as f:
    f.writelines(new_lines)
print('Fixed dollars.')
