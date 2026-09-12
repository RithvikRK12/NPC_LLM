# Uses only the disposable port-8001 backend.
extends SceneTree

func _initialize() -> void: call_deferred("run_check")

func wait_for(condition: Callable) -> bool:
	var deadline := Time.get_ticks_msec() + 20000
	while not condition.call():
		await process_frame
		if Time.get_ticks_msec() > deadline:
			push_error("Persistence smoke timed out")
			quit(1)
			return false
	return true

func check(ok: bool, message: String) -> bool:
	if not ok:
		push_error(message)
		quit(1)
	return ok

func new_scene():
	var scene = load("res://scenes/Main.tscn").instantiate()
	scene.backend_url = "http://127.0.0.1:8001"
	root.add_child(scene)
	return scene

func run_check() -> void:
	var scene = new_scene()
	if not await wait_for(func(): return scene.world_loaded): return
	if not await wait_for(func(): return not scene._operations_pending()): return
	scene._restart_game()
	if not await wait_for(func(): return scene.world_loaded): return
	scene._quest_call("start")
	if not await wait_for(func(): return not scene.quest_busy): return
	scene.chat_windows[1].open_chat()
	scene.chat_windows[1].transfer_item("water", "to_npc")
	if not await wait_for(func(): return not scene.chat_windows[1].pending): return
	scene.player.position = Vector2(95, 105)
	scene._save_position()
	if not await wait_for(func(): return not scene.position_busy): return
	if not check(scene.last_saved_position == Vector2(95, 105), "Position must save"): return
	scene.queue_free()
	await process_frame
	await process_frame
	scene = new_scene()
	if not await wait_for(func(): return scene.world_loaded): return
	if not check(scene.player.position == Vector2(95, 105), "Launch must restore position"): return
	if not check(scene.bow_state.phase == "meet", "Launch must preserve quest"): return
	if not check(not scene.player_items.has("water"), "Launch must preserve inventory"): return
	if not check(scene.chat_windows[1].dialogue_log.get_parsed_text().contains("Thank you"), "Launch must restore chats"): return
	if not await wait_for(func(): return not scene._operations_pending()): return
	scene.restart_button.pressed.emit()
	if not check(scene.restart_dialog.visible, "Restart must show confirmation"): return
	scene.restart_dialog.hide()
	scene.restart_dialog.confirmed.emit()
	if not await wait_for(func(): return scene.world_loaded): return
	if not check(scene.player.position == Vector2.ZERO, "Restart must reset position"): return
	if not check(scene.bow_state.phase == "available", "Restart must reset quest"): return
	if not check(scene.player_items == ["water", "food"], "Restart must restore starter inventory"): return
	if not check(not scene.chat_windows[1].dialogue_log.get_parsed_text().contains("Thank you"), "Restart must clear chat"): return
	print("PASS persistence across launches and explicit restart")
	quit(0)
