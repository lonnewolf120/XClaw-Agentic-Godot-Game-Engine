import os
path = r'e:/Projects/GAMEDEV/XClaw Agentic Godot Game Engine/templates/Starter-Kit-3D-Platformer/addons/xclaw_agentic_engine/plugin.gd'
with open(path, 'r') as ff:
    t = ff.read()
t = t.replace('undo_redo.add_do_method(pair[\'do_method\'])', 'undo_redo.add_do_method(pair[\'do_method\'].get_object(), pair[\'do_method\'].get_method())')
t = t.replace('undo_redo.add_undo_method(pair[\'undo_method\'])', 'undo_redo.add_undo_method(pair[\'undo_method\'].get_object(), pair[\'undo_method\'].get_method())')
with open(path, 'w') as ff:
    ff.write(t)
print('Patched')
