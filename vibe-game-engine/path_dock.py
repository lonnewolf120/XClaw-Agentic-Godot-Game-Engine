import os, re
path_gd = r'E:\Projects\GAMEDEV\XClaw Agentic Godot Game Engine\templates\Starter-Kit-3D-Platformer\addons\xclaw_agentic_engine\xclaw_dock.gd'
path_tscn = r'E:\Projects\GAMEDEV\XClaw Agentic Godot Game Engine\templates\Starter-Kit-3D-Platformer\addons\xclaw_agentic_engine\xclaw_dock.tscn'

# Patch tscn
with open(path_tscn, 'r') as f:
    tscn = f.read()

# Add ApiKeyHBox right after BackendUrlInput definition
tscn_snip = '''[node name="ApiKeyHBox" type="HBoxContainer" parent="VBoxContainer/TabContainer/Config"]
layout_mode = 2

[node name="Label" type="Label" parent="VBoxContainer/TabContainer/Config/ApiKeyHBox"]
layout_mode = 2
text = "Gemini API Key:"

[node name="ApiKeyInput" type="LineEdit" parent="VBoxContainer/TabContainer/Config/ApiKeyHBox"]
layout_mode = 2
size_flags_horizontal = 3
text = ""
secret = true
'''

if 'ApiKeyHBox' not in tscn:
    tscn = tscn.replace('text = "http://127.0.0.1:8000"\n', 'text = "http://127.0.0.1:8000"\n\n' + tscn_snip)
    with open(path_tscn, 'w') as f:
        f.write(tscn)
    print("Patched tscn")

# Patch gd
with open(path_gd, 'r') as f:
    gd = f.read()

if 'api_key_input' not in gd:
    gd = gd.replace('@onready var backend_url_input', '@onready var api_key_input: LineEdit = /TabContainer/Config/ApiKeyHBox/ApiKeyInput\n@onready var backend_url_input')
    
    # modify _send_proposal_request to include api_key
    # Find payload definition
    gd = gd.replace('"prompt": prompt_input.text\n\t}', '"prompt": prompt_input.text,\n\t\t"options": { "api_key": api_key_input.text }\n\t}')
    
    with open(path_gd, 'w') as f:
        f.write(gd)
    print("Patched gd")
    
