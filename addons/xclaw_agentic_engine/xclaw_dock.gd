@tool
extends Control

@onready var chat_display: RichTextLabel = $VBoxContainer/TabContainer/Agent/ChatDisplay
@onready var prompt_input: LineEdit = $VBoxContainer/TabContainer/Agent/HBoxContainer/PromptInput
@onready var submit_btn: Button = $VBoxContainer/TabContainer/Agent/HBoxContainer/SubmitBtn
@onready var status_lbl: Label = $VBoxContainer/HeaderBar/Status
@onready var auto_apply_check: CheckButton = $VBoxContainer/HeaderBar/AutoApplyCheck
@onready var connection_indicator: ColorRect = $VBoxContainer/HeaderBar/ConnectionIndicator
@onready var log_terminal: RichTextLabel = $VBoxContainer/TabContainer/Logs/LogTerminal
@onready var backend_url_input: LineEdit = $VBoxContainer/TabContainer/Config/BackendUrlHBox/BackendUrlInput
@onready var llm_provider_option: OptionButton = $VBoxContainer/TabContainer/Config/LlmProviderHBox/LlmProviderOption
@onready var llm_model_input: LineEdit = $VBoxContainer/TabContainer/Config/LlmModelHBox/LlmModelInput
@onready var api_key_input: LineEdit = $VBoxContainer/TabContainer/Config/ApiKeyHBox/ApiKeyInput
@onready var gemini_cli_cmd_input: LineEdit = $VBoxContainer/TabContainer/Config/GeminiCliCmdHBox/GeminiCliCmdInput
@onready var copilot_cmd_input: LineEdit = $VBoxContainer/TabContainer/Config/CopilotCmdHBox/CopilotCmdInput
@onready var codex_cmd_input: LineEdit = $VBoxContainer/TabContainer/Config/CodexCmdHBox/CodexCmdInput

var plugin: EditorPlugin
var mutation_executor: RefCounted
var current_proposal_id: String = ""
var current_actions: Array = []
var poll_timer: Timer
var health_timer: Timer
var is_connected_to_backend = false
var _is_initialized := false

const LLM_PROVIDER_GEMINI := "gemini"
const LLM_PROVIDER_GEMINI_CLI := "gemini_cli"
const LLM_PROVIDER_COPILOT := "copilot_cli"
const LLM_PROVIDER_CODEX := "codex_cli"

func _ready() -> void:
    if _is_initialized:
        return
    _is_initialized = true

    mutation_executor = preload("res://addons/xclaw_agentic_engine/mutation_executor.gd").new(plugin)

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

    _initialize_provider_options()
    setup_connections()

func get_backend_url() -> String:
    if backend_url_input:
        return backend_url_input.text.strip_edges()
    return "http://127.0.0.1:8000"

func _initialize_provider_options() -> void:
    if not llm_provider_option:
        return
    llm_provider_option.clear()
    llm_provider_option.add_item("Gemini")
    llm_provider_option.set_item_metadata(0, LLM_PROVIDER_GEMINI)
    llm_provider_option.add_item("Gemini CLI")
    llm_provider_option.set_item_metadata(1, LLM_PROVIDER_GEMINI_CLI)
    llm_provider_option.add_item("GitHub Copilot CLI")
    llm_provider_option.set_item_metadata(2, LLM_PROVIDER_COPILOT)
    llm_provider_option.add_item("Codex CLI")
    llm_provider_option.set_item_metadata(3, LLM_PROVIDER_CODEX)
    llm_provider_option.select(0)

func _get_selected_provider_id() -> String:
    if not llm_provider_option:
        return LLM_PROVIDER_GEMINI
    var idx = llm_provider_option.selected
    if idx < 0:
        return LLM_PROVIDER_GEMINI
    var meta = llm_provider_option.get_item_metadata(idx)
    if typeof(meta) == TYPE_STRING:
        return String(meta)
    return LLM_PROVIDER_GEMINI

