extends Node2D

@export var backend_url := "http://127.0.0.1:8000"

var world_view: Node
var village: Node2D
var interiors: Array[Node2D] = []
var travelling := false
var travel_fade: ColorRect
var recovery_notice := ""
var player: CharacterBody2D
var npc_nodes: Dictionary = {}
var current_npc: Area2D
var chat_windows: Dictionary = {}
var inventory_label: Label
var interaction_label: Label
var help_label: Label
var world_request: HTTPRequest
var world_loaded := false
var inventory_drawer: PanelContainer
var inventory_compact_theme: Theme
var player_grid: GridContainer
var player_scroll: ScrollContainer
var give_button: Button
var bag_button: Button
var player_items: Array = []
var quest_panel: PanelContainer
var quest_request: HTTPRequest
var quest_busy := false
var bow_state: Dictionary = {}
var string_pickup: Sprite2D
var pickup_hint: Label
var restart_button: Button
var restart_dialog: ConfirmationDialog
var position_request: HTTPRequest
var position_busy := false
var last_saved_position := Vector2.INF
var sent_position := Vector2.ZERO
var quitting := false
var world_busy := false
var ui: Control
var menu_layer: Control
var menu_panel: PanelContainer
var menu_status: Label
var resume_button: Button
var quit_button: Button
var retry_button: Button
var back_button: Button
var previous_focus: Control
var active_npc_id := 0
var save_error := false
var large_text := false
var restart_in_flight := false
const Styles = preload("res://scripts/medieval_theme.gd")


func _ready() -> void:
	ThemeDB.get_default_theme().default_font = Styles.create().default_font
	get_tree().auto_accept_quit = false
	_build_world()
	_build_ui()
	_load_world()


func _process(_delta: float) -> void:
	player.set_physics_process(world_loaded and not quitting and not travelling and not ui_owns_input())
	restart_button.disabled = not world_loaded or _operations_pending() or quitting
	resume_button.disabled = quitting
	quit_button.disabled = quitting
	if menu_layer.visible:
		var menu_size := menu_panel.get_combined_minimum_size().max(Vector2(440,416))
		menu_panel.offset_left = -menu_size.x / 2
		menu_panel.offset_right = menu_size.x / 2
		menu_panel.offset_top = -menu_size.y / 2
		menu_panel.offset_bottom = menu_size.y / 2
	if quitting:
		menu_status.text = "Finishing current action..." if _operations_pending() and not position_busy else "Saving..."
		if not _operations_pending():
			if not world_loaded: get_tree().quit()
			else: _save_position()
	var room: String = village.layout.interior_at(player.position)
	world_view.follow(player.position if room.is_empty() else village.layout.interior_origin(room) + Vector2(0,-16))
	_update_current_npc()
	interaction_label.text = "E  Talk to " + current_npc.display_name if current_npc != null else "Approach a villager to talk"
	if not room.is_empty():
		interaction_label.text = village.layout.interiors()[room].name + " • Walk down to leave" if current_npc == null else interaction_label.text
	elif not village.layout.doorway_at(player.position).is_empty():
		interaction_label.text = "W / E  Enter " + village.layout.interiors()[village.layout.doorway_at(player.position)].name
	_update_give_action()
	if string_pickup.visible and player.position.distance_to(string_pickup.position) < 64:
		interaction_label.text = "F  Pick up string"
	var conversation_open := false
	var dialogue_top := ui.size.y
	for window in chat_windows.values():
		if window.visible:
			conversation_open = true
			dialogue_top = minf(dialogue_top,window.global_position.y)
	interaction_label.visible = not conversation_open
	help_label.visible = not conversation_open
	if not recovery_notice.is_empty(): interaction_label.text = recovery_notice
	inventory_drawer.offset_left = -minf(310, ui.size.x * 0.285)
	inventory_drawer.offset_right = minf(310, ui.size.x * 0.285)
	var compact_bag := conversation_open and ui.size.y < 640
	var inventory_top := 16 if compact_bag else (24 if ui.size.y < 640 else 90)
	var bag_theme: Theme = inventory_compact_theme if compact_bag else null
	if inventory_drawer.theme != bag_theme: inventory_drawer.theme = bag_theme
	# Let the slot list scroll within the space above the actual dialogue box.
	player_scroll.custom_minimum_size.y = 0 if conversation_open else 152
	inventory_drawer.offset_top = -ui.size.y / 2 + inventory_top if conversation_open else -160
	inventory_drawer.offset_bottom = inventory_drawer.offset_top + minf(320, dialogue_top - inventory_top - 12) if conversation_open else 160
	player_grid.fit_columns(inventory_drawer.size.x - 40)
	for id in chat_windows:
		var window = chat_windows[id]
		window.modal_blocked = menu_layer.visible or quitting or restart_dialog.visible
		var target: Node2D = player if window.active_speaker == "Player" else npc_nodes[id]
		window.speaker_screen = world_view.world_to_screen(target.global_position - Vector2(0,48))
		window.speaker_visible = Rect2(Vector2.ZERO, ui.size).has_point(window.speaker_screen)
	for npc in npc_nodes.values():
		npc.label.position = world_view.world_to_screen(npc.position - Vector2(0,92)) - Vector2(80,0)
		npc.label.visible = Rect2(Vector2.ZERO,ui.size).has_point(npc.label.position+Vector2(80,0)) and not conversation_open


