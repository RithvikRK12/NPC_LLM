extends PanelContainer

signal world_changed(response: Dictionary)
var backend_url := "http://127.0.0.1:8000"
var npc_id := 0
var npc_name := "NPC"
var dialogue_log: RichTextLabel
var message_input: LineEdit
var send_button: Button
var npc_inventory_label: Label
var item_grid: GridContainer
var take_button: Button
var clear_button: Button
var operation := "chat"
var request: HTTPRequest
var pending := false


func _ready() -> void:
	position = Vector2(670, 24)
	custom_minimum_size = Vector2(586, 672)
	size = custom_minimum_size
	var style := StyleBoxFlat.new()
	style.bg_color = Color("202a27")
	style.border_color = Color("7f8c69")
	style.set_border_width_all(2)
	style.set_corner_radius_all(12)
	style.content_margin_left = 22
	style.content_margin_right = 22
	style.content_margin_top = 20
	style.content_margin_bottom = 20
	add_theme_stylebox_override("panel", style)
	var layout := VBoxContainer.new()
	layout.add_theme_constant_override("separation", 12)
	add_child(layout)
	var title := Label.new()
	title.text = npc_name
	title.add_theme_font_size_override("font_size", 26)
	title.add_theme_color_override("font_color", Color("ead5a4"))
	layout.add_child(title)
	npc_inventory_label = Label.new()
	npc_inventory_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	npc_inventory_label.text = "SUPPLIES • Select an item to request it"
	layout.add_child(npc_inventory_label)
	var supply_scroll := ScrollContainer.new()
	supply_scroll.custom_minimum_size.y = 108
	supply_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	layout.add_child(supply_scroll)
	item_grid = preload("res://scripts/item_grid.gd").new()
	supply_scroll.add_child(item_grid)
	item_grid.item_selected.connect(func(item: String): take_button.text = "Request " + item.capitalize(); take_button.disabled = pending)
	take_button = Button.new()
	take_button.text = "Select a supply above"
	take_button.disabled = true
	take_button.custom_minimum_size.y = 32
	take_button.pressed.connect(func(): transfer_item(item_grid.selected_item, "to_player"))
	layout.add_child(take_button)
	dialogue_log = RichTextLabel.new()
	dialogue_log.custom_minimum_size = Vector2(540, 170)
	dialogue_log.size_flags_vertical = Control.SIZE_EXPAND_FILL
	dialogue_log.scroll_following = true
	dialogue_log.add_theme_font_size_override("normal_font_size", 19)
	dialogue_log.add_theme_constant_override("line_separation", 5)
	layout.add_child(dialogue_log)
	message_input = LineEdit.new()
	message_input.placeholder_text = "Try: Can you give me wood?"
	message_input.custom_minimum_size.y = 48
	message_input.max_length = 500
	message_input.add_theme_font_size_override("font_size", 18)
	message_input.text_submitted.connect(func(_text: String): submit())
	layout.add_child(message_input)
	var buttons := HBoxContainer.new()
	layout.add_child(buttons)
	send_button = Button.new()
	send_button.text = "Send"
	send_button.custom_minimum_size = Vector2(132, 40)
	send_button.pressed.connect(submit)
	buttons.add_child(send_button)
	var close := Button.new()
	close.text = "Close • Esc"
	close.custom_minimum_size = Vector2(132, 40)
	close.pressed.connect(close_chat)
	buttons.add_child(close)
	clear_button = Button.new()
	clear_button.text = "Clear chat"
	clear_button.tooltip_text = "Clear only this NPC's saved conversation and dialogue memories. Items stay unchanged."
	clear_button.custom_minimum_size = Vector2(120, 40)
	clear_button.pressed.connect(clear_chat)
	buttons.add_child(clear_button)
	request = HTTPRequest.new()
	request.timeout = 160
	add_child(request)
	request.request_completed.connect(_completed)
	hide()


func open_chat() -> void:
	show()
	message_input.grab_focus()