func _build_provider_options() -> Dictionary:
    var options := {
        "llm_provider": _get_selected_provider_id(),
        "llm_model": llm_model_input.text.strip_edges() if llm_model_input else "",
        "api_key": api_key_input.text.strip_edges() if api_key_input else "",
        "gemini_cli_cmd": gemini_cli_cmd_input.text.strip_edges() if gemini_cli_cmd_input else "",
        "copilot_cli_cmd": copilot_cmd_input.text.strip_edges() if copilot_cmd_input else "",
        "codex_cli_cmd": codex_cmd_input.text.strip_edges() if codex_cmd_input else ""
    }
    return options

func system_log(msg: String, error: bool = false) -> void:
    var time_dict = Time.get_time_dict_from_system()
    var time_str = "[%02d:%02d:%02d]" % [time_dict.hour, time_dict.minute, time_dict.second]
    var line = "\n" + time_str + " " + msg
    if error:
        line = "\n[color=red]" + time_str + " ERROR: " + msg + "[/color]"
        
    print("[XClaw] ", msg)
    if log_terminal:
        log_terminal.text += line

func set_plugin(p_plugin: EditorPlugin) -> void:
    plugin = p_plugin
    mutation_executor = preload("res://addons/xclaw_agentic_engine/mutation_executor.gd").new(plugin)
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
    
    chat_display.text += "\n[color=lightblue]You:[/color] " + t
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

    var selected_nodes: Array = []
    if plugin and plugin.get_editor_interface():
        selected_nodes = plugin.get_editor_interface().get_selection().get_selected_nodes()

    var context_dump = []
    for node in selected_nodes:
        context_dump.append({"name": node.name, "class": node.get_class(), "path": str(node.get_path())})
    
    if plugin: plugin.has_pending_proposals = true
    chat_display.text += "\n[color=yellow]Agent:[/color] Requesting proposal from orchestrator..."
    _send_proposal_request(t, context_dump)

func _create_http_request(callback: Callable) -> HTTPRequest:
    var http = HTTPRequest.new()
    add_child(http)
    http.request_completed.connect(callback.bind(http))
    return http

func _on_health_ping() -> void:
    var http = _create_http_request(Callable(self, "_on_health_completed"))
    var err = http.request(get_backend_url() + "/health", ["Content-Type: application/json"], HTTPClient.METHOD_GET)
    if err != OK:
        _on_health_failure(http, "Health request could not be sent")

func _on_health_failure(http: HTTPRequest, message: String) -> void:
    if http:
        http.queue_free()
    if is_connected_to_backend:
        system_log("Lost connection to AI Backend.", true)
    is_connected_to_backend = false
    if connection_indicator:
        connection_indicator.color = Color(1, 0, 0, 1)
    system_log(message, true)

func _on_health_completed(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray, http: HTTPRequest) -> void:
    if result == HTTPRequest.RESULT_SUCCESS and response_code == 200:
        if not is_connected_to_backend:
            system_log("Connected to AI Backend.")
        is_connected_to_backend = true
        if connection_indicator: connection_indicator.color = Color(0, 1, 0, 1) # Green
    else:
        _on_health_failure(http, "Health ping failed (result=%d, code=%d)" % [result, response_code])
        return
    http.queue_free()

func _on_poll_timer() -> void:
    if not auto_apply_check or not auto_apply_check.button_pressed: return
    if current_proposal_id != "": return
    if not is_connected_to_backend: return
    
    var http = _create_http_request(Callable(self, "_on_poll_completed"))
    var err = http.request(get_backend_url() + "/plugin/poll", ["Content-Type: application/json"], HTTPClient.METHOD_GET)
    if err != OK:
        system_log("Failed to send poll request", true)
        http.queue_free()

func _on_poll_completed(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray, http: HTTPRequest) -> void:
    http.queue_free()
    if response_code != 200: return
    
    var json_str = body.get_string_from_utf8()
    var json = JSON.parse_string(json_str)
    if typeof(json) != TYPE_DICTIONARY: return
    if json.has("status") and json.get("status") == "empty": return
    
    system_log("Polled new proposal from dashboard.")
    chat_display.text += "\n[color=yellow]Agent:[/color] Received remote actions. Auto-applying..."
    preview_proposal(json)
    if current_proposal_id != "":
        _send_apply_request()