func ui_owns_input() -> bool:
	if travelling: return true
	if menu_layer.visible or restart_dialog.visible or inventory_drawer.visible or quest_panel.visible: return true
	for window in chat_windows.values():
		if window.visible: return true
	return false

func _input(event: InputEvent) -> void:
	if travelling: return
	if event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_F3:
		village.set_debug(not village.debug_geometry)
		for interior in interiors: interior.set_debug(village.debug_geometry)
		for actor in [player,npc_nodes[1],npc_nodes[2]]:
			for child in actor.get_children():
				if child.get_script() == preload("res://scripts/person.gd"):
					child.debug_geometry = village.debug_geometry
					child.queue_redraw()
	if menu_layer.visible and not restart_dialog.visible and event is InputEventKey and event.pressed:
		if event.keycode in [KEY_TAB, KEY_UP, KEY_DOWN]:
			get_viewport().set_input_as_handled()
			if event.echo or quitting: return
			var controls: Array[Control] = [resume_button, restart_button, quit_button, menu_panel.get_child(0).get_child(4), retry_button, back_button, menu_panel.get_child(0).get_child(menu_panel.get_child(0).get_child_count()-1)]
			var available: Array[Control] = []
			for control in controls:
				if control.is_visible_in_tree() and not control.disabled: available.append(control)
			var index := available.find(get_viewport().gui_get_focus_owner())
			var direction := -1 if event.keycode == KEY_UP or (event.keycode == KEY_TAB and event.shift_pressed) else 1
			available[posmod(index + direction, available.size())].grab_focus()
			return
	if event is InputEventKey and event.keycode == KEY_ESCAPE and event.pressed:
		get_viewport().set_input_as_handled()
		if event.echo or quitting: return
		if restart_dialog.visible:
			restart_dialog.hide()
			restart_button.grab_focus()
		elif menu_layer.visible: _resume_game()
		else: _open_menu()

func _unhandled_input(event: InputEvent) -> void:
	if not world_loaded or quitting or travelling or menu_layer.visible or restart_dialog.visible: return
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_I:
			_toggle_bag()
		elif not ui_owns_input():
			if event.keycode == KEY_E:
				var door: String = village.layout.doorway_at(player.position)
				if not door.is_empty(): _enter_building(door)
				else: _open_dialogue()
			elif event.keycode == KEY_F and string_pickup.visible and player.position.distance_to(string_pickup.position) < 64:
				_quest_call("pickup-string", {"x": player.position.x, "y": player.position.y})

