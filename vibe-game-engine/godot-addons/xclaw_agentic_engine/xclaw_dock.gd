@tool
extends Control

@onready var chat_display: RichTextLabel = $VBoxContainer/ChatDisplay
@onready var prompt_input: LineEdit = $VBoxContainer/HBoxContainer/PromptInput
@onready var submit_btn: Button = $VBoxContainer/HBoxContainer/SubmitBtn
@onready var status_lbl: Label = $VBoxContainer/HeaderBar/Status

var plugin: EditorPlugin
var current_proposal_id: String = ""
var current_actions: Array = []
var mutation_executor = null

# To let us add Accept / Reject buttons dynamically later, for now we will cheat
# and use commands like "/accept" and "/reject" in the prompt for phase 1.      

func set_plugin(p_plugin: EditorPlugin) -> void:
    plugin = p_plugin
    var ExecClass = preload("res://addons/xclaw_agentic_engine/mutation_executor.gd")
    mutation_executor = ExecClass.new(plugin)
    submit_btn.pressed.connect(_on_submit)
    prompt_input.text_submitted.connect(_on_submit_text)

func _on_submit() -> void:
    _on_submit_text(prompt_input.text)

func _on_submit_text(text: String) -> void:
    var t = text.strip_edges()
    if t == "":
        return
        
    chat_display.text += "\n[color=lightblue]You:[/color] " + t
    prompt_input.text = ""
    
    if t == "/accept" or t == "accept":
        if current_proposal_id != "":
            _send_apply_request()
        else:
            chat_display.text += "\n[color=red]Error:[/color] No pending proposal to accept."
        return
    elif t == "/reject" or t == "reject":
        if current_proposal_id != "":
            reject_proposal()
        else:
            chat_display.text += "\n[color=red]Error:[/color] No pending proposal to reject."
        return

    status_lbl.text = "Thinking..."

    # Layer A - 1. Selection and context capture
    var selected_nodes = EditorInterface.get_selection().get_selected_nodes()
    var context_dump = []

    for node in selected_nodes:
        context_dump.append({
            "name": node.name,
            "class": node.get_class(),
            "path": str(node.get_path())
        })

    var context_str = ""
    if selected_nodes.size() > 0:
        context_str = " (Context: " + str(selected_nodes.size()) + " nodes selected)"
        print("[XClaw Context Capture] ", context_dump)
    else:
        context_str = " (Context: Global)"

    # Simulate pending proposal to block builds early
    if plugin:
        plugin.has_pending_proposals = true
        chat_display.text += "\n[color=yellow]Agent:[/color] Requesting proposal from orchestrator" + context_str + "..."
    
    _send_proposal_request(t, context_dump)

# ------------------------------------------------------------------------------
# HTTP Bridge Methods
# ------------------------------------------------------------------------------

func _send_proposal_request(prompt: String, context_dump: Array) -> void:
    var http = HTTPRequest.new()
    add_child(http)
    http.request_completed.connect(_on_proposal_completed.bind(http))
    
    var url = "http://127.0.0.1:8000/plugin/proposal"
    var headers = ["Content-Type: application/json"]
    
    # Get current scene if available
    var current_scene = EditorInterface.get_edited_scene_root()
    var scene_path = current_scene.scene_file_path if current_scene else ""
        
    var body = JSON.stringify({
        "prompt": prompt,
        "selection": context_dump,
        "current_scene_path": scene_path,
        "mode": "scene_mutation"
    })
    
    http.request(url, headers, HTTPClient.METHOD_POST, body)

func _on_proposal_completed(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray, http: HTTPRequest) -> void:
    http.queue_free()
    if response_code != 200:
        chat_display.text += "\n[color=red]Error:[/color] Failed to reach Python orchestrator (Code " + str(response_code) + ")."
        status_lbl.text = "API Error"
        if plugin:
            plugin.has_pending_proposals = false
        return
        
    var json = JSON.parse_string(body.get_string_from_utf8())
    if typeof(json) != TYPE_DICTIONARY:
        chat_display.text += "\n[color=red]Error:[/color] Invalid JSON from orchestrator."
        status_lbl.text = "Parse Error"
        if plugin:
            plugin.has_pending_proposals = false
        return
        
    preview_proposal(json)

func preview_proposal(proposal: Dictionary) -> void:
    var p_id = proposal.get("proposal_id", "")
    var actions = proposal.get("actions", [])
    current_proposal_id = p_id
    current_actions = actions
    print("[XClaw] Proposal Diff:")
    for d in proposal.get("diff_preview", []):
        print("  - ", d)
    
    status_lbl.text = "Review Proposal"
    
    if plugin:
        plugin.has_pending_proposals = true

func reject_proposal() -> void:
    current_proposal_id = ""
    if plugin:
        plugin.has_pending_proposals = false
    status_lbl.text = "Idle"
    chat_display.text += "\n[color=gray]System:[/color] Proposal rejected. Build lock released."

func _send_apply_request() -> void:
    status_lbl.text = "Applying..."
    var http = HTTPRequest.new()
    add_child(http)
    http.request_completed.connect(_on_apply_completed.bind(http))
    
    var url = "http://127.0.0.1:8000/plugin/apply"
    var headers = ["Content-Type: application/json"]
    var body = JSON.stringify({
        "proposal_id": current_proposal_id,
        "approved_actions": []
    })
    
    http.request(url, headers, HTTPClient.METHOD_POST, body)

func _on_apply_completed(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray, http: HTTPRequest) -> void:
    http.queue_free()
    
    if response_code != 200:
        chat_display.text += "\n[color=red]Error:[/color] Failed to apply via python."
        status_lbl.text = "Apply Error"
        return
        
    var data = JSON.parse_string(body.get_string_from_utf8())
    execute_ai_transaction(data)

func execute_ai_transaction(data: Dictionary) -> void:
    if plugin:
        var action_name = "AI: Apply Proposal " + current_proposal_id.substr(0, 8)
        
        # We process current_actions through mutation_executor
        var validation = mutation_executor.validate_and_build_batch(current_actions)
        
        if validation.status == "error":
            chat_display.text += "\n[color=red]System:[/color] Apply Failed: " + validation.error
            status_lbl.text = "Error"
            return
            
        plugin.execute_ai_action_batch(action_name, validation.batch)
        plugin.has_pending_proposals = false
        
        print("[XClaw Node mutation Receipt]: nodes_touched=", validation.nodes_touched, " files_touched=", validation.files_touched, " actions=", validation.actions_executed)

    current_proposal_id = ""
    current_actions = []
# Called by plugin _apply_changes()
func flush_pending_changes() -> void:
    print("[XClaw] State flushed safely before operation.")
