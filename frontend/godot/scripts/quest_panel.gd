extends PanelContainer
signal start_requested
var state: Dictionary = {}
var title: Label
var objective: Label
var start_button: Button
var progress: ProgressBar
var remaining := 0.0

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_TOP_LEFT)
	offset_left = 24
	offset_top = 100
	offset_right = 600
	add_theme_stylebox_override("panel", preload("res://scripts/medieval_theme.gd").frame())
	var layout := VBoxContainer.new()
	layout.add_theme_constant_override("separation", 10)
	add_child(layout)
	title = Label.new()
	title.text = "GET A BOW"
	title.add_theme_font_size_override("font_size", 28)
	title.add_theme_color_override("font_color", Color("302419"))
	layout.add_child(title)
	var close := Button.new()
	close.text = "Close"
	close.pressed.connect(hide)
	layout.add_child(close)
	objective = Label.new()
	objective.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	objective.custom_minimum_size.x = 400
	layout.add_child(objective)
	progress = ProgressBar.new()
	progress.custom_minimum_size.y = 26
	layout.add_child(progress)
	start_button = Button.new()
	start_button.text = "Begin • Get a bow"
	start_button.custom_minimum_size.y = 38
	start_button.pressed.connect(func(): start_requested.emit())
	layout.add_child(start_button)
	hide()

func update_quest(data: Dictionary) -> void:
	state = data
	objective.text = data.get("objective", "Explore the village or begin a quest.")
	var phase: String = data.get("phase", "available")
	start_button.visible = phase == "available"
	start_button.disabled = false
	progress.visible = phase == "crafting"
	remaining = float(data.get("remaining_seconds", 0))
	title.text = "GET A BOW • COMPLETE" if phase == "completed" else "GET A BOW"
	if phase == "crafting": show()

func _process(delta: float) -> void:
	if state.get("phase") == "crafting":
		remaining = maxf(0, remaining - delta)
		progress.value = minf(99, (1.0 - remaining / float(state.get("craft_seconds", 5))) * 100)