func _build_world() -> void:
	world_view = preload("res://scripts/world_view.gd").new()
	add_child(world_view)
	village = preload("res://scripts/village.gd").new()
	world_view.world.add_child(village)
	for id in village.layout.interiors():
		var interior := preload("res://scripts/building_interior.gd").new()
		interior.room_id = id
		interior.layout = village.layout
		world_view.world.add_child(interior)
		interiors.append(interior)
	string_pickup = Sprite2D.new()
	string_pickup.texture = preload("res://assets/items/pixel/string.svg")
	string_pickup.position = Vector2(-70,240)
	string_pickup.scale = Vector2(2,2)
	string_pickup.offset = Vector2(0,-10)
	string_pickup.hide()
	world_view.world.add_child(string_pickup)
	pickup_hint = Label.new()
	pickup_hint.text = "String • F to pick up"
	pickup_hint.position = Vector2(-40,-40)
	pickup_hint.scale = Vector2(0.5,0.5)
	pickup_hint.add_theme_color_override("font_color",Color("fff0ce"))
	string_pickup.add_child(pickup_hint)
	player = preload("res://scripts/player.gd").new()
	player.position = Vector2.ZERO
	world_view.world.add_child(player)
	player.set_physics_process(false)
	_add_world_marker(player,Color("3c8592"),"Player")
	var craftsman_at: Array = village.layout.interiors().workshop.craftsman
	_add_npc(1,"Craftsman","craftsman",village.layout.interior_origin("workshop") + Vector2(craftsman_at[0],craftsman_at[1]),Color("c38a45"),0.65,0.10,0.05,0.30)
	_add_npc(2,"Gatherer","gatherer",Vector2(-650,70),Color("648954"),0.50,0.25,0.05,0.70)
	var fade_layer := CanvasLayer.new()
	fade_layer.layer = 20
	add_child(fade_layer)
	travel_fade = ColorRect.new()
	travel_fade.color = Color(0.04,0.05,0.06,0)
	travel_fade.mouse_filter = Control.MOUSE_FILTER_STOP
	travel_fade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	fade_layer.add_child(travel_fade)
	travel_fade.hide()

func _physics_process(_delta: float) -> void:
	if not world_loaded or quitting or travelling or ui_owns_input(): return
	var room: String = village.layout.interior_at(player.position)
	if room.is_empty():
		var door: String = village.layout.doorway_at(player.position)
		if not door.is_empty() and Input.is_key_pressed(KEY_W) and player.position.y <= village.layout.exterior_spawn(door).y-12:
			_enter_building(door)
	else:
		var local: Vector2 = player.position-village.layout.interior_origin(room)
		if absf(local.x) <= 24 and local.y >= 180 and Input.is_key_pressed(KEY_S):
			_travel_to(village.layout.exterior_spawn(room), "down")

func _enter_building(id: String) -> void:
	var spawn: Array = village.layout.interiors()[id].spawn
	_travel_to(village.layout.interior_origin(id) + Vector2(spawn[0],spawn[1]), "up")

func _travel_to(at: Vector2, facing: String) -> void:
	if travelling or ui_owns_input() or not world_loaded or quitting: return
	travelling = true
	travel_fade.show()
	player.velocity = Vector2.ZERO
	player.set_physics_process(false)
	var fade_out := create_tween()
	fade_out.tween_property(travel_fade,"color:a",1.0,0.12)
	await fade_out.finished
	player.position = at
	player.get_child(0).facing = facing
	_update_current_npc()
	_save_position()
	var fade_in := create_tween()
	fade_in.tween_property(travel_fade,"color:a",0.0,0.12)
	await fade_in.finished
	travelling = false
	travel_fade.hide()


func make_button(text: String, callback: Callable, parent: Node) -> Button:
	var control := Button.new()
	control.text = text
	control.pressed.connect(callback)
	parent.add_child(control)
	return control

