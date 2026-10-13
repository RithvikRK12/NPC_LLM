extends PanelContainer

signal world_changed(response: Dictionary)
signal overlay_opened(owner: Control)
var backend_url := "http://127.0.0.1:8000"
var npc_id := 0
var npc_name := "NPC"
# Kept as the full, labeled history presentation for saved transcript consumers.
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
var modal_blocked := false
var active_text: RichTextLabel
var speaker_label: Label
var portrait_texture: Texture2D
var portrait: Control
var continue_button: Button
var notice: Label
var history_panel: PanelContainer
var history_bubbles: VBoxContainer
var overlay_opener: Control
var supplies_panel: PanelContainer
var pages: Array[String] = []
var page_index := 0
var active_speaker := "System"
var active_message := ""
var failed_message := ""
var speaker_screen := Vector2.ZERO
var speaker_visible := false
var preferred_height := 268.0
var compact_overlay_theme: Theme
const Styles = preload("res://scripts/medieval_theme.gd")

func button(text: String, callback: Callable, parent: Node) -> Button:
	var control := Button.new()
	control.text = text
	control.pressed.connect(callback)
	parent.add_child(control)
	return control

func _ready() -> void:
	compact_overlay_theme = Styles.compact_overlay()
	set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	offset_left = 24
	offset_right = -24
	offset_top = -268
	offset_bottom = -24
	var layout := VBoxContainer.new()
	layout.add_theme_constant_override("separation", 8)
	add_child(layout)
	var heading := HBoxContainer.new()
	layout.add_child(heading)
	speaker_label = Label.new()
	speaker_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	speaker_label.add_theme_font_size_override("font_size", 30)
	heading.add_child(speaker_label)
	button("History", func(): toggle_overlay(history_panel), heading)
	button("Supplies", func(): toggle_overlay(supplies_panel), heading)
	button("Close", close_chat, heading)
	var body := HBoxContainer.new()
	body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_theme_constant_override("separation", 16)
	layout.add_child(body)
	portrait = Control.new()
	portrait.custom_minimum_size = Vector2(96, 96)
	portrait.draw.connect(_draw_portrait)
	body.add_child(portrait)
	active_text = RichTextLabel.new()
	active_text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	active_text.size_flags_vertical = Control.SIZE_EXPAND_FILL
	active_text.scroll_active = false
	body.add_child(active_text)
	active_text.resized.connect(func(): if not active_message.is_empty(): paginate())
	continue_button = button("Continue >", advance_page, body)
	notice = Label.new()
	notice.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	notice.add_theme_font_size_override("font_size", 21)
	layout.add_child(notice)
	var reply := HBoxContainer.new()
	layout.add_child(reply)
	message_input = LineEdit.new()
	message_input.placeholder_text = "Talk to " + npc_name + "..."
	message_input.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	message_input.custom_minimum_size.y = 40
	message_input.max_length = 500
	message_input.text_submitted.connect(func(_text: String): submit())
	reply.add_child(message_input)
	send_button = button("Send", submit, reply)
	history_panel = make_overlay("CONVERSATION HISTORY")
	dialogue_log = RichTextLabel.new()
	dialogue_log.size_flags_vertical = Control.SIZE_EXPAND_FILL
	dialogue_log.scroll_following = true
	dialogue_log.hide()
	history_panel.get_child(0).add_child(dialogue_log)
	var history_scroll := ScrollContainer.new()
	history_scroll.focus_mode = Control.FOCUS_ALL
	history_scroll.follow_focus = true
	history_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	history_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	history_panel.get_child(0).add_child(history_scroll)
	history_bubbles = VBoxContainer.new()
	history_bubbles.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	history_bubbles.add_theme_constant_override("separation", 8)
	history_scroll.add_child(history_bubbles)
	clear_button = button("Clear chat & memories", clear_chat, history_panel.get_child(0))
	clear_button.tooltip_text = "Clear only this NPC's saved conversation and dialogue memories. Items and quests stay unchanged."
	supplies_panel = make_overlay(npc_name.to_upper() + " • SUPPLIES")
	npc_inventory_label = Label.new()
	npc_inventory_label.text = "Select a supply to request"
	npc_inventory_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	supplies_panel.get_child(0).add_child(npc_inventory_label)
	var scroll := ScrollContainer.new()
	scroll.follow_focus = true
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	supplies_panel.get_child(0).add_child(scroll)
	item_grid = preload("res://scripts/item_grid.gd").new()
	scroll.add_child(item_grid)
	item_grid.item_selected.connect(func(_item: String): set_inventory(item_grid.items))
	take_button = button("Select a supply above", func(): transfer_item(item_grid.selected_item, "to_player"), supplies_panel.get_child(0))
	take_button.disabled = true
	take_button.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	request = HTTPRequest.new()
	request.timeout = 160
	add_child(request)
	request.request_completed.connect(_completed)
	resized.connect(func(): if not active_message.is_empty(): paginate())
	hide()

