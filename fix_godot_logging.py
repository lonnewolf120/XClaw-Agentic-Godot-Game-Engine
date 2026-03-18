import os
import re

path = r'E:\Projects\GAMEDEV\XClaw Agentic Godot Game Engine\templates\Starter-Kit-3D-Platformer\addons\xclaw_agentic_engine\xclaw_dock.gd'
with open(path, 'r') as f:
    text = f.read()

replacement = """func system_log(msg: String, error: bool = false) -> void:
    var time_dict = Time.get_time_dict_from_system()
    var time_str = "[%02d:%02d:%02d]" % [time_dict.hour, time_dict.minute, time_dict.second]
    var line = "\\n" + time_str + " " + msg
    if error:
        line = "\\n[color=red]" + time_str + " ERROR: " + msg + "[/color]"
        push_error("[XClaw] " + msg)
    else:
        print("[XClaw] " + msg)
        
    if log_terminal:
        log_terminal.text += line
"""

text = re.sub(r'func system_log\(msg: String, error: bool = false\) -> void:.*?if log_terminal:.*?log_terminal\.text \+= line', replacement, text, flags=re.DOTALL)

with open(path, 'w') as f:
    f.write(text)
print("Updated Godot logging")