func _build_ui() -> void:
	var hud := CanvasLayer.new()
	add_child(hud)
	ui = Control.new()
	ui.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	ui.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ui.theme = Styles.create()
	hud.add_child(ui)
	for npc in npc_nodes.values():
		npc.label.reparent(ui)
		npc.label.custom_minimum_size = Vector2(160,0)
		npc.label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	var heading := Label.new()
	heading.position = Vector2(24, 16)
	heading.text = "WILLOWBROOK"
	heading.add_theme_font_size_override("font_size", 32)
	heading.add_theme_color_override("font_color", Color("fff0ce"))
	ui.add_child(heading)
	var hud_row := HBoxContainer.new()
	ui.add_child(hud_row)
	hud_row.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT)
	hud_row.offset_left = -280
	hud_row.offset_right = -24
	hud_row.offset_top = 16
	bag_button = make_button("Bag • I", _toggle_bag, hud_row)
	make_button("Quests", func():
		var opening := not quest_panel.visible
		_close_overlays()
		quest_panel.visible = opening, hud_row)
	quest_panel = preload("res://scripts/quest_panel.gd").new()
	ui.add_child(quest_panel)
	quest_panel.start_requested.connect(func(): _quest_call("start"))
	inventory_label = Label.new()
	inventory_label.position = Vector2(24, 52)
	inventory_label.text = "Loading village..."
	inventory_label.add_theme_color_override("font_color", Color("fff0ce"))
	ui.add_child(inventory_label)
	interaction_label = Label.new()
	ui.add_child(interaction_label)
	interaction_label.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_LEFT)
	interaction_label.offset_left = 24
	interaction_label.offset_top = -76
	interaction_label.add_theme_color_override("font_color", Color("fff0ce"))
	var help := Label.new()
	help_label = help
	help.text = "WASD Move • E Talk • F Pick up • I Bag • Esc Menu"
	ui.add_child(help)
	help.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_LEFT)
	help.offset_left = 24
	help.offset_top = -44
	help.add_theme_color_override("font_color", Color("fff0ce"))
	inventory_drawer = PanelContainer.new()
	inventory_compact_theme = Styles.compact_overlay()
	ui.add_child(inventory_drawer)
	inventory_drawer.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	inventory_drawer.offset_left = -310
	inventory_drawer.offset_right = 310
	inventory_drawer.offset_top = -210
	inventory_drawer.offset_bottom = 40
	var contents := VBoxContainer.new()
	inventory_drawer.add_child(contents)
	var title_row := HBoxContainer.new()
	contents.add_child(title_row)
	var title := Label.new()
	title.text = "YOUR SATCHEL"
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title_row.add_child(title)
	make_button("Close", func(): inventory_drawer.hide(); bag_button.grab_focus(), title_row)
	var scroll := ScrollContainer.new()
	player_scroll = scroll
	scroll.custom_minimum_size.y = 144
	scroll.follow_focus = true
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	contents.add_child(scroll)
	player_grid = preload("res://scripts/item_grid.gd").new()
	scroll.add_child(player_grid)
	give_button = make_button("Select an item to give", _give_selected_item, contents)
	give_button.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	inventory_drawer.hide()
	for id in npc_nodes:
		var window := preload("res://scripts/chat_window.gd").new()
		window.backend_url = backend_url
		window.npc_id = id
		window.npc_name = npc_nodes[id].display_name
		ui.add_child(window)
		window.world_changed.connect(_apply_chat_state)
		window.overlay_opened.connect(func(_owner): inventory_drawer.hide(); quest_panel.hide())
		chat_windows[id] = window
	menu_layer = Control.new()
	ui.add_child(menu_layer)
	menu_layer.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var dim := ColorRect.new()
	dim.color = Color(0.10, 0.07, 0.04, 0.65)
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	menu_layer.add_child(dim)
	menu_panel = PanelContainer.new()
	menu_layer.add_child(menu_panel)
	menu_panel.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	menu_panel.offset_left = -220
	menu_panel.offset_right = 220
	menu_panel.offset_top = -208
	menu_panel.offset_bottom = 208
	var menu := VBoxContainer.new()
	menu.add_theme_constant_override("separation", 12)
	menu_panel.add_child(menu)
	var menu_title := Label.new()
	menu_title.text = "WILLOWBROOK • MENU"
	menu_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	menu.add_child(menu_title)
	resume_button = make_button("Resume", _resume_game, menu)
	restart_button = make_button("Restart Game", func(): restart_dialog.popup_centered(Vector2i(520, 180)), menu)
	quit_button = make_button("Quit Game", _begin_shutdown, menu)
	var larger := CheckButton.new()
	larger.text = "Larger text"
	larger.toggled.connect(func(enabled: bool):
		large_text = enabled
		ui.theme = Styles.create(enabled)
		restart_dialog.theme = ui.theme
		for window in chat_windows.values():
			window.preferred_height = 304 if enabled else 268
			window.paginate())
	menu.add_child(larger)
	menu_status = Label.new()
	menu_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	menu.add_child(menu_status)
	var recovery := HBoxContainer.new()
	menu.add_child(recovery)
	retry_button = make_button("Retry save", _begin_shutdown, recovery)
	back_button = make_button("Back", func(): save_error = false; menu_status.text = ""; retry_button.hide(); back_button.hide(); resume_button.grab_focus(), recovery)
	retry_button.hide()
	back_button.hide()
	var motion := CheckButton.new()
	motion.text = "Reduced scenery motion"
	motion.toggled.connect(func(enabled): village.set_reduced_motion(enabled))
	menu.add_child(motion)
	menu_layer.hide()
	restart_dialog = ConfirmationDialog.new()
	restart_dialog.theme = ui.theme
	restart_dialog.title = "Restart Game"
	restart_dialog.dialog_text = "Start again? This clears quests, inventories, chats and NPC memories."
	restart_dialog.dialog_autowrap = true
	restart_dialog.ok_button_text = "Restart"
	restart_dialog.confirmed.connect(_restart_game)
	restart_dialog.canceled.connect(func(): restart_button.grab_focus())
	ui.add_child(restart_dialog)
	position_request = HTTPRequest.new()
	position_request.timeout = 5
	add_child(position_request)
	position_request.request_completed.connect(_position_completed)
	var save_timer := Timer.new()
	save_timer.wait_time = 1.0
	save_timer.timeout.connect(_save_position)
	add_child(save_timer)
	save_timer.start()
	quest_request = HTTPRequest.new()
	quest_request.timeout = 10
	add_child(quest_request)
	quest_request.request_completed.connect(_quest_completed)
	var crafting_timer := Timer.new()
	crafting_timer.wait_time = 0.5
	crafting_timer.timeout.connect(func():
		if bow_state.get("phase") == "crafting" and not quest_busy: _quest_call("advance"))
	add_child(crafting_timer)
	crafting_timer.start()
	world_request = HTTPRequest.new()
	world_request.timeout = 10
	ui.add_child(world_request)
	world_request.request_completed.connect(_world_completed)
	var reconnect := Timer.new()
	reconnect.wait_time = 5.0
	reconnect.timeout.connect(func():
		if not world_loaded and not quitting: _load_world())
	add_child(reconnect)
	reconnect.start()