func close_chat() -> void:
	message_input.release_focus()
	hide()


func set_inventory(items: Array) -> void:
	if item_grid.items != items:
		item_grid.populate(items)
	take_button.disabled = pending or item_grid.selected_item.is_empty()
	take_button.text = "Request " + item_grid.selected_item.capitalize() if not item_grid.selected_item.is_empty() else "Select a supply above"


func load_history(turns: Array) -> void:
	dialogue_log.clear()
	for turn in turns:
		append_dialogue("Player", str(turn.get("player", "")))
		append_dialogue(npc_name, str(turn.get("npc", "")))
	if turns.is_empty():
		append_dialogue("System", "Your conversation with %s starts here." % npc_name)


func append_dialogue(speaker: String, text: String) -> void:
	dialogue_log.push_color(Color("b3c3ad") if speaker == "System" else Color("ead5a4"))
	dialogue_log.add_text(speaker + "\n")
	dialogue_log.pop()
	dialogue_log.add_text(text + "\n\n")


func submit() -> void:
	if pending or not visible:
		return
	var message := message_input.text.strip_edges()
	if message.is_empty():
		return
	operation = "chat"
	start_request()
	append_dialogue("Player", message)
	var error := request.request(backend_url + "/chat", PackedStringArray(["Content-Type: application/json"]), HTTPClient.METHOD_POST, JSON.stringify({"npc_id": npc_id, "player_message": message}))
	if error != OK:
		finish()
		append_dialogue("System", "Could not send: " + error_string(error))
	else:
		message_input.clear()


func finish() -> void:
	pending = false
	send_button.disabled = false
	send_button.text = "Send"
	clear_button.disabled = false
	take_button.disabled = item_grid.selected_item.is_empty()


func _completed(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	finish()
	if result != HTTPRequest.RESULT_SUCCESS or code != 200:
		append_dialogue("System", "Request failed (%s). Check the backend and try again." % code)
		return
	var parsed: Variant = JSON.parse_string(body.get_string_from_utf8())
	if not parsed is Dictionary:
		append_dialogue("System", "Invalid response from backend.")
		return
	var response: Dictionary = parsed
	if operation == "clear":
		load_history([])
		return
	append_dialogue(npc_name, str(response.get("final_dialogue", "")))
	var output: Dictionary = response.get("validated_output", {})
	if output.get("action") == "give_item":
		append_dialogue("System", "%s → Player: %s" % [npc_name, output.get("item", "item")])
	elif output.get("action") == "receive_item":
		append_dialogue("System", "Player → %s: %s" % [npc_name, output.get("item", "item")])
	if output.get("intent") == "confirm_transfer":
		message_input.placeholder_text = "Explain why you need it, or type cancel..."
		if visible: message_input.grab_focus()
	else:
		message_input.placeholder_text = "Talk to " + npc_name + "..."
	set_inventory(response.get("npc", {}).get("inventory", []))
	world_changed.emit(response)


func start_request() -> void:
	pending = true
	send_button.disabled = true
	clear_button.disabled = true
	take_button.disabled = true
	send_button.text = "Working..."


func transfer_item(item: String, direction: String) -> void:
	if pending or item.is_empty() or not visible:
		return
	operation = "transfer"
	start_request()
	var error := request.request(backend_url + "/inventory/transfer", PackedStringArray(["Content-Type: application/json"]), HTTPClient.METHOD_POST, JSON.stringify({"npc_id": npc_id, "item": item, "direction": direction}))
	if error != OK:
		finish()
		append_dialogue("System", "Transfer could not be sent. Please retry.")


func clear_chat() -> void:
	if pending: return
	operation = "clear"
	start_request()
	var error := request.request(backend_url + "/chat/%s" % npc_id, PackedStringArray(), HTTPClient.METHOD_DELETE)
	if error != OK:
		finish()
		append_dialogue("System", "Could not clear chat. Please retry.")
