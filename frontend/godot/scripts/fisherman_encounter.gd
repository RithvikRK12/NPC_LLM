extends Node2D
# 32 world units per meter, matching the island's authored grid.
const INTRO_RADIUS := 320.0
const TALK_RADIUS := 100.0
const INTRO_DURATION := 1.8
const GRAPH_PATH := "res://resources/fisherman_dialogue.json"
var graph: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(GRAPH_PATH))
var current_id := "F00"
var state_path := "user://fisherman-presentation.cfg"
var game_scope := ""
var intro_seen := false
var introducing := false
var approaching := false
var approach_path: Array[Vector2] = []
var intro_elapsed := 0.0
var looking_up := false
var panel: PanelContainer
var line: Label
var choices: VBoxContainer
var close_button: Button

func _ready() -> void:
	position = Vector2(250,2252)
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST

func build_ui(parent: Control) -> void:
	panel = PanelContainer.new()
	parent.add_child(panel)
	panel.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	panel.offset_left = 24
	panel.offset_right = -24
	panel.offset_top = -330
	panel.offset_bottom = -16
	var scroll := ScrollContainer.new()
	scroll.follow_focus = true
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	panel.add_child(scroll)
	var content := VBoxContainer.new()
	content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(content)
	var header := HBoxContainer.new()
	content.add_child(header)
	var title := Label.new()
	title.text = "Rowan • Old fisherman"
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(title)
	close_button = Button.new()
	close_button.text = "Close / Back"
	close_button.pressed.connect(close_dialogue)
	header.add_child(close_button)
	line = Label.new()
	line.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	line.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	content.add_child(line)
	choices = VBoxContainer.new()
	content.add_child(choices)
	panel.hide()

func set_scope(scope: String) -> void:
	if scope != game_scope: close_dialogue()
	game_scope = scope
	var state := ConfigFile.new()
	intro_seen = state.load(state_path) == OK and bool(state.get_value("introductions",scope,false))

func try_introduction(at: Vector2) -> bool:
	if intro_seen or introducing or game_scope.is_empty() or at.distance_to(position) > INTRO_RADIUS: return false
	intro_seen = true
	introducing = true
	intro_elapsed = 0.0
	looking_up = false
	var state := ConfigFile.new()
	state.load(state_path)
	state.set_value("introductions",game_scope,true)
	if state.save(state_path) != OK: push_warning("Rowan's introduction flag could not be saved")
	queue_redraw()
	return true

func begin_approach(actor: CharacterBody2D, layout: Resource) -> void:
	var goal := Vector2(250,2310)
	approach_path.clear()
	if clear_segment(actor.position,goal,layout):
		approach_path.append(goal)
	else:
		# A small local grid routes arrivals from either side around the solid
		# trunk and nearby scenery. Walkability already includes the foot box.
		var grid := AStarGrid2D.new()
		var center := Vector2i(position / 16)
		grid.region = Rect2i(center-Vector2i(25,25),Vector2i(51,51))
		grid.cell_size = Vector2(16,16)
		grid.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_NEVER
		grid.update()
		for y in range(grid.region.position.y,grid.region.end.y):
			for x in range(grid.region.position.x,grid.region.end.x):
				grid.set_point_solid(Vector2i(x,y),not route_point_clear(Vector2(x,y)*16,layout))
		var start := nearest_grid_point(actor.position,grid,layout)
		var end := nearest_grid_point(goal,grid,layout)
		if start != Vector2i.MAX and end != Vector2i.MAX:
			for id in grid.get_id_path(start,end): approach_path.append(Vector2(id)*16)
			if not approach_path.is_empty(): approach_path.append(goal)
	approaching = not approach_path.is_empty()
	if not approaching: close_dialogue()

func nearest_grid_point(at: Vector2, grid: AStarGrid2D, layout: Resource) -> Vector2i:
	var center := Vector2i((at / 16).round())
	var best := Vector2i.MAX
	var distance := INF
	for y in range(-2,3):
		for x in range(-2,3):
			var id := center+Vector2i(x,y)
			var point := Vector2(id)*16
			if not grid.region.has_point(id) or grid.is_point_solid(id): continue
			if point.distance_squared_to(at) < distance and clear_segment(at,point,layout):
				best = id
				distance = point.distance_squared_to(at)
	return best

func clear_segment(from: Vector2, to: Vector2, layout: Resource) -> bool:
	var steps := maxi(1,ceili(from.distance_to(to)/4.0))
	for i in range(steps+1):
		if not route_point_clear(from.lerp(to,float(i)/steps),layout): return false
	return true

func route_point_clear(at: Vector2, layout: Resource) -> bool:
	# Keep a small margin beyond the foot box so a route never grazes a
	# trunk edge that is mathematically open but touching in physics.
	for offset in [Vector2.ZERO,Vector2(-2,-2),Vector2(2,-2),Vector2(-2,2),Vector2(2,2)]:
		if not layout.is_walkable(at+offset): return false
	return true