func _close_overlays() -> void:
	inventory_drawer.hide()
	quest_panel.hide()
	for window in chat_windows.values(): window.close_overlays()

func _toggle_bag() -> void:
	if quitting or menu_layer.visible: return
	var opening := not inventory_drawer.visible
	_close_overlays()
	inventory_drawer.visible = opening
	if opening: inventory_drawer.get_child(0).get_child(0).get_child(1).grab_focus()

func _open_menu() -> void:
	previous_focus = get_viewport().gui_get_focus_owner()
	player.set_physics_process(false)
	for window in chat_windows.values(): window.modal_blocked = true
	menu_layer.show()
	resume_button.grab_focus()

func _resume_game() -> void:
	if quitting: return
	menu_layer.hide()
	for window in chat_windows.values(): window.modal_blocked = false
	if is_instance_valid(previous_focus) and previous_focus.is_visible_in_tree(): previous_focus.grab_focus()

func _begin_shutdown() -> void:
	if quitting: return
	if not menu_layer.visible: _open_menu()
	restart_dialog.hide()
	save_error = false
	retry_button.hide()
	back_button.hide()
	quitting = true
	# Initial GET is safe to cancel; dispatched mutations must finish.
	if not world_loaded and world_busy:
		if not restart_in_flight:
			world_request.cancel_request()
			world_busy = false

func _open_dialogue() -> void:
	if current_npc == null or not world_loaded:
		return
	_close_overlays()
	for window in chat_windows.values():
		window.close_chat()
	active_npc_id = current_npc.npc_id
	chat_windows[active_npc_id].open_chat()


func _load_world() -> void:
	# Avoid replacing a conversation while its request is in flight.
	for window in chat_windows.values():
		if window.pending:
			return
	if world_busy or quitting: return
	world_busy = true
	if world_request.request(backend_url + "/world") != OK:
		world_busy = false


