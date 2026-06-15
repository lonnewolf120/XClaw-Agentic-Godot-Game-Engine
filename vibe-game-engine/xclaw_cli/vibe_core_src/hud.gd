extends CanvasLayer
# VibeCore Auto-HUD
# Generates a premium game UI dynamically. No setup required.

var score_label: Label
var health_bar: ProgressBar
var notify_label: Label

func _ready():
	process_mode = Node.PROCESS_MODE_ALWAYS
	layer = 120 # Ensure it stays above everything
	_build_ui()
	
	# Connect to framework signals
	if has_node("/root/VibeEvents"):
		VibeEvents.score_changed.connect(_on_score_updated)
		VibeEvents.health_changed.connect(_on_health_updated)
		VibeEvents.notification_posted.connect(notify)

func _build_ui():
	var margin = MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT, Control.PRESET_MODE_MINSIZE, 20)
	margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(margin)
	
	var vbox = VBoxContainer.new()
	vbox.mouse_filter = Control.MOUSE_FILTER_IGNORE
	margin.add_child(vbox)
	
	# Score Label (Premium Styling)
	score_label = Label.new()
	score_label.text = "SCORE: 0"
	score_label.add_theme_font_size_override("font_size", 32)
	score_label.add_theme_color_override("font_outline_color", Color.BLACK)
	score_label.add_theme_constant_override("outline_size", 8)
	vbox.add_child(score_label)
	
	# Health Bar
	var h_box = HBoxContainer.new()
	vbox.add_child(h_box)
	
	var h_label = Label.new()
	h_label.text = "HEALTH "
	h_box.add_child(h_label)
	
	health_bar = ProgressBar.new()
	health_bar.custom_minimum_size = Vector2(250, 20)
	health_bar.show_percentage = false
	health_bar.value = 100
	h_box.add_child(health_bar)
	
	# Notification Area (Bottom Center)
	notify_label = Label.new()
	notify_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	notify_label.set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM, Control.PRESET_MODE_MINSIZE, 100)
	notify_label.modulate.a = 0
	add_child(notify_label)

func _on_score_updated(value):
	score_label.text = "SCORE: " + str(value)
	var tween = create_tween()
	tween.tween_property(score_label, "scale", Vector2(1.2, 1.2), 0.1)
	tween.tween_property(score_label, "scale", Vector2(1.0, 1.0), 0.1)

func _on_health_updated(_target, current, max_v):
	health_bar.max_value = max_v
	var tween = create_tween()
	tween.tween_property(health_bar, "value", current, 0.3).set_trans(Tween.TRANS_SINE)

func notify(message: String, _type: String = "info"):
	notify_label.text = message
	var tween = create_tween()
	tween.tween_property(notify_label, "modulate:a", 1.0, 0.2)
	tween.tween_interval(2.0)
	tween.tween_property(notify_label, "modulate:a", 0.0, 0.5)
