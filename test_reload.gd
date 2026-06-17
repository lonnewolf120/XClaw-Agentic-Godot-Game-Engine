@tool
extends EditorScript

func _run():
    var editor = get_editor_interface()
    editor.set_plugin_enabled("xclaw_agentic_engine", false)
    editor.set_plugin_enabled("xclaw_agentic_engine", true)
    print("Plugin reloaded!")