func _world_completed(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	world_busy = false
	restart_in_flight = false
	if result != HTTPRequest.RESULT_SUCCESS or code != 200:
		inventory_label.text = "Connecting to the village..."
		return
	var parsed: Variant = JSON.parse_string(body.get_string_from_utf8())
	if not parsed is Dictionary:
		return
	var data: Dictionary = parsed
	var saved: Dictionary = data.get("player_position", {"x": 0, "y": 0})
	player.position = Vector2(float(saved.get("x", 0)), float(saved.get("y", 0)))
	last_saved_position = player.position
	var recovered: Vector2 = village.layout.recover_position(player.position)
	if recovered != player.position:
		player.position = recovered
		recovery_notice = "Moved to clear ground beside new scenery • position will be saved"
		get_tree().create_timer(8).timeout.connect(func(): recovery_notice = "")
	for npc in data.get("npcs", []):
		var id := int(npc.get("id", 0))
		if chat_windows.has(id):
			chat_windows[id].set_inventory(npc.get("inventory", []))
			chat_windows[id].load_history(data.get("histories", {}).get(str(id), []))
			npc_nodes[id].apply_state(npc)
	_update_player(data)
	_update_quest(data.get("bow_quest", {}))
	world_loaded = true
	if player.position != last_saved_position: _save_position()


func _apply_chat_state(response: Dictionary) -> void:
	_update_player(response)
	_update_quest(response.get("bow_quest", {}))
	var npc: Dictionary = response.get("npc", {})
	var id := int(npc.get("id", 0))
	if npc_nodes.has(id):
		npc_nodes[id].apply_state(npc)


func _update_player(data: Dictionary) -> void:
	var items: Array = data.get("player_inventory", [])
	player_items = items.duplicate()
	if player_grid.items != items:
		player_grid.populate(items)
	inventory_label.text = ""
	bag_button.text = "Bag • %s • I" % items.size()


func _add_npc(npc_id: int, npc_name: String, role_name: String, position: Vector2, color: Color, trust: float, fear: float, aggression: float, curiosity: float) -> void:
	var npc := preload("res://scripts/npc.gd").new()
	npc.npc_id = npc_id
	npc.display_name = npc_name
	npc.role_name = role_name
	npc.position = position
	world_view.world.add_child(npc)

	var body := preload("res://scripts/person.gd").new()
	body.identity = role_name
	npc.add_child(body)

	var collider := CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = Vector2(24, 16)
	collider.shape = rect
	npc.add_child(collider)

	var name_label := Label.new()
	name_label.position = Vector2(-65, -84)
	name_label.add_theme_font_size_override("font_size", 19)
	name_label.add_theme_color_override("font_color",Color("fff0ce"))
	name_label.add_theme_color_override("font_shadow_color", Color.BLACK)
	name_label.add_theme_constant_override("shadow_offset_x", 1)
	name_label.add_theme_constant_override("shadow_offset_y", 1)
	npc.add_child(name_label)
	npc.label = name_label
	npc.refresh_label(trust, fear, aggression, curiosity)

	npc_nodes[npc_id] = npc


func _add_world_marker(target: Node2D, color: Color, text: String) -> void:
	var marker := preload("res://scripts/person.gd").new()
	marker.identity = "player"
	target.add_child(marker)

	var collider := CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = Vector2(24, 16)
	collider.shape = rect
	target.add_child(collider)


func _update_current_npc() -> void:
	current_npc = null
	var nearest_distance := 99999.0
	for npc in npc_nodes.values():
		var distance := player.global_position.distance_to(npc.global_position)
		if distance < 96.0 and distance < nearest_distance:
			nearest_distance = distance
			current_npc = npc


func _update_give_action() -> void:
	var disabled := true
	var caption := ""
	var item: String = player_grid.selected_item
	if item.is_empty():
		caption = "Select an item to give"
	elif _give_recipient() == null:
		caption = "Approach an NPC to give " + item.capitalize()
	else:
		caption = "Give %s to %s" % [item.capitalize(), _give_recipient().display_name]
		disabled = not world_loaded or chat_windows[_give_recipient().npc_id].pending or quitting or menu_layer.visible
	if give_button.disabled != disabled:
		give_button.disabled = disabled

	if give_button.text != caption:
		give_button.text = caption


func _give_recipient():
	for id in chat_windows:
		if chat_windows[id].visible: return npc_nodes[id]
	return current_npc

func _give_selected_item() -> void:
	var recipient = _give_recipient()
	if recipient == null or not player_items.has(player_grid.selected_item) or quitting or menu_layer.visible: return
	var window = chat_windows[recipient.npc_id]
	if window.pending: return
	inventory_drawer.hide()
	for other in chat_windows.values(): other.close_chat()
	active_npc_id = recipient.npc_id
	window.open_chat()
	window.transfer_item(player_grid.selected_item, "to_npc")


func _update_quest(data: Dictionary) -> void:
	if data.is_empty(): return
	bow_state = data
	if data.get("phase") == "crafting": inventory_drawer.hide()
	quest_panel.update_quest(data)
	string_pickup.visible = data.get("string_available", false)
	var at: Dictionary = data.get("string_position",{"x":-70,"y":240})
	string_pickup.position = Vector2(float(at.x),float(at.y))


func _quest_call(action: String, payload: Dictionary = {}) -> void:
	if quest_busy or not world_loaded or quitting or restart_dialog.visible: return
	quest_busy = true
	quest_panel.start_button.disabled = true
	var error := quest_request.request(backend_url + "/quests/bow/" + action, PackedStringArray(["Content-Type: application/json"]), HTTPClient.METHOD_POST, JSON.stringify(payload))
	if error != OK:
		quest_busy = false
		quest_panel.start_button.disabled = false
		quest_panel.objective.text = "Could not reach the village. Try again."


func _quest_completed(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	quest_busy = false
	quest_panel.start_button.disabled = false
	var parsed: Variant = JSON.parse_string(body.get_string_from_utf8())
	if result != HTTPRequest.RESULT_SUCCESS or code != 200 or not parsed is Dictionary:
		quest_panel.show()
		quest_panel.objective.text = "Could not update quest. Move closer to the item or try again."
		return
	var data: Dictionary = parsed
	_update_quest(data.get("bow_quest", {}))
	_update_player(data)
	for npc in data.get("npcs", []):
		var id := int(npc.get("id", 0))
		if chat_windows.has(id):
			chat_windows[id].set_inventory(npc.get("inventory", []))
			npc_nodes[id].apply_state(npc)
	if data.get("reward_dialogue"):
		quest_panel.show()
		for id in chat_windows:
			if npc_nodes[id].role_name == "craftsman":
				chat_windows[id].append_dialogue("Craftsman", str(data.reward_dialogue))


func _operations_pending() -> bool:
	if travelling or quest_busy or position_busy or world_busy: return true
	for window in chat_windows.values():
		if window.pending: return true
	return false


func _restart_game() -> void:
	if _operations_pending() or not world_loaded or quitting: return
	menu_layer.hide()
	restart_in_flight = true
	world_loaded = false
	world_busy = true
	inventory_drawer.hide()
	quest_panel.hide()
	for window in chat_windows.values(): window.close_chat()
	var error := world_request.request(backend_url + "/world/new-game", PackedStringArray(), HTTPClient.METHOD_POST)
	if error != OK:
		world_busy = false
		inventory_label.text = "Restart could not be sent. Reconnecting..."


func _save_position() -> void:
	if not world_loaded or position_busy or world_busy or restart_dialog.visible or save_error: return
	if player.position == last_saved_position:
		if quitting and not _operations_pending(): get_tree().quit()
		return
	sent_position = player.position
	position_busy = true
	var error := position_request.request(backend_url + "/world/player-position", PackedStringArray(["Content-Type: application/json"]), HTTPClient.METHOD_PUT, JSON.stringify({"x": sent_position.x, "y": sent_position.y}))
	if error != OK:
		position_busy = false
		_save_failed()


func _position_completed(result: int, code: int, _headers: PackedStringArray, _body: PackedByteArray) -> void:
	position_busy = false
	if result == HTTPRequest.RESULT_SUCCESS and code == 200:
		last_saved_position = sent_position
	else:
		_save_failed()


func _save_failed() -> void:
	if not quitting:
		inventory_label.text = "Position save failed. Will retry when connected."
		return
	quitting = false
	save_error = true
	menu_layer.show()
	menu_status.text = "Save failed. Check the connection, then Retry save or Back."
	retry_button.show()
	back_button.show()
	retry_button.grab_focus()


func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST: _begin_shutdown()
