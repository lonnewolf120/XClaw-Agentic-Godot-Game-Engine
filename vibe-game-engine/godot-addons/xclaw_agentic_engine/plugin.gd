@tool
extends EditorPlugin

var dock: Control

func _enter_tree() -> void:
    # Initialization of the plugin goes here.
    # Instantiate the dock control
    dock = preload("res://addons/xclaw_agentic_engine/xclaw_dock.tscn").instantiate()
    
    # Add the loaded scene to the bottom/right dock
    add_control_to_dock(DOCK_SLOT_RIGHT_BL, dock)


func _exit_tree() -> void:
    # Clean-up of the plugin goes here.
    if dock:
        remove_control_from_docks(dock)
        dock.queue_free()
