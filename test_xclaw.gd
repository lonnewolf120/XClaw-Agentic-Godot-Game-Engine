extends SceneTree
func _init():
    var p = load("res://addons/xclaw_agentic_engine/plugin.gd")
    if p:
        print("LOADED")
    else:
        print("FAILED TO LOAD PLUGIN")
    quit()
