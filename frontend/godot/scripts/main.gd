extends Node2D

@export var backend_url := "http://127.0.0.1:8000"

var player: CharacterBody2D
var npc_nodes: Dictionary = {}
var current_npc: Area2D
var chat_windows: Dictionary = {}
var inventory_label: Label
var interaction_label: Label
var world_request: HTTPRequest
var world_loaded := false
var inventory_drawer: PanelContainer
var player_grid: GridContainer
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
var district: Node3D
var pause_menu: Control
var paused := false
var restart_queued := false


func _ready() -> void:
	get_tree().auto_accept_quit = false
	_build_world()
	_build_ui()
	_load_world()


func _process(_delta: float) -> void:
	player.set_physics_process(false)
	restart_button.disabled = not world_loaded or quitting or restart_queued
	if restart_queued and not _operations_pending(): _restart_game()
	if quitting and not _operations_pending(): _save_position()
	_update_current_npc()
	interaction_label.text = "E  Talk to " + current_npc.display_name if current_npc != null else "Approach an operator to talk"
	_update_give_action()
	if string_pickup.visible and player.position.distance_to(string_pickup.position) < 64:
		interaction_label.text = "F  Pick up fiber cable"


func _unhandled_input(event: InputEvent) -> void:
	if not world_loaded or quitting or restart_dialog.visible: return
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_ESCAPE:
			_set_paused(not paused)
			get_viewport().set_input_as_handled()
			return
		if paused: return
		if event.keycode == KEY_E:
			_open_dialogue()
		elif event.keycode == KEY_F and string_pickup.visible and player.position.distance_to(string_pickup.position) < 64:
			_quest_call("pickup-string", {"x": player.position.x, "y": player.position.y})
		elif event.keycode == KEY_I:
			inventory_drawer.visible = not inventory_drawer.visible


func _build_world() -> void:
	string_pickup = Sprite2D.new()
	string_pickup.texture = preload("res://assets/items/fiber_cable.svg")
	string_pickup.position = Vector2(-70, 240)
	string_pickup.scale = Vector2(0.65, 0.65)
	string_pickup.hide()
	string_pickup.modulate.a = 0.0
	add_child(string_pickup)
	pickup_hint = Label.new()
	pickup_hint.text = "FIBER CABLE"
	pickup_hint.position = Vector2(-58, -72)
	_apply_holo_label(pickup_hint, 14, Color("19f6ff"))
	string_pickup.add_child(pickup_hint)

	player = preload("res://scripts/player.gd").new()
	player.position = Vector2(0, 0)
	add_child(player)
	player.set_physics_process(false)
	player.hide()

	_add_npc(1, "Neon Techsmith", "craftsman", Vector2(360, -120), Color("ffb84a"), 0.65, 0.10, 0.05, 0.30)
	_add_npc(2, "Data Broker", "gatherer", Vector2(-430, -140), Color("ff3df2"), 0.50, 0.25, 0.05, 0.70)
	for npc in npc_nodes.values(): npc.hide()
	district = preload("res://scripts/district_3d.gd").new()
	district.controller = self
	add_child(district)


