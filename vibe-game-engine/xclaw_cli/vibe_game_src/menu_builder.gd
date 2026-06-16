extends RefCounted
# MenuBuilder — main menu + game-over screens as code-only CanvasLayers.
# Buttons call back into the GameManager autoload.

func _gm() -> Node:
	return Engine.get_main_loop().root.get_node_or_null("GameManager")


func build_main_menu(parent: Node) -> CanvasLayer:
	var layer := CanvasLayer.new()
	layer.name = "MenuLayer"
	layer.layer = 100

	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	layer.add_child(center)

	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 16)
	center.add_child(vbox)

	var title := Label.new()
	title.text = "VIBE GREYBOX"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override("font_size", 48)
	vbox.add_child(title)

	var start := Button.new()
	start.name = "StartButton"
	start.text = "Start"
	start.pressed.connect(func(): _gm().begin_game())
	vbox.add_child(start)

	var quit := Button.new()
	quit.name = "QuitButton"
	quit.text = "Quit"
	quit.pressed.connect(func(): _gm().quit_game())
	vbox.add_child(quit)

	parent.add_child(layer)
	return layer


func build_game_over(parent: Node, won: bool) -> CanvasLayer:
	var layer := CanvasLayer.new()
	layer.name = "GameOverLayer"
	layer.layer = 101

	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	layer.add_child(center)

	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 16)
	center.add_child(vbox)

	var label := Label.new()
	label.text = "YOU WIN" if won else "GAME OVER"
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.add_theme_font_size_override("font_size", 48)
	vbox.add_child(label)

	var retry := Button.new()
	retry.name = "RetryButton"
	retry.text = "Retry"
	retry.pressed.connect(func(): _gm().restart())
	vbox.add_child(retry)

	var quit := Button.new()
	quit.name = "QuitButton"
	quit.text = "Quit"
	quit.pressed.connect(func(): _gm().quit_game())
	vbox.add_child(quit)

	parent.add_child(layer)
	return layer
