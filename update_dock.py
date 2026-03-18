import os

tscn = """[gd_scene load_steps=2 format=3 uid="uid://xclaw_dock_1"]

[ext_resource type="Script" path="res://addons/xclaw_agentic_engine/xclaw_dock.gd" id="1_bdk"]

[node name="XClawAgent" type="Control"]
layout_mode = 3
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
grow_horizontal = 2
grow_vertical = 2
script = ExtResource("1_bdk")

[node name="VBoxContainer" type="VBoxContainer" parent="."]
layout_mode = 1
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
grow_horizontal = 2
grow_vertical = 2

[node name="HeaderBar" type="HBoxContainer" parent="VBoxContainer"]
layout_mode = 2

[node name="ConnectionIndicator" type="ColorRect" parent="VBoxContainer/HeaderBar"]
custom_minimum_size = Vector2(16, 16)
layout_mode = 2
size_flags_vertical = 4
color = Color(1, 0, 0, 1)

[node name="Label" type="Label" parent="VBoxContainer/HeaderBar"]
layout_mode = 2
text = "XClaw"

[node name="AutoApplyCheck" type="CheckButton" parent="VBoxContainer/HeaderBar"]
layout_mode = 2
text = "Auto-Poll"

[node name="Status" type="Label" parent="VBoxContainer/HeaderBar"]
layout_mode = 2
size_flags_horizontal = 3
text = "Idle"
horizontal_alignment = 2

[node name="TabContainer" type="TabContainer" parent="VBoxContainer"]
layout_mode = 2
size_flags_vertical = 3

[node name="Agent" type="VBoxContainer" parent="VBoxContainer/TabContainer"]
layout_mode = 2

[node name="ChatDisplay" type="RichTextLabel" parent="VBoxContainer/TabContainer/Agent"]
layout_mode = 2
size_flags_vertical = 3
bbcode_enabled = true
text = "Welcome to XClaw Agentic Game Engine.
Select a node and tell me what to build."

[node name="HBoxContainer" type="HBoxContainer" parent="VBoxContainer/TabContainer/Agent"]
layout_mode = 2

[node name="PromptInput" type="LineEdit" parent="VBoxContainer/TabContainer/Agent/HBoxContainer"]
layout_mode = 2
size_flags_horizontal = 3
placeholder_text = "Prompt..."

[node name="SubmitBtn" type="Button" parent="VBoxContainer/TabContainer/Agent/HBoxContainer"]
layout_mode = 2
text = "Apply"

[node name="Logs" type="VBoxContainer" parent="VBoxContainer/TabContainer"]
visible = false
layout_mode = 2

[node name="LogTerminal" type="RichTextLabel" parent="VBoxContainer/TabContainer/Logs"]
layout_mode = 2
size_flags_vertical = 3
bbcode_enabled = true
scroll_following = true

[node name="Config" type="VBoxContainer" parent="VBoxContainer/TabContainer"]
visible = false
layout_mode = 2

[node name="BackendUrlHBox" type="HBoxContainer" parent="VBoxContainer/TabContainer/Config"]
layout_mode = 2

[node name="Label" type="Label" parent="VBoxContainer/TabContainer/Config/BackendUrlHBox"]
layout_mode = 2
text = "Backend URL:"

[node name="BackendUrlInput" type="LineEdit" parent="VBoxContainer/TabContainer/Config/BackendUrlHBox"]
layout_mode = 2
size_flags_horizontal = 3
text = "http://127.0.0.1:8000"
"""

