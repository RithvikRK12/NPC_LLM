extends PanelContainer
signal start_requested
var state: Dictionary = {}
var title: Label
var objective: Label
var start_button: Button
var progress: ProgressBar
var remaining := 0.0
var content_scroll: ScrollContainer

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_TOP_LEFT)
	offset_left = 24
	offset_top = 100
	offset_right = 600
	add_theme_stylebox_override("panel", preload("res://scripts/medieval_theme.gd").frame())
	content_scroll=ScrollContainer.new()
	content_scroll.follow_focus=true
	content_scroll.horizontal_scroll_mode=ScrollContainer.SCROLL_MODE_DISABLED
	content_scroll.custom_minimum_size=Vector2(550,360)
	add_child(content_scroll)
	var layout := VBoxContainer.new()
	layout.size_flags_horizontal=Control.SIZE_EXPAND_FILL
	layout.add_theme_constant_override("separation", 10)
	content_scroll.add_child(layout)
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
	if content_scroll:
		var available: float=get_parent().size.y-140
		content_scroll.custom_minimum_size.y=minf(500,maxf(240,available))
		content_scroll.custom_minimum_size.x=minf(550,get_parent().size.x-64)
	if state.get("phase") == "crafting":
		remaining = maxf(0, remaining - delta)
		progress.value = minf(99, (1.0 - remaining / float(state.get("craft_seconds", 5))) * 100)

var ship_title: Label
var ship_objective: Label
func set_ship_state(data: Dictionary, encounter: Dictionary) -> void:
	if ship_title==null:
		var container: VBoxContainer=title.get_parent()
		ship_title=Label.new(); ship_title.text="A WAY HOME • MAIN STORY"; container.add_child(ship_title)
		ship_title.add_theme_font_size_override("font_size",24)
		ship_objective=Label.new(); ship_objective.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
		ship_objective.custom_minimum_size.x=400; container.add_child(ship_objective)
	var phase: String=data.get("phase","not_started")
	ship_title.visible=phase!="not_started" or encounter.get("outing_active",false)
	ship_objective.visible=ship_title.visible
	var lines: Array[String]=[]
	if phase!="not_started":
		lines.append(data.get("objective","Gather ship-repair materials."))
		for material in data.get("materials",[]):
			lines.append("%s: %s / %s" % [material.name,int(material.contributed),int(material.required)])
		lines.append(data.get("availability_note",""))
	elif encounter.get("outing_active",false): lines.append("Lead the Craftsman to your ship.")
	var mode: String=encounter.get("mode","")
	if mode=="waiting_for_player": lines.append("Craftsman: waiting for you. Return and ask him to resume.")
	elif mode=="returning_to_workshop": lines.append("Craftsman: walking back to his workshop.")
	elif encounter.get("navigation_space","")=="workshop": lines.append("Craftsman: at the workshop.")
	ship_objective.text="\n".join(lines)
