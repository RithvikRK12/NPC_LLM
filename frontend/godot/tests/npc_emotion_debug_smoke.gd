extends SceneTree

var failures := 0

func check(ok: bool, description: String) -> void:
	if not ok:
		failures += 1
		push_error(description)

func _initialize() -> void:
	call_deferred("run_check")

func run_check() -> void:
	var ui := Control.new()
	ui.size = Vector2(1280, 720)
	root.add_child(ui)
	var chat = preload("res://scripts/chat_window.gd").new()
	chat.npc_id = 1
	chat.npc_name = "Craftsman"
	ui.add_child(chat)
	if not chat.has_method("set_emotional_state"):
		check(false, "Chat must support the hidden NPC emotion inspector")
		ui.queue_free()
		await process_frame
		quit(1)
		return
	var key := InputEventKey.new()
	key.keycode = KEY_F8
	key.physical_keycode = KEY_F8
	key.pressed = true
	chat._input(key)
	check(not chat.emotion_panel.visible, "F8 must do nothing outside a conversation")
	chat.set_emotional_state({"id": 1, "trust": 0.65, "fear": 0.1, "aggression": 0.05, "curiosity": 0.3})
	chat.open_chat()
	chat._input(key)
	check(chat.emotion_panel.visible, "F8 must open the inspector during chat")
	if not chat.emotion_values["trust"] is SpinBox:
		check(false, "Emotion values must be editable numeric fields")
		ui.queue_free()
		await process_frame
		quit(1)
		return
	check(is_equal_approx(chat.emotion_values["trust"].value, 0.65), "Inspector must show initial authoritative values")
	check(root.gui_get_focus_owner() == chat.message_input, "Opening the inspector must preserve reply typing focus")
	ui.theme = preload("res://scripts/medieval_theme.gd").create(true)
	ui.size = Vector2(960, 540)
	await process_frame
	await process_frame
	check(Rect2(Vector2.ZERO, ui.size).encloses(chat.emotion_panel.get_global_rect()), "Inspector must fit the minimum viewport with large text")
	check(not chat.emotion_panel.get_global_rect().intersects(chat.message_input.get_global_rect()), "Inspector must leave the reply field accessible")
	key.echo = true
	chat._input(key)
	check(chat.emotion_panel.visible, "Holding F8 must not repeatedly toggle the inspector")
	key.echo = false
	chat.game_scope = "emotion:test"
	chat.sent_game_scope = "emotion:test"
	chat._on_conversation_finalized("test", {
		"turn": {"key": {"epoch": 0}}, "final_dialogue": "Hello.",
		"npc": {"id": 1, "trust": 0.72, "fear": 0.08, "aggression": 0.04, "curiosity": 0.31}})
	check(is_equal_approx(chat.emotion_values["trust"].value, 0.72), "Every NPC reply must refresh the visible values")
	check(is_equal_approx(chat.emotion_values["fear"].value, 0.08), "All four emotional values must refresh")
	chat.set_emotional_state({"id": 2, "trust": 0.01})
	check(is_equal_approx(chat.emotion_values["trust"].value, 0.72), "Other NPCs must not overwrite this inspector")
	chat.emotion_values["trust"].get_line_edit().text = "0.830"
	var payload: Dictionary = chat._emotion_payload()
	check(is_equal_approx(payload.trust, 0.83) and payload.game_scope == "emotion:test", "Apply must capture typed values and the current save")
	chat.emotion_pending = true
	chat.emotion_scope = "emotion:test"
	chat._emotion_edit_completed(HTTPRequest.RESULT_SUCCESS, 200, PackedStringArray(), JSON.stringify({
		"id": 1, "trust": 0.83, "fear": 0.08, "aggression": 0.04, "curiosity": 0.31}).to_utf8_buffer())
	check(not chat.emotion_pending and is_equal_approx(chat.emotion_values["trust"].value, 0.83), "Successful Apply must show persisted values")
	chat.emotion_values["trust"].value = 0.9
	chat.emotion_pending = true
	chat._emotion_edit_completed(HTTPRequest.RESULT_CANT_CONNECT, 0, PackedStringArray(), PackedByteArray())
	check(not chat.emotion_pending and is_equal_approx(chat.emotion_values["trust"].value, 0.9), "Failed saves must preserve the draft and unlock editing")
	check(chat.emotion_status.text.begins_with("Could not save"), "Failed saves must report the error")
	chat._input(key)
	check(not chat.emotion_panel.visible, "F8 must toggle the inspector closed")
	chat.modal_blocked = true
	chat._input(key)
	check(not chat.emotion_panel.visible, "F8 must not open behind a modal menu")
	chat.modal_blocked = false
	chat._input(key)
	chat.close_chat()
	check(not chat.emotion_panel.visible, "Closing chat must close the inspector")
	chat._input(key)
	check(not chat.emotion_panel.visible, "F8 must stay inactive after closing chat")
	print("NPC emotion debug: ", "PASS" if failures == 0 else "FAIL")
	ui.queue_free()
	await process_frame
	quit(0 if failures == 0 else 1)
