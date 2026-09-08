extends Node2D

const BACKEND_URL := "http://127.0.0.1:8000"

var player: CharacterBody2D
var npc_nodes: Dictionary = {}
var current_npc: Area2D
var dialogue_log: RichTextLabel
var message_input: LineEdit
var send_button: Button
var inventory_label: Label
var quest_label: Label
var prompt_label: Label
var interaction_label: Label
var http_request: HTTPRequest
var dialogue_panel: Control


func _ready() -> void:
	_build_world()
	_build_ui()
	_append_dialogue("System", "Walk up to an NPC and press E to open dialogue.")


func _process(_delta: float) -> void:
	_update_current_npc()
	if current_npc != null:
		interaction_label.text = "Press E to talk to %s" % current_npc.display_name
	else:
		interaction_label.text = "No NPC nearby"


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_E and current_npc != null:
			_open_dialogue()
		elif event.keycode == KEY_ESCAPE:
			_close_dialogue()


func _build_world() -> void:
	var ground := Polygon2D.new()
	ground.polygon = PackedVector2Array([
		Vector2(-640, -360),
		Vector2(640, -360),
		Vector2(640, 360),
		Vector2(-640, 360),
	])
	ground.color = Color(0.13, 0.18, 0.15)
	add_child(ground)

	player = preload("res://scripts/player.gd").new()
	player.position = Vector2(0, 0)
	add_child(player)
	_add_world_marker(player, Color(0.25, 0.70, 0.90), "Player")
	var camera := Camera2D.new()
	camera.zoom = Vector2(1.0, 1.0)
	camera.position_smoothing_enabled = true
	player.add_child(camera)
	camera.make_current()

	_add_npc(1, "Craftsman", "craftsman", Vector2(180, -20), Color(0.80, 0.55, 0.20), 0.65, 0.10, 0.05, 0.30)
	_add_npc(2, "Gatherer", "gatherer", Vector2(-170, 35), Color(0.28, 0.75, 0.35), 0.50, 0.25, 0.05, 0.70)


func _build_ui() -> void:
	var hud := CanvasLayer.new()
	add_child(hud)

	dialogue_panel = PanelContainer.new()
	dialogue_panel.position = Vector2(24, 24)
	dialogue_panel.custom_minimum_size = Vector2(430, 310)
	hud.add_child(dialogue_panel)

	var outer := VBoxContainer.new()
	dialogue_panel.add_child(outer)

	prompt_label = Label.new()
	prompt_label.text = "Closed-Loop NPC Demo"
	outer.add_child(prompt_label)

	interaction_label = Label.new()
	interaction_label.text = "No NPC nearby"
	outer.add_child(interaction_label)

	dialogue_log = RichTextLabel.new()
	dialogue_log.fit_content = true
	dialogue_log.scroll_active = true
	dialogue_log.custom_minimum_size = Vector2(390, 120)
	outer.add_child(dialogue_log)

	message_input = LineEdit.new()
	message_input.placeholder_text = "Type a message and press Send"
	message_input.visible = false
	outer.add_child(message_input)
	message_input.text_submitted.connect(_on_message_submitted)

	var buttons := HBoxContainer.new()
	outer.add_child(buttons)

	send_button = Button.new()
	send_button.text = "Send"
	send_button.disabled = true
	send_button.pressed.connect(_submit_message)
	buttons.add_child(send_button)

	var close_button := Button.new()
	close_button.text = "Close"
	close_button.pressed.connect(_close_dialogue)
	buttons.add_child(close_button)

	inventory_label = Label.new()
	inventory_label.text = "Inventory: []"
	outer.add_child(inventory_label)

	quest_label = Label.new()
	quest_label.text = "Quest: inactive"
	outer.add_child(quest_label)

	http_request = HTTPRequest.new()
	hud.add_child(http_request)
	http_request.request_completed.connect(_on_request_completed)


