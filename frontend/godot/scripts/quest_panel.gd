extends PanelContainer
signal start_requested
var state: Dictionary = {}
var title: Label
var objective: Label
var start_button: Button
var progress: ProgressBar
var remaining := 0.0

func _ready() -> void:
	position = Vector2(24, 152)
	custom_minimum_size = Vector2(600, 172)
	var style := StyleBoxFlat.new()
	style.bg_color = _ca("090d19", 0.94)
	style.border_color = Color("19f6ff")
	style.set_border_width_all(1)
	style.set_corner_radius_all(10)
	style.content_margin_left = 16
	style.content_margin_right = 16
	style.content_margin_top = 14
	style.content_margin_bottom = 14
	add_theme_stylebox_override("panel", style)
	var layout := VBoxContainer.new()
	layout.add_theme_constant_override("separation", 10)
	add_child(layout)
	title = Label.new()
	title.text = "ASSEMBLE PULSE BLASTER"
	title.add_theme_font_size_override("font_size", 24)
	title.add_theme_color_override("font_color", Color("ff3df2"))
	layout.add_child(title)
	objective = Label.new()
	objective.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	objective.custom_minimum_size.x = 564
	layout.add_child(objective)
	progress = ProgressBar.new()
	progress.custom_minimum_size.y = 26
	var fill := StyleBoxFlat.new()
	fill.bg_color = Color("19f6ff")
	fill.set_corner_radius_all(5)
	progress.add_theme_stylebox_override("fill", fill)
	layout.add_child(progress)
	start_button = Button.new()
	start_button.text = "Begin • Assemble Pulse Blaster"
	start_button.custom_minimum_size.y = 38
	start_button.pressed.connect(func(): start_requested.emit())
	layout.add_child(start_button)
	hide()

func update_quest(data: Dictionary) -> void:
	state = data
	objective.text = data.get("objective", "Explore JIT Cyber Grid or begin a mission.")
	var phase: String = data.get("phase", "available")
	start_button.visible = phase == "available"
	start_button.disabled = false
	progress.visible = phase == "crafting"
	remaining = float(data.get("remaining_seconds", 0))
	title.text = "PULSE BLASTER • COMPLETE" if phase == "completed" else "ASSEMBLE PULSE BLASTER"
	if phase == "crafting": show()

func _process(delta: float) -> void:
	if state.get("phase") == "crafting":
		remaining = maxf(0, remaining - delta)
		progress.value = minf(99, (1.0 - remaining / float(state.get("craft_seconds", 5))) * 100)


func _ca(hex: String, alpha: float) -> Color:
	var color := Color(hex)
	color.a = alpha
	return color