gd = """@tool
extends Control

@onready var chat_display: RichTextLabel = \/TabContainer/Agent/ChatDisplay
@onready var prompt_input: LineEdit = \/TabContainer/Agent/HBoxContainer/PromptInput
@onready var submit_btn: Button = \/TabContainer/Agent/HBoxContainer/SubmitBtn
@onready var status_lbl: Label = \/HeaderBar/Status
@onready var auto_apply_check: CheckButton = \/HeaderBar/AutoApplyCheck
@onready var connection_indicator: ColorRect = \/HeaderBar/ConnectionIndicator
@onready var log_terminal: RichTextLabel = \/TabContainer/Logs/LogTerminal
@onready var backend_url_input: LineEdit = \/TabContainer/Config/BackendUrlHBox/BackendUrlInput

var plugin: EditorPlugin
var current_proposal_id: String = ""
var current_actions: Array = []
var poll_timer: Timer
var health_timer: Timer
var is_connected_to_backend = false

func _ready() -> void:
    poll_timer = Timer.new()
    poll_timer.wait_time = 1.5
    poll_timer.autostart = true
    poll_timer.timeout.connect(_on_poll_timer)
    add_child(poll_timer)

    health_timer = Timer.new()
    health_timer.wait_time = 3.0
    health_timer.autostart = true
    health_timer.timeout.connect(_on_health_ping)
    add_child(health_timer)
    
    if log_terminal:
        log_terminal.text = "[color=gray]System initialized.[/color]"

func get_backend_url() -> String:
    if backend_url_input:
        return backend_url_input.text.strip_edges()
    return "http://127.0.0.1:8000"

func system_log(msg: String, error: bool = false) -> void:
    var time_dict = Time.get_time_dict_from_system()
    var time_str = "[%02d:%02d:%02d]" % [time_dict.hour, time_dict.minute, time_dict.second]
    var line = "\\n" + time_str + " " + msg
    if error:
        line = "\\n[color=red]" + time_str + " ERROR: " + msg + "[/color]"
        
    print("[XClaw] ", msg)
    if log_terminal:
        log_terminal.text += line

func set_plugin(p_plugin: EditorPlugin) -> void:
    plugin = p_plugin
    setup_connections()

func _enter_tree() -> void:
    setup_connections()

func setup_connections() -> void:
    if submit_btn and not submit_btn.pressed.is_connected(_on_submit):
        submit_btn.pressed.connect(_on_submit)
    if prompt_input and not prompt_input.text_submitted.is_connected(_on_submit_text):
        prompt_input.text_submitted.connect(_on_submit_text)

func _on_submit() -> void:
    if prompt_input:
        _on_submit_text(prompt_input.text)

func _on_submit_text(text: String) -> void:
    var t = text.strip_edges()
    if t == "": return
    
    chat_display.text += "\\n[color=lightblue]You:[/color] " + t
    prompt_input.text = ""
    system_log("Command input: " + t)
    
    if t == "/accept" or t == "accept":
        if current_proposal_id != "": _send_apply_request()
        else: system_log("No pending proposal to accept", true)
        return
    elif t == "/reject" or t == "reject":
        if current_proposal_id != "": reject_proposal()
        else: system_log("No pending proposal to reject", true)
        return

    status_lbl.text = "Thinking..."
    
    var selected_nodes = EditorInterface.get_selection().get_selected_nodes()
    var context_dump = []
    for node in selected_nodes:
        context_dump.append({"name": node.name, "class_name": node.get_class(), "path": str(node.get_path())})
    
    if plugin: plugin.has_pending_proposals = true
    chat_display.text += "\\n[color=yellow]Agent:[/color] Requesting proposal from orchestrator..."
    _send_proposal_request(t, context_dump)

func _on_health_ping() -> void:
    var http = HTTPRequest.new()
    add_child(http)
    http.request_completed.connect(_on_health_completed.bind(http))
    http.request(get_backend_url() + "/health", ["Content-Type: application/json"], HTTPClient.METHOD_GET)

func _on_health_completed(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray, http: HTTPRequest) -> void:
    http.queue_free()
    if response_code == 200:
        if not is_connected_to_backend:
            system_log("Connected to AI Backend.")
        is_connected_to_backend = true
        if connection_indicator: connection_indicator.color = Color(0, 1, 0, 1) # Green
    else:
        if is_connected_to_backend:
            system_log("Lost connection to AI Backend.", true)
        is_connected_to_backend = false
        if connection_indicator: connection_indicator.color = Color(1, 0, 0, 1) # Red

func _on_poll_timer() -> void:
    if not auto_apply_check or not auto_apply_check.button_pressed: return
    if current_proposal_id != "": return
    if not is_connected_to_backend: return
    
    var http = HTTPRequest.new()
    add_child(http)
    http.request_completed.connect(_on_poll_completed.bind(http))
    http.request(get_backend_url() + "/plugin/poll", ["Content-Type: application/json"], HTTPClient.METHOD_GET)

func _on_poll_completed(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray, http: HTTPRequest) -> void:
    http.queue_free()
    if response_code != 200: return
    
    var json_str = body.get_string_from_utf8()
    var json = JSON.parse_string(json_str)
    if typeof(json) != TYPE_DICTIONARY: return
    if json.has("status") and json.get("status") == "empty": return
    
    system_log("Polled new proposal from dashboard.")
    chat_display.text += "\\n[color=yellow]Agent:[/color] Received remote actions. Auto-applying..."
    preview_proposal(json)
    if current_proposal_id != "":
        _send_apply_request()

func _send_proposal_request(prompt: String, context_dump: Array) -> void:
    var http = HTTPRequest.new()
    add_child(http)
    http.request_completed.connect(_on_proposal_completed.bind(http))
    
    var body = JSON.stringify({
        "prompt": prompt,
        "selection": context_dump,
        "mode": "scene_mutation"
    })
    system_log("Sending proposal request (AI Generation)...")
    http.request(get_backend_url() + "/plugin/proposal", ["Content-Type: application/json"], HTTPClient.METHOD_POST, body)

func _on_proposal_completed(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray, http: HTTPRequest) -> void:
    http.queue_free()
    if response_code != 200:
        system_log("Failed to reach orchestrator (Code %d)" % response_code, true)
        status_lbl.text = "API Error"
        if plugin: plugin.has_pending_proposals = false
        return
        
    var json = JSON.parse_string(body.get_string_from_utf8())
    if typeof(json) != TYPE_DICTIONARY:
        system_log("Invalid JSON from orchestrator", true)
        if plugin: plugin.has_pending_proposals = false
        return
        
    preview_proposal(json)

func preview_proposal(proposal: Dictionary) -> void:
    current_proposal_id = proposal.get("proposal_id", "")
    current_actions = proposal.get("actions", [])
    
    system_log("Previewing proposal: " + current_proposal_id)
    chat_display.text += "\\n[color=cyan][XClaw][/color] Validating native batch..."
    
    if ClassDB.class_exists("EditorAIActions"):
        var ai = ClassDB.instantiate("EditorAIActions")
        var preview_receipts = ai.call("preview_action_batch", current_actions)
        system_log("Native Preview Receipts: " + str(preview_receipts))
    else:
        system_log("EditorAIActions C++ module not found", true)
        
    status_lbl.text = "Review Proposal"
    if plugin: plugin.has_pending_proposals = true

func reject_proposal() -> void:
    system_log("Proposal rejected by user.")
    current_proposal_id = ""
    current_actions = []
    if plugin: plugin.has_pending_proposals = false
    status_lbl.text = "Idle"
    chat_display.text += "\\n[color=gray]System:[/color] Proposal rejected."
    
func _send_apply_request() -> void:
    status_lbl.text = "Applying..."
    var receipts = []
    
    if ClassDB.class_exists("EditorAIActions"):
        var ai = ClassDB.instantiate("EditorAIActions")
        receipts = ai.call("apply_action_batch", current_actions)
        system_log("Applied native batch: " + str(receipts))
    else:
        system_log("EditorAIActions module missing!", true)
        status_lbl.text = "Error"
        return
        
    var http = HTTPRequest.new()
    add_child(http)
    http.request_completed.connect(_on_apply_completed.bind(http))
    
    var body = JSON.stringify({
        "proposal_id": current_proposal_id,
        "native_receipts": receipts,
        "apply_status": "success",
        "editor_validation_status": "passed"
    })
    http.request(get_backend_url() + "/plugin/apply", ["Content-Type: application/json"], HTTPClient.METHOD_POST, body)

func _on_apply_completed(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray, http: HTTPRequest) -> void:
    http.queue_free()
    if response_code != 200:
        system_log("Failed to sync receipts (Code %d)" % response_code, true)
    else:
        system_log("Successfully synced apply receipts to backend.")
        chat_display.text += "\\n[color=green][XClaw] Execution Complete.[/color]"
        
    status_lbl.text = "Idle"
    if plugin: plugin.has_pending_proposals = false
    current_proposal_id = ""
    current_actions = []

func flush_pending_changes() -> void:
    pass
"""

base_dir = r"E:\Projects\GAMEDEV\XClaw Agentic Godot Game Engine\templates\Starter-Kit-3D-Platformer\addons\xclaw_agentic_engine"
with open(os.path.join(base_dir, "xclaw_dock.tscn"), "w") as f:
    f.write(tscn)
with open(os.path.join(base_dir, "xclaw_dock.gd"), "w") as f:
    f.write(gd)
print("Updated UI and Scripts")