func advance_approach(actor: CharacterBody2D, delta: float) -> void:
	if not approaching: return
	var motion := approach_path[0]-actor.position
	actor.velocity = motion.normalized()*actor.speed
	var collision := actor.move_and_collide(motion.limit_length(actor.speed*delta))
	if collision:
		# Cancel rather than teleport through an unexpected obstruction.
		actor.velocity = Vector2.ZERO
		close_dialogue()
		return
	if actor.position.distance_to(approach_path[0]) < 0.1:
		approach_path.pop_front()
		if approach_path.is_empty():
			actor.velocity = Vector2.ZERO
			actor.get_child(0).set_facing(&"up")
			approaching = false
			intro_elapsed = 0.0

func advance_intro(delta: float) -> void:
	if not introducing or approaching: return
	intro_elapsed += delta
	looking_up = intro_elapsed >= 0.6
	queue_redraw()
	if intro_elapsed >= INTRO_DURATION:
		introducing = false
		open_dialogue()

func owns_input() -> bool:
	return introducing or (is_instance_valid(panel) and panel.visible)

func open_dialogue() -> void:
	introducing = false
	looking_up = true
	panel.show()
	present("F00")
	queue_redraw()

func close_dialogue() -> void:
	approaching = false
	approach_path.clear()
	introducing = false
	looking_up = false
	current_id = "F00"
	if is_instance_valid(panel): panel.hide()
	queue_redraw()

func present(id: String) -> void:
	current_id = id
	line.text = graph[id].text
	for child in choices.get_children():
		choices.remove_child(child)
		child.queue_free()
	var options: Array = graph[id].get("choices",[])
	if options.is_empty():
		var button := Button.new()
		button.text = "Continue"
		button.pressed.connect(continue_dialogue)
		choices.add_child(button)
	else:
		for i in range(options.size()):
			var button := Button.new()
			button.text = options[i].text
			button.pressed.connect(choose.bind(i))
			choices.add_child(button)
	choices.get_child(0).grab_focus()

func choose(index: int) -> void:
	var options: Array = graph[current_id].get("choices",[])
	if index >= 0 and index < options.size(): present(options[index].to)

func continue_dialogue() -> void:
	if graph[current_id].get("end",false): close_dialogue()

func _draw() -> void:
	draw_set_transform(Vector2(0,-2)) # Sort just in front of the grounded trunk.
	# Authored on the same 2-unit pixel grid as the village actors. Hips sit
	# on the log at y=-20; knees and boots overlap its front, never its trunk.
	draw_rect(Rect2(-16,-26,32,12),Color("302e28"))
	draw_rect(Rect2(-14,-24,12,20),Color("58605a"))
	draw_rect(Rect2(4,-24,12,20),Color("58605a"))
	draw_rect(Rect2(-14,-6,10,14),Color("41463f"))
	draw_rect(Rect2(6,-6,10,14),Color("41463f"))
	draw_rect(Rect2(-18,6,14,6),Color("493d30"))
	draw_rect(Rect2(4,6,16,6),Color("493d30"))
	draw_rect(Rect2(-14,-44,28,24),Color("394b4b"))
	draw_rect(Rect2(-10,-44,8,22),Color("6b7b70"))
	draw_rect(Rect2(-20,-40,8,18),Color("52645d"))
	draw_rect(Rect2(12,-40,8,18),Color("52645d"))
	var head_y := -62.0 if looking_up else -56.0
	draw_rect(Rect2(-10,head_y,20,20),Color("b9956d"))
	draw_rect(Rect2(-12,head_y,4,14),Color("d2cbb0"))
	draw_rect(Rect2(8,head_y,4,14),Color("d2cbb0"))
	draw_rect(Rect2(-8,head_y+14,16,8),Color("d2cbb0"))
	draw_rect(Rect2(-4,head_y+20,8,4),Color("b0b39e"))
	draw_rect(Rect2(-12,head_y-6,24,8),Color("797457"))
	draw_rect(Rect2(-16,head_y,32,4),Color("a19770"))
	if looking_up:
		draw_rect(Rect2(-6,head_y+8,2,2),Color("302e28"))
		draw_rect(Rect2(4,head_y+8,2,2),Color("302e28"))
	# A sagging mesh across the knees, with exposed hands holding the edges.
	draw_rect(Rect2(-20,-26,40,12),Color("4c5650"))
	for x in range(-18,20,6): draw_line(Vector2(x,-26),Vector2(x+4,-14),Color("a6a68a"),2)
	for y in range(-24,-12,4): draw_line(Vector2(-18,y),Vector2(18,y),Color("a6a68a"),2)
	draw_rect(Rect2(-22,-28,8,6),Color("b9956d"))
	draw_rect(Rect2(14,-28,8,6),Color("b9956d"))
