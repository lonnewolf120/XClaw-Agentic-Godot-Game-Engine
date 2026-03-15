@tool
extends Control

@onready var chat_display: RichTextLabel = $VBoxContainer/ChatDisplay
@onready var prompt_input: LineEdit = $VBoxContainer/HBoxContainer/PromptInput
@onready var submit_btn: Button = $VBoxContainer/HBoxContainer/SubmitBtn
@onready var status_lbl: Label = $VBoxContainer/HeaderBar/Status

func _ready() -> void:
    submit_btn.pressed.connect(_on_submit)
    prompt_input.text_submitted.connect(_on_submit_text)

func _on_submit() -> void:
    _on_submit_text(prompt_input.text)

func _on_submit_text(text: String) -> void:
    if text.strip_edges() == "":
        return
        
    chat_display.text += "\n[color=lightblue]You:[/color] " + text
    prompt_input.text = ""
    status_lbl.text = "Thinking..."
    
    # 1. Grab Selected Nodes
    var selected_nodes = EditorInterface.get_selection().get_selected_nodes()
    
    # 2. Transmit to Python Backend (To be implemented using HTTPRequest/WebSocket)
    # _send_to_orchestrator(text, selected_nodes)
    
    # Mocking for now:
    chat_display.text += "\n[color=yellow]Agent:[/color] Generating Action Plan (mock)..."
    status_lbl.text = "Idle"