func _build_ui() -> void:
	var hud := CanvasLayer.new()
	add_child(hud)
	for id in npc_nodes:
		var window := preload("res://scripts/chat_window.gd").new()
		window.backend_url = backend_url
		window.npc_id = id
		window.npc_name = npc_nodes[id].display_name
		hud.add_child(window)
		window.world_changed.connect(_apply_chat_state)
		chat_windows[id] = window
	var heading := Label.new()
	heading.position = Vector2(26, 22)
	heading.text = "NEON DISTRICT"
	_apply_holo_label(heading, 22, Color("e9fbff"))
	hud.add_child(heading)
	quest_panel = preload("res://scripts/quest_panel.gd").new()
	hud.add_child(quest_panel)
	quest_panel.start_requested.connect(func(): _quest_call("start"))
	var pause_button := Button.new()
	pause_button.text = "Pause"
	pause_button.position = Vector2(26, 70)
	pause_button.custom_minimum_size = Vector2(110, 36)
	pause_button.pressed.connect(func(): _set_paused(true))
	hud.add_child(pause_button)
	var pause_layer := CanvasLayer.new()
	pause_layer.layer = 10
	add_child(pause_layer)
	pause_menu = preload("res://scripts/pause_menu.gd").new()
	pause_layer.add_child(pause_menu)
	restart_button = pause_menu.restart_button
	pause_menu.resume_requested.connect(func(): _set_paused(false))
	pause_menu.missions_requested.connect(func(): _set_paused(false); quest_panel.show())
	pause_menu.inventory_requested.connect(func(): _set_paused(false); inventory_drawer.show())
	pause_menu.zoom_changed.connect(func(value): district.camera_distance = value)
	pause_menu.fullscreen_changed.connect(func(enabled):
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN if enabled else DisplayServer.WINDOW_MODE_WINDOWED))
	pause_menu.quit_requested.connect(func(): _notification(NOTIFICATION_WM_CLOSE_REQUEST))
	restart_dialog = ConfirmationDialog.new()
	restart_dialog.title = "Restart Game"
	restart_dialog.dialog_text = "Start again? This clears missions, inventories, chats and NPC memories."
	restart_dialog.ok_button_text = "Restart"
	restart_dialog.confirmed.connect(_restart_game)
	hud.add_child(restart_dialog)
	restart_button.pressed.connect(func():
		_set_paused(true)
		restart_dialog.popup_centered())
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
		if bow_state.get("phase") == "crafting" and not quest_busy and not restart_queued: _quest_call("advance"))
	add_child(crafting_timer)
	crafting_timer.start()
	var bag := PanelContainer.new()
	bag.position = Vector2(24, 544)
	bag.custom_minimum_size = Vector2(606, 152)
	var style := StyleBoxFlat.new()
	style.bg_color = _ca("090d19", 0.92)
	style.border_color = _ca("19f6ff", 0.70)
	style.set_border_width_all(1)
	style.set_corner_radius_all(10)
	style.content_margin_left = 16
	style.content_margin_right = 16
	style.content_margin_top = 12
	style.content_margin_bottom = 12
	bag.add_theme_stylebox_override("panel", style)
	hud.add_child(bag)
	var layout := VBoxContainer.new()
	bag.add_child(layout)
	inventory_label = Label.new()
	inventory_label.text = "Loading supplies..."
	inventory_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_apply_holo_label(inventory_label, 18, Color("e9fbff"))
	layout.add_child(inventory_label)
	bag_button = Button.new()
	bag_button.hide()
	layout.add_child(bag_button)
	inventory_drawer = PanelContainer.new()
	inventory_drawer.position = Vector2(24, 266)
	inventory_drawer.size = Vector2(606, 266)
	var drawer_style := style.duplicate()
	drawer_style.border_color = Color("ff3df2")
	drawer_style.set_border_width_all(1)
	inventory_drawer.add_theme_stylebox_override("panel", drawer_style)
	hud.add_child(inventory_drawer)
	var contents := VBoxContainer.new()
	contents.add_theme_constant_override("separation", 10)
	inventory_drawer.add_child(contents)
	var bag_heading := Label.new()
	bag_heading.text = "RUNNER LOADOUT"
	_apply_holo_label(bag_heading, 20, Color("19f6ff"))
	contents.add_child(bag_heading)
	var item_scroll := ScrollContainer.new()
	item_scroll.custom_minimum_size.y = 136
	item_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	item_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	contents.add_child(item_scroll)
	player_grid = preload("res://scripts/item_grid.gd").new()
	item_scroll.add_child(player_grid)
	give_button = Button.new()
	give_button.custom_minimum_size.y = 42
	give_button.pressed.connect(_give_selected_item)
	contents.add_child(give_button)
	inventory_drawer.hide()
	interaction_label = Label.new()
	_apply_holo_label(interaction_label, 16, Color("e9fbff"))
	layout.add_child(interaction_label)
	var help := Label.new()
	help.text = "WASD Move • E Talk • F Pick up • I Bag • Esc Pause"
	_apply_holo_label(help, 13, Color("9fb8c9"))
	layout.add_child(help)
	world_request = HTTPRequest.new()
	hud.add_child(world_request)
	world_request.request_completed.connect(_world_completed)
	var reconnect := Timer.new()
	reconnect.wait_time = 5.0
	reconnect.timeout.connect(func():
		if not world_loaded: _load_world())
	add_child(reconnect)
	reconnect.start()