func _add_npc(npc_id: int, npc_name: String, role_name: String, position: Vector2, color: Color, trust: float, fear: float, aggression: float, curiosity: float) -> void:
	var npc := preload("res://scripts/npc.gd").new()
	npc.npc_id = npc_id
	npc.display_name = npc_name
	npc.role_name = role_name
	npc.position = position
	add_child(npc)

	var body := Polygon2D.new()
	body.polygon = PackedVector2Array([
		Vector2(-22, -22),
		Vector2(22, -22),
		Vector2(22, 22),
		Vector2(-22, 22),
	])
	body.color = color
	npc.add_child(body)

	var collider := CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = Vector2(44, 44)
	collider.shape = rect
	npc.add_child(collider)

	var name_label := Label.new()
	name_label.position = Vector2(-36, -54)
	npc.add_child(name_label)
	npc.label = name_label
	npc.refresh_label(trust, fear, aggression, curiosity)

	npc_nodes[npc_id] = npc


func _add_world_marker(target: Node2D, color: Color, text: String) -> void:
	var marker := Polygon2D.new()
	marker.polygon = PackedVector2Array([
		Vector2(-18, -18),
		Vector2(18, -18),
		Vector2(18, 18),
		Vector2(-18, 18),
	])
	marker.color = color
	target.add_child(marker)

	var label := Label.new()
	label.position = Vector2(-20, -48)
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


func _open_dialogue() -> void:
	if current_npc == null:
		return
	dialogue_panel.visible = true
	message_input.visible = true
	message_input.editable = true
	message_input.grab_focus()
	send_button.disabled = false
	_append_dialogue("System", "Talking to %s." % current_npc.display_name)


func _close_dialogue() -> void:
	message_input.visible = false
	message_input.text = ""
	send_button.disabled = true


func _on_message_submitted(_text: String) -> void:
	_submit_message()


func _submit_message() -> void:
	if current_npc == null:
		return
	var message := message_input.text.strip_edges()
	if message.is_empty():
		return
	_append_dialogue("Player", message)
	_send_chat_request(current_npc.npc_id, message)
	message_input.text = ""


func _send_chat_request(npc_id: int, message: String) -> void:
	var payload := {
		"npc_id": npc_id,
		"player_message": message,
	}
	var headers := PackedStringArray(["Content-Type: application/json"])
	http_request.request(BACKEND_URL + "/chat", headers, HTTPClient.METHOD_POST, JSON.stringify(payload))


func _on_request_completed(_result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if response_code < 200 or response_code >= 300:
		_append_dialogue("System", "Backend request failed: %s" % response_code)
		return

	var parsed := JSON.parse_string(body.get_string_from_utf8())
	if typeof(parsed) != TYPE_DICTIONARY:
		_append_dialogue("System", "Invalid JSON response")
		return

	var response := parsed as Dictionary
	var validated := response.get("validated_output", {}) as Dictionary
	var npc := response.get("npc", {}) as Dictionary

	_append_dialogue(npc.get("name", "NPC"), response.get("final_dialogue", ""))
	inventory_label.text = "Inventory: %s" % [str(response.get("player_inventory", []))]
	quest_label.text = "Quest: %s (%s)" % [str(response.get("quest_status", "unknown")), str(response.get("quest_progress", 0))]

	var npc_id := int(npc.get("id", 0))
	if npc_nodes.has(npc_id):
		var node := npc_nodes[npc_id] as Area2D
		node.apply_state(npc)
		node.refresh_label(float(npc.get("trust", 0.0)), float(npc.get("fear", 0.0)), float(npc.get("aggression", 0.0)), float(npc.get("curiosity", 0.0)))

	if validated.has("action"):
		_append_dialogue("System", "Action accepted: %s" % str(validated.get("action")))


func _append_dialogue(speaker: String, text: String) -> void:
	dialogue_log.append_text("[%s] %s\n" % [speaker, text])