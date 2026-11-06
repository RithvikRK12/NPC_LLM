extends Control
# Presentation belongs to a saved run, independent of quests and NPC memory.
const OBJECTIVE := "Find someone to get help."
const HOLD_TIME := 1.6
const MOVE_TIME := 1.1
const DOCK := Vector2(24,100)
const DOCK_SCALE := 0.65
const CHECK_DRAW_TIME := 0.28
const COMPLETION_HOLD := 1.5
const COMPLETION_FADE := 0.45
const COMPLETION_END := CHECK_DRAW_TIME+COMPLETION_HOLD+COMPLETION_FADE
const Styles = preload("res://scripts/medieval_theme.gd")
var state_path := "user://onboarding-presentation.cfg"
var game_scope := ""
var completed := false
var completing := false
var completion_elapsed := 0.0
var checkmark: Control
var acknowledged := false
var active := false
var animating := false
var elapsed := 0.0
var modal: Control
var card: PanelContainer
var go_button: Button
var objective: PanelContainer
var objective_text: Label

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	modal = Control.new()
	add_child(modal)
	modal.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var dim := ColorRect.new()
	dim.color = Color("132022cf")
	modal.add_child(dim)
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	card = PanelContainer.new()
	modal.add_child(card)
	card.add_theme_stylebox_override("panel",Styles.frame(Color("ead7ab"),Color("70482c"),4,24))
	var content := VBoxContainer.new()
	content.add_theme_constant_override("separation",12)
	card.add_child(content)
	var title := Label.new()
	title.text = "YOU'RE ASHORE"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override("font_size",36)
	content.add_child(title)
	var subtitle := Label.new()
	subtitle.text = "Take a moment to learn the controls."
	subtitle.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	content.add_child(subtitle)
	var grid := GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation",28)
	grid.add_theme_constant_override("v_separation",8)
	content.add_child(grid)
	for row in [["W A S D","Move"],["Shift + direction","Sprint (1.5× speed)"],["E","Talk, inspect, or enter"],["F","Pick up nearby items"],["I","Open your bag"],["Esc","Menu / close panels"]]:
		var key := Label.new()
		key.text = row[0]
		key.custom_minimum_size = Vector2(150,34)
		key.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		key.add_theme_stylebox_override("normal",Styles.frame(Color("c4a675"),Color("927045"),2,4))
		grid.add_child(key)
		var action := Label.new()
		action.text = row[1]
		action.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		grid.add_child(action)
	go_button = Button.new()
	go_button.text = "Let's go"
	go_button.custom_minimum_size.y = 54
	go_button.pressed.connect(dismiss)
	content.add_child(go_button)
	for direction in ["focus_next","focus_previous","focus_neighbor_top","focus_neighbor_bottom","focus_neighbor_left","focus_neighbor_right"]:
		go_button.set(direction,go_button.get_path())
	objective = PanelContainer.new()
	add_child(objective)
	objective.mouse_filter = Control.MOUSE_FILTER_IGNORE
	objective.add_theme_stylebox_override("panel",Styles.frame(Color("203e32ed"),Color("b9a46b"),2,14))
	objective_text = Label.new()
	objective_text.text = OBJECTIVE
	objective_text.add_theme_font_size_override("font_size",36)
	objective_text.add_theme_color_override("font_color",Color("fff0ce"))
	objective_text.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var objective_row := HBoxContainer.new()
	objective.add_child(objective_row)
	checkmark = Control.new()
	checkmark.custom_minimum_size = Vector2(54,44)
	checkmark.mouse_filter = Control.MOUSE_FILTER_IGNORE
	checkmark.draw.connect(_draw_checkmark)
	objective_row.add_child(checkmark)
	checkmark.hide()
	objective_row.add_child(objective_text)
	resized.connect(_layout)
	reset_presentation()

func set_scope(scope: String) -> void:
	reset_presentation()
	game_scope = scope
	var state := ConfigFile.new()
	state.load(state_path)
	acknowledged = bool(state.get_value("controls",scope,false))
	completed = bool(state.get_value("objectives",scope,false))

func begin() -> void:
	if game_scope.is_empty(): return
	active = true
	if acknowledged:
		objective.visible = not completed
		elapsed = HOLD_TIME+MOVE_TIME
		_layout()
		return
	modal.show()
	objective.hide()
	# A held fast-forward key must not dismiss the card at the handoff.
	go_button.disabled = Input.is_key_pressed(KEY_SPACE) or Input.is_key_pressed(KEY_ENTER)
	go_button.grab_focus()
	_layout()