func _send_proposal_request(prompt: String, context_dump: Array) -> void:
    var http = _create_http_request(Callable(self, "_on_proposal_completed"))
    var options = _build_provider_options()
    
    var body = JSON.stringify({
        "prompt": prompt,
        "selection": context_dump,
        "mode": "scene_mutation",
        "llm_provider": options.get("llm_provider", LLM_PROVIDER_GEMINI),
        "llm_model": options.get("llm_model", ""),
        "options": options
    })
    system_log("Sending proposal request (AI Generation)...")
    var err = http.request(get_backend_url() + "/plugin/proposal", ["Content-Type: application/json"], HTTPClient.METHOD_POST, body)
    if err != OK:
        system_log("Failed to send proposal request", true)
        status_lbl.text = "API Error"
        if plugin:
            plugin.has_pending_proposals = false
        http.queue_free()

func _on_proposal_completed(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray, http: HTTPRequest) -> void:
    http.queue_free()
    if result != HTTPRequest.RESULT_SUCCESS or response_code != 200:
        var error_text = body.get_string_from_utf8()
        system_log("Failed to reach orchestrator (Code %d): %s" % [response_code, error_text], true)
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
    chat_display.text += "\n[color=cyan][XClaw][/color] Validating native batch..."
    
    if ClassDB.class_exists("EditorAIActions"):
        var ai = ClassDB.instantiate("EditorAIActions")
        var preview_receipts = ai.call("preview_action_batch", current_actions)
        system_log("Native Preview Receipts: " + str(preview_receipts))
    elif mutation_executor:
        var validation = mutation_executor.validate_and_build_batch(current_actions)
        if validation.get("status") == "error":
            system_log("Validation failed: " + str(validation.get("error")), true)
            status_lbl.text = "Validation Error"
            return
        system_log("Preview validated with fallback executor")
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
    chat_display.text += "\n[color=gray]System:[/color] Proposal rejected."
    
func _send_apply_request() -> void:
    status_lbl.text = "Applying..."
    var receipts = []
    
    if ClassDB.class_exists("EditorAIActions"):
        var ai = ClassDB.instantiate("EditorAIActions")
        receipts = ai.call("apply_action_batch", current_actions)
        system_log("Applied native batch: " + str(receipts))
    elif mutation_executor:
        var validation = mutation_executor.validate_and_build_batch(current_actions)
        if validation.get("status") == "error":
            system_log("Apply validation failed: " + str(validation.get("error")), true)
            status_lbl.text = "Error"
            return
        var batch = validation.get("batch", [])
        plugin.execute_ai_action_batch("XClaw AI Apply", batch)
        receipts.append({
            "engine": "gdscript_fallback",
            "actions_executed": validation.get("actions_executed", 0),
            "nodes_touched": validation.get("nodes_touched", []),
            "files_touched": validation.get("files_touched", [])
        })
        system_log("Applied fallback batch: " + str(receipts))
    else:
        system_log("EditorAIActions module missing!", true)
        status_lbl.text = "Error"
        return

    var http = _create_http_request(Callable(self, "_on_apply_completed"))
    
    var body = JSON.stringify({
        "proposal_id": current_proposal_id,
        "native_receipts": receipts,
        "apply_status": "success",
        "editor_validation_status": "passed"
    })
    var err = http.request(get_backend_url() + "/plugin/apply", ["Content-Type: application/json"], HTTPClient.METHOD_POST, body)
    if err != OK:
        system_log("Failed to send apply sync request", true)
        status_lbl.text = "Apply Sync Error"
        if plugin:
            plugin.has_pending_proposals = false
        current_proposal_id = ""
        current_actions = []
        http.queue_free()

func _on_apply_completed(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray, http: HTTPRequest) -> void:
    http.queue_free()
    if result != HTTPRequest.RESULT_SUCCESS or response_code != 200:
        system_log("Failed to sync receipts (Code %d): %s" % [response_code, body.get_string_from_utf8()], true)
    else:
        system_log("Successfully synced apply receipts to backend.")
        chat_display.text += "\n[color=green][XClaw] Execution Complete.[/color]"
        
    status_lbl.text = "Idle"
    if plugin: plugin.has_pending_proposals = false
    current_proposal_id = ""
    current_actions = []

func flush_pending_changes() -> void:
    pass