func make_overlay(title: String) -> PanelContainer:
	var panel := PanelContainer.new()
	get_parent().add_child(panel)
	panel.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE)
	panel.offset_top = -320
	panel.offset_bottom = -16
	var layout := VBoxContainer.new()
	panel.add_child(layout)
	var row := HBoxContainer.new()
	layout.add_child(row)
	var label := Label.new()
	label.text = title
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(label)
	button("Close", func(): panel.hide(); restore_overlay_focus(), row)
	panel.hide()
	return panel

func toggle_overlay(panel: Control) -> void:
	var was_visible := panel.visible
	overlay_opener = get_viewport().gui_get_focus_owner()
	close_overlays()
	if not was_visible:
		overlay_opened.emit(panel)
		panel.show()
		panel.get_child(0).get_child(0).get_child(1).grab_focus()

func restore_overlay_focus() -> void:
	if is_instance_valid(overlay_opener) and overlay_opener.is_visible_in_tree(): overlay_opener.grab_focus()
	else: message_input.grab_focus()

func close_overlays() -> void:
	history_panel.hide()
	supplies_panel.hide()

func open_chat() -> void:
	show()
	message_input.grab_focus()

func close_chat() -> void:
	message_input.release_focus()
	close_overlays()
	hide()

func set_inventory(items: Array) -> void:
	if item_grid.items != items: item_grid.populate(items)
	take_button.disabled = pending or item_grid.selected_item.is_empty()
	take_button.text = "Request " + item_grid.selected_item.capitalize() if not item_grid.selected_item.is_empty() else "Select a supply above"
	npc_inventory_label.text = npc_name + " • " + (item_grid.selected_item.capitalize() if not item_grid.selected_item.is_empty() else "Choose a supply")

func load_history(turns: Array) -> void:
	dialogue_log.clear()
	for child in history_bubbles.get_children():
		history_bubbles.remove_child(child)
		child.queue_free()
	active_message = ""
	notice.text = ""
	for turn in turns:
		append_dialogue("Player", str(turn.get("player", "")))
		append_dialogue(npc_name, str(turn.get("npc", "")))
	if turns.is_empty(): append_dialogue("System", "Your conversation with %s starts here." % npc_name)

func conversation_text() -> String:
	return dialogue_log.get_parsed_text()

func append_dialogue(speaker: String, text: String) -> void:
	dialogue_log.add_text(speaker + "\n" + text + "\n\n")
	var bubble := PanelContainer.new()
	bubble.add_theme_stylebox_override("panel", Styles.frame(Color("f4e6c5") if speaker == "Player" else Color("ddc797"), Color("a28356"), 2, 8))
	var label := Label.new()
	label.text = speaker + "\n" + text
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	bubble.add_child(label)
	history_bubbles.add_child(bubble)
	if speaker == "System":
		notice.text = "Notice: " + text
		if active_message.is_empty(): present(speaker, text)
	else:
		present(speaker, text)

func present(speaker: String, text: String) -> void:
	notice.text = ""
	active_speaker = speaker
	active_message = text
	speaker_label.text = speaker
	page_index = 0
	paginate()
	portrait.queue_redraw()
	queue_redraw()

func paginate() -> void:
	if active_text == null: return
	# Fit actual font-shaped lines to the available body, rather than character counts.
	var font := get_theme_default_font()
	var font_size := active_text.get_theme_font_size("normal_font_size")
	var width := maxf(160, size.x - 304)
	var height := maxf(44, active_text.size.y)
	var lines_per_page := maxi(1, int(height / (font.get_height(font_size) + 2)))
	# Use TextParagraph's break boundaries, including explicit newlines and Unicode.
	var paragraph := TextParagraph.new()
	paragraph.width = width
	paragraph.add_string(active_message, font, font_size)
	pages.clear()
	var line_count := paragraph.get_line_count()
	for first in range(0, line_count, lines_per_page):
		var start := paragraph.get_line_range(first).x
		var end := paragraph.get_line_range(mini(first + lines_per_page - 1, line_count - 1)).y
		pages.append(active_message.substr(start, end - start))
	if pages.is_empty(): pages.append(active_message)
	page_index = mini(page_index, pages.size() - 1)
	show_page()

func show_page() -> void:
	active_text.text = pages[page_index]
	continue_button.visible = pages.size() > 1
	continue_button.text = "%s/%s >" % [page_index + 1, pages.size()]
	continue_button.disabled = page_index == pages.size() - 1

func advance_page() -> void:
	if page_index + 1 < pages.size():
		page_index += 1
		show_page()