func _process(_delta: float) -> void:
	if modal.visible and go_button.disabled and not Input.is_key_pressed(KEY_SPACE) and not Input.is_key_pressed(KEY_ENTER):
		go_button.disabled = false
		go_button.grab_focus()

func owns_input() -> bool:
	return modal.visible

func dismiss() -> void:
	if not modal.visible: return
	modal.hide()
	acknowledged = true
	var state := ConfigFile.new()
	state.load(state_path)
	state.set_value("controls",game_scope,true)
	if state.save(state_path) != OK: push_warning("Controls acknowledgment could not be saved")
	objective.visible = not completed
	elapsed = 0.0
	animating = not completed
	_layout()

# Reuse the arrival objective presentation for nonblocking gameplay guidance.
# The owning game state restores these tasks; they do not acknowledge controls
# or write the initial find-help objective's save flag.
func present_objective(text: String, animate: bool = true) -> void:
	reset_presentation()
	objective_text.text = text
	active = true
	acknowledged = true
	completed = false
	elapsed = 0.0 if animate else HOLD_TIME+MOVE_TIME
	animating = animate
	objective.show()
	_layout()

func advance(delta: float, reduced_motion: bool = false) -> void:
	if completing:
		completion_elapsed = minf(COMPLETION_END,completion_elapsed+delta)
		checkmark.queue_redraw()
		objective.modulate.a = 1.0-clampf((completion_elapsed-CHECK_DRAW_TIME-COMPLETION_HOLD)/COMPLETION_FADE,0,1)
		if completion_elapsed >= COMPLETION_END:
			completing = false
			objective.hide()
		return
	if not animating: return
	elapsed = minf(HOLD_TIME+MOVE_TIME,elapsed+delta)
	if reduced_motion and elapsed >= HOLD_TIME: elapsed = HOLD_TIME+MOVE_TIME
	animating = elapsed < HOLD_TIME+MOVE_TIME
	_layout_objective()

func reset_presentation() -> void:
	active = false
	completing = false
	completion_elapsed = 0.0
	if is_instance_valid(checkmark): checkmark.hide()
	if is_instance_valid(objective): objective.modulate = Color.WHITE
	if is_instance_valid(objective_text): objective_text.add_theme_color_override("font_color",Color("fff0ce"))
	animating = false
	elapsed = 0.0
	if is_instance_valid(modal): modal.hide()
	if is_instance_valid(objective): objective.hide()

func _layout() -> void:
	if not is_instance_valid(card): return
	var width := minf(800,size.x-48)
	card.size = Vector2(width,card.get_combined_minimum_size().y)
	card.position = ((size-card.size)/2).round()
	_layout_objective()

func _layout_objective() -> void:
	if not is_instance_valid(objective): return
	objective.size = objective.get_combined_minimum_size()
	var progress := clampf((elapsed-HOLD_TIME)/MOVE_TIME,0,1)
	var eased := progress*progress*(3.0-2.0*progress)
	objective.scale = Vector2.ONE*lerpf(1.0,DOCK_SCALE,eased)
	var center := Vector2((size.x-objective.size.x)/2,size.y*0.43-objective.size.y/2)
	objective.position = center.lerp(DOCK,eased).round()

func set_obscured(obscured: bool) -> void:
	objective.visible = active and acknowledged and (not completed or completing) and not modal.visible and not obscured

func complete_objective(animate: bool = true) -> void:
	if completed: return
	completed = true
	var state := ConfigFile.new()
	state.load(state_path)
	state.set_value("objectives",game_scope,true)
	if not game_scope.is_empty() and state.save(state_path) != OK: push_warning("Objective completion could not be saved")
	animating = false
	completing = animate and active and acknowledged
	if not completing:
		objective.hide()
		return
	completion_elapsed = 0.0
	elapsed = HOLD_TIME+MOVE_TIME
	checkmark.show()
	objective_text.add_theme_color_override("font_color",Color("c4e8a3"))
	objective.show()
	_layout_objective()
	checkmark.queue_redraw()

func _draw_checkmark() -> void:
	var progress := clampf(completion_elapsed/CHECK_DRAW_TIME,0,1)
	var a := Vector2(6,24)
	var b := Vector2(20,36)
	var c := Vector2(46,8)
	var first := clampf(progress*3,0,1)
	var second := clampf((progress-1.0/3.0)*1.5,0,1)
	checkmark.draw_line(a,a.lerp(b,first),Color("a9da82"),6)
	if second > 0: checkmark.draw_line(b,b.lerp(c,second),Color("a9da82"),6)