func _open_dialogue() -> void:
	if current_npc == null or not world_loaded:
		return
	for window in chat_windows.values():
		window.close_chat()
	chat_windows[current_npc.npc_id].open_chat()


func _set_paused(value: bool) -> void:
	paused = value
	pause_menu.visible = value
	pause_menu.zoom.set_value_no_signal(district.camera_distance)
	if value:
		inventory_drawer.hide()
		quest_panel.hide()
		for window in chat_windows.values(): window.close_chat()
	get_viewport().gui_release_focus()


func _load_world() -> void:
	# Avoid replacing a conversation while its request is in flight.
	for window in chat_windows.values():
		if window.pending:
			return
	if world_busy: return
	world_busy = true
	if world_request.request(backend_url + "/world") != OK:
		world_busy = false


func _world_completed(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	world_busy = false
	if result != HTTPRequest.RESULT_SUCCESS or code != 200:
		inventory_label.text = "Connecting to the grid..."
		return
	var parsed: Variant = JSON.parse_string(body.get_string_from_utf8())
	if not parsed is Dictionary:
		return
	var data: Dictionary = parsed
	var saved: Dictionary = data.get("player_position", {"x": 0, "y": 0})
	player.position = Vector2(float(saved.get("x", 0)), float(saved.get("y", 0)))
	last_saved_position = player.position
	for npc in data.get("npcs", []):
		var id := int(npc.get("id", 0))
		if chat_windows.has(id):
			chat_windows[id].set_inventory(npc.get("inventory", []))
			chat_windows[id].load_history(data.get("histories", {}).get(str(id), []))
			npc_nodes[id].apply_state(npc)
	_update_player(data)
	_update_quest(data.get("bow_quest", {}))
	world_loaded = true


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
	inventory_label.text = "LOADOUT  •  %s items" % items.size()
	bag_button.text = "Open inventory  •  I"


func _add_npc(npc_id: int, npc_name: String, role_name: String, position: Vector2, color: Color, trust: float, fear: float, aggression: float, curiosity: float) -> void:
	var npc := preload("res://scripts/npc.gd").new()
	npc.npc_id = npc_id
	npc.display_name = npc_name
	npc.role_name = role_name
	npc.position = position
	add_child(npc)

	var body := preload("res://scripts/person.gd").new()
	body.coat = color
	body.apron = role_name == "craftsman"
	npc.add_child(body)

	var collider := CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = Vector2(44, 44)
	collider.shape = rect
	npc.add_child(collider)

	var name_label := Label.new()
	name_label.position = Vector2(-70, -104)
	_apply_holo_label(name_label, 14, Color("e9fbff"))
	npc.add_child(name_label)
	npc.label = name_label
	npc.refresh_label(trust, fear, aggression, curiosity)

	npc_nodes[npc_id] = npc


func _add_world_marker(target: Node2D, color: Color, text: String) -> void:
	var marker := preload("res://scripts/person.gd").new()
	marker.coat = color
	target.add_child(marker)

	var label := Label.new()
	label.position = Vector2(-32, -92)
	label.text = text
	_apply_holo_label(label, 13, Color("19f6ff"))
	target.add_child(label)

	var collider := CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = Vector2(36, 36)
	collider.shape = rect
	target.add_child(collider)


func _update_current_npc() -> void:
	current_npc = null
	var shop_id: int = district.shop_for_position(player.position * 0.025)
	if shop_id != 0:
		current_npc = npc_nodes[shop_id]
		return
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
	elif current_npc == null:
		caption = "Approach an NPC to give " + item.capitalize()
	else:
		caption = "Give %s to %s" % [item.capitalize(), current_npc.display_name]
		disabled = not world_loaded or chat_windows[current_npc.npc_id].pending
	if give_button.disabled != disabled:
		give_button.disabled = disabled

	if give_button.text != caption:
		give_button.text = caption


func _give_selected_item() -> void:
	if current_npc == null or not player_items.has(player_grid.selected_item): return
	var window = chat_windows[current_npc.npc_id]
	if window.pending: return
	_open_dialogue()
	window.transfer_item(player_grid.selected_item, "to_npc")


func _update_quest(data: Dictionary) -> void:
	if data.is_empty(): return
	bow_state = data
	if data.get("phase") == "crafting": inventory_drawer.hide()
	quest_panel.update_quest(data)
	string_pickup.visible = data.get("string_available", false)


func _quest_call(action: String, payload: Dictionary = {}) -> void:
	if quest_busy or not world_loaded or quitting or restart_dialog.visible: return
	quest_busy = true
	quest_panel.start_button.disabled = true
	var error := quest_request.request(backend_url + "/quests/bow/" + action, PackedStringArray(["Content-Type: application/json"]), HTTPClient.METHOD_POST, JSON.stringify(payload))
	if error != OK:
		quest_busy = false
		quest_panel.start_button.disabled = false
		quest_panel.objective.text = "Could not reach the grid. Try again."


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
				chat_windows[id].append_dialogue("Neon Techsmith", str(data.reward_dialogue))


func _operations_pending() -> bool:
	if quest_busy or position_busy or world_busy: return true
	for window in chat_windows.values():
		if window.pending: return true
	return false


func _restart_game() -> void:
	if not world_loaded: return
	if _operations_pending():
		restart_queued = true
		return
	restart_queued = false
	_set_paused(false)
	district.reset_patrols()
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
	if not world_loaded or position_busy or world_busy or restart_dialog.visible: return
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
	quitting = false
	inventory_label.text = "Position save failed. Check the backend and try closing again."


func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST:
		if not world_loaded:
			get_tree().quit()
		else:
			restart_dialog.hide()
			quitting = true
			inventory_drawer.hide()
			quest_panel.hide()
			for window in chat_windows.values(): window.close_chat()


func _build_collision() -> void:
	# Map edge blockers.
	_add_wall_rect(Vector2(0, -548), Vector2(2100, 120))
	_add_wall_rect(Vector2(0, 548), Vector2(2100, 120))
	_add_wall_rect(Vector2(-1048, 0), Vector2(160, 1180))
	_add_wall_rect(Vector2(1048, 0), Vector2(160, 1180))

	# Rooftops and dense background architecture. Doorways/interiors stay open.
	_add_wall_rect(Vector2(0, -405), Vector2(1620, 130))
	_add_wall_rect(Vector2(-662, -190), Vector2(260, 230))
	_add_wall_rect(Vector2(664, -135), Vector2(230, 350))
	_add_wall_rect(Vector2(300, -270), Vector2(500, 95))
	_add_wall_rect(Vector2(-835, 120), Vector2(190, 360))
	_add_wall_rect(Vector2(818, 238), Vector2(210, 450))

	# Foreground buildings and railings; these stop the player from walking over structures.
	_add_wall_poly(PackedVector2Array([
		Vector2(-836, 470), Vector2(-836, 270), Vector2(-638, 318), Vector2(-608, 470)
	]))
	_add_wall_poly(PackedVector2Array([
		Vector2(520, 470), Vector2(836, 470), Vector2(836, 184), Vector2(650, 244)
	]))
	_add_wall_rect(Vector2(-42, 382), Vector2(272, 124))


func _add_wall_rect(center: Vector2, size: Vector2) -> void:
	var body := StaticBody2D.new()
	body.position = center
	var collider := CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = size
	collider.shape = rect
	body.add_child(collider)
	add_child(body)


func _add_wall_poly(points: PackedVector2Array) -> void:
	var body := StaticBody2D.new()
	var collider := CollisionPolygon2D.new()
	collider.polygon = points
	body.add_child(collider)
	add_child(body)


func _apply_holo_label(label: Label, size: int, color: Color) -> void:
	label.add_theme_font_override("font", _cyber_font())
	label.add_theme_font_size_override("font_size", size)
	label.add_theme_color_override("font_color", color)
	label.add_theme_color_override("font_outline_color", Color("02050a"))
	label.add_theme_constant_override("outline_size", 5)


func _cyber_font() -> SystemFont:
	var font := SystemFont.new()
	font.font_names = PackedStringArray(["Orbitron", "Rajdhani", "Eurostile", "Avenir Next Condensed", "Menlo"])
	return font


func _ca(hex: String, alpha: float) -> Color:
	var color := Color(hex)
	color.a = alpha
	return color
