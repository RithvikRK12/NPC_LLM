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


func _ready() -> void:
	_build_world()
	_build_ui()
	_load_world()


func _process(_delta: float) -> void:
	_update_current_npc()
	interaction_label.text = "E  Talk to " + current_npc.display_name if current_npc != null else "Approach a villager to talk"
	_update_give_action()
	if string_pickup.visible and player.position.distance_to(string_pickup.position) < 64:
		interaction_label.text = "F  Pick up string"


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_E:
			_open_dialogue()
		elif event.keycode == KEY_F and string_pickup.visible and player.position.distance_to(string_pickup.position) < 64:
			_quest_call("pickup-string", {"x": player.position.x, "y": player.position.y})
		elif event.keycode == KEY_I:
			inventory_drawer.visible = not inventory_drawer.visible
		elif event.keycode == KEY_ESCAPE:
			inventory_drawer.hide()
			quest_panel.hide()
			for window in chat_windows.values():
				window.close_chat()


func _build_world() -> void:
	add_child(preload("res://scripts/village.gd").new())
	string_pickup = Sprite2D.new()
	string_pickup.texture = preload("res://assets/items/string.svg")
	string_pickup.position = Vector2(-70, 240)
	string_pickup.scale = Vector2(0.65, 0.65)
	string_pickup.hide()
	add_child(string_pickup)
	pickup_hint = Label.new()
	pickup_hint.text = "String • F to pick up"
	pickup_hint.position = Vector2(-80, -65)
	pickup_hint.add_theme_color_override("font_color", Color("f5df9a"))
	string_pickup.add_child(pickup_hint)
	var workshop := StaticBody2D.new()
	workshop.position = Vector2(195, -160)
	var walls := CollisionShape2D.new()
	var footprint := RectangleShape2D.new()
	footprint.size = Vector2(230, 125)
	walls.shape = footprint
	workshop.add_child(walls)
	add_child(workshop)

	player = preload("res://scripts/player.gd").new()
	player.position = Vector2(0, 0)
	add_child(player)
	_add_world_marker(player, Color(0.25, 0.70, 0.90), "Player")
	var camera := Camera2D.new()
	camera.zoom = Vector2(1.0, 1.0)
	camera.position_smoothing_enabled = true
	camera.position = Vector2(290, 0)
	player.add_child(camera)
	camera.make_current()

	_add_npc(1, "Craftsman", "craftsman", Vector2(180, -20), Color(0.80, 0.55, 0.20), 0.65, 0.10, 0.05, 0.30)
	_add_npc(2, "Gatherer", "gatherer", Vector2(-170, 35), Color(0.28, 0.75, 0.35), 0.50, 0.25, 0.05, 0.70)


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
	heading.text = "WILLOWBROOK\nThe forest & the forge"
	heading.add_theme_font_size_override("font_size", 26)
	heading.add_theme_color_override("font_color", Color("f4e7c9"))
	hud.add_child(heading)
	quest_panel = preload("res://scripts/quest_panel.gd").new()
	hud.add_child(quest_panel)
	quest_panel.start_requested.connect(func(): _quest_call("start"))
	var quests_button := Button.new()
	quests_button.text = "Quests"
	quests_button.position = Vector2(26, 108)
	quests_button.custom_minimum_size = Vector2(150, 34)
	quests_button.pressed.connect(func(): quest_panel.visible = not quest_panel.visible; inventory_drawer.hide())
	hud.add_child(quests_button)
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
	var bag := PanelContainer.new()
	bag.position = Vector2(24, 544)
	bag.custom_minimum_size = Vector2(606, 152)
	var style := StyleBoxFlat.new()
	style.bg_color = Color("202a27")
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
	inventory_label.add_theme_font_size_override("font_size", 19)
	layout.add_child(inventory_label)
	bag_button = Button.new()
	bag_button.text = "Open inventory  •  I"
	bag_button.pressed.connect(func(): inventory_drawer.visible = not inventory_drawer.visible; quest_panel.hide())
	layout.add_child(bag_button)
	inventory_drawer = PanelContainer.new()
	inventory_drawer.position = Vector2(24, 266)
	inventory_drawer.size = Vector2(606, 266)
	var drawer_style := style.duplicate()
	drawer_style.border_color = Color("b49e6b")
	drawer_style.set_border_width_all(1)
	inventory_drawer.add_theme_stylebox_override("panel", drawer_style)
	hud.add_child(inventory_drawer)
	var contents := VBoxContainer.new()
	contents.add_theme_constant_override("separation", 10)
	inventory_drawer.add_child(contents)
	var bag_heading := Label.new()
	bag_heading.text = "YOUR SATCHEL"
	bag_heading.add_theme_color_override("font_color", Color("ead5a4"))
	bag_heading.add_theme_font_size_override("font_size", 22)
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
	layout.add_child(interaction_label)
	var help := Label.new()
	help.text = "WASD Move • E Talk • F Pick up • I Bag • Esc Close"
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


func _load_world() -> void:
	# Avoid replacing a conversation while its request is in flight.
	for window in chat_windows.values():
		if window.pending:
			return
	if not world_loaded:
		world_request.request(backend_url + "/world/new-game", PackedStringArray(), HTTPClient.METHOD_POST)
	else:
		world_request.request(backend_url + "/world")


func _world_completed(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if result != HTTPRequest.RESULT_SUCCESS or code != 200:
		inventory_label.text = "Connecting to the village..."
		return
	var parsed: Variant = JSON.parse_string(body.get_string_from_utf8())
	if not parsed is Dictionary:
		return
	var data: Dictionary = parsed
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
	inventory_label.text = "SATCHEL  •  %s items" % items.size()
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
	name_label.position = Vector2(-65, -83)
	name_label.add_theme_font_size_override("font_size", 16)
	name_label.add_theme_color_override("font_shadow_color", Color.BLACK)
	name_label.add_theme_constant_override("shadow_offset_x", 1)
	name_label.add_theme_constant_override("shadow_offset_y", 1)
	npc.add_child(name_label)
	npc.label = name_label
	npc.refresh_label(trust, fear, aggression, curiosity)

	npc_nodes[npc_id] = npc


func _add_world_marker(target: Node2D, color: Color, text: String) -> void:
	var marker := preload("res://scripts/person.gd").new()
	marker.coat = color
	target.add_child(marker)

	var label := Label.new()
	label.position = Vector2(-20, -72)
	label.text = text
	target.add_child(label)

	var collider := CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = Vector2(36, 36)
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
	if quest_busy or not world_loaded: return
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