func _process(_delta: float) -> void:
	if not visible: return
	notice.visible = not notice.text.is_empty()
	# Larger fonts and notices can exceed the preferred box height. Grow upward
	# from the bottom margin so the reply and Send button remain on screen.
	offset_top = -maxf(preferred_height, get_combined_minimum_size().y + 24)
	item_grid.fit_columns(supplies_panel.size.x - 48)
	var compact: bool = get_parent().size.y < 640
	# The selected name is already present on Request and in each slot tooltip.
	npc_inventory_label.visible = not compact
	for panel in [history_panel, supplies_panel]:
		var overlay_theme: Theme = compact_overlay_theme if compact else null
		if panel.theme != overlay_theme: panel.theme = overlay_theme
		panel.offset_left = position.x + 16
		panel.offset_right = -position.x - 16
		panel.offset_top = maxf(16 if compact else 24, position.y - 320)
		panel.offset_bottom = position.y - (12 if compact else 16)
	queue_redraw()

func _draw() -> void:
	if active_speaker == "System" or not speaker_visible: return
	var x := clampf((get_global_transform().affine_inverse() * speaker_screen).x, 36, size.x - 36)
	draw_colored_polygon(PackedVector2Array([Vector2(x - 16, 3), Vector2(x, -18), Vector2(x + 16, 3)]), Color("70482c"))
	draw_colored_polygon(PackedVector2Array([Vector2(x - 10, 4), Vector2(x, -10), Vector2(x + 10, 4)]), Styles.PARCHMENT)

func _draw_portrait() -> void:
	if active_speaker == "System":
		portrait.draw_style_box(Styles.frame(Color("c4a675"),Color("70482c"),3,0),Rect2(0,0,96,96))
		portrait.draw_rect(Rect2(42,22,12,34),Styles.INK)
		portrait.draw_rect(Rect2(42,68,12,8),Styles.INK)
		return
	var identity := "player" if active_speaker == "Player" else ("craftsman" if npc_id==1 else "gatherer")
	portrait.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	portrait_texture = load("res://assets/portraits/%s.svg" % identity)
	portrait.draw_texture_rect(portrait_texture,Rect2(0,0,96,96),false)


func submit() -> void:
	if pending or not visible or modal_blocked:
		return
	var message := message_input.text.strip_edges()
	if message.is_empty():
		return
	operation = "chat"
	failed_message = message
	append_dialogue("Player", message)
	start_request()
	var error := request.request(backend_url + "/chat", PackedStringArray(["Content-Type: application/json"]), HTTPClient.METHOD_POST, JSON.stringify({"npc_id": npc_id, "player_message": message}))
	if error != OK:
		finish()
		append_dialogue("System", "Could not send: " + error_string(error))
	else:
		message_input.clear()


func finish() -> void:
	pending = false
	notice.text = ""
	send_button.disabled = false
	send_button.text = "Send"
	clear_button.disabled = false
	take_button.disabled = item_grid.selected_item.is_empty()


func _completed(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	finish()
	if result != HTTPRequest.RESULT_SUCCESS or code != 200:
		if operation == "chat" and message_input.text.is_empty(): message_input.text = failed_message
		append_dialogue("System", "Request failed (%s). Check the backend and try again." % code)
		return
	var parsed: Variant = JSON.parse_string(body.get_string_from_utf8())
	if not parsed is Dictionary:
		if operation == "chat" and message_input.text.is_empty(): message_input.text = failed_message
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
		if visible and not modal_blocked: message_input.grab_focus()
	else:
		message_input.placeholder_text = "Talk to " + npc_name + "..."
	set_inventory(response.get("npc", {}).get("inventory", []))
	world_changed.emit(response)


func start_request() -> void:
	pending = true
	send_button.disabled = true
	clear_button.disabled = true
	take_button.disabled = true
	send_button.text = "Waiting..."
	notice.text = "Waiting for " + npc_name + "..."


func transfer_item(item: String, direction: String) -> void:
	if pending or item.is_empty() or not visible or modal_blocked:
		return
	operation = "transfer"
	start_request()
	var error := request.request(backend_url + "/inventory/transfer", PackedStringArray(["Content-Type: application/json"]), HTTPClient.METHOD_POST, JSON.stringify({"npc_id": npc_id, "item": item, "direction": direction}))
	if error != OK:
		finish()
		append_dialogue("System", "Transfer could not be sent. Please retry.")


func clear_chat() -> void:
	if pending or modal_blocked: return
	operation = "clear"
	start_request()
	var error := request.request(backend_url + "/chat/%s" % npc_id, PackedStringArray(), HTTPClient.METHOD_DELETE)
	if error != OK:
		finish()
		append_dialogue("System", "Could not clear chat. Please retry.")
