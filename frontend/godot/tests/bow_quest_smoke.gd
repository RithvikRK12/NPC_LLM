# Run with a fresh test backend on port 8001; never uses the player's port-8000 save.
extends SceneTree

func _initialize() -> void: call_deferred("run_check")

func wait_for(condition: Callable) -> bool:
	var deadline := Time.get_ticks_msec() + 20000
	while not condition.call():
		await process_frame
		if Time.get_ticks_msec() > deadline:
			push_error("Timed out in bow quest smoke test")
			quit(1)
			return false
	return true

func check(ok: bool, label: String) -> bool:
	if not ok:
		push_error(label)
		quit(1)
	return ok

func run_check() -> void:
	var scene = load("res://scenes/Main.tscn").instantiate()
	scene.backend_url = "http://127.0.0.1:8001"
	root.add_child(scene)
	if not await wait_for(func(): return scene.world_loaded): return
	if not check(scene.bow_state.phase == "available" and not scene.quest_panel.visible, "Must begin in free roam"): return
	scene.quest_panel.show()
	scene.quest_panel.start_button.pressed.emit()
	if not await wait_for(func(): return not scene.quest_busy): return
	scene.player.position = Vector2(110, -20)
	scene._update_current_npc()
	scene._open_dialogue()
	var craftsman = scene.chat_windows[1]
	craftsman.message_input.text = "Can you make me a bow?"
	craftsman.submit()
	if not await wait_for(func(): return not craftsman.pending): return
	if not check(scene.bow_state.phase == "gather" and scene.string_pickup.visible, "Craftsman must request materials"): return
	scene.player.position = Vector2(-100, 35)
	scene._update_current_npc()
	scene._open_dialogue()
	var gatherer = scene.chat_windows[2]
	gatherer.item_grid.select_item("wood")
	gatherer.take_button.pressed.emit()
	if not await wait_for(func(): return not gatherer.pending): return
	if not check(not scene.player_items.has("wood"), "Wood needs a reason before transfer"): return
	gatherer.message_input.text = "To help the Craftsman make a bow"
	gatherer.submit()
	if not await wait_for(func(): return not gatherer.pending): return
	gatherer.close_chat()
	scene.player.position = Vector2(-70, 240)
	var pickup := InputEventKey.new()
	pickup.keycode = KEY_F
	pickup.pressed = true
	scene._unhandled_input(pickup)
	if not await wait_for(func(): return not scene.quest_busy): return
	if not check(scene.player_items.has("wood") and scene.player_items.has("string") and not scene.string_pickup.visible, "Materials must be real inventory items"): return
	scene.player.position = Vector2(110, -20)
	scene._update_current_npc()
	for item in ["wood", "string"]:
		scene.player_grid.select_item(item)
		scene._give_selected_item()
		if not await wait_for(func(): return not craftsman.pending): return
	if not check(scene.bow_state.phase == "crafting" and not scene.player_items.has("bow"), "Bow must not be granted instantly"): return
	if not await wait_for(func(): return scene.quest_panel.progress.value > 10): return
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("/tmp/npc-bow-crafting.png")
	if not await wait_for(func(): return scene.bow_state.phase == "completed"): return
	if not check(scene.player_items.count("bow") == 1, "Quest must award exactly one bow"): return
	scene.inventory_drawer.show()
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("/tmp/npc-bow-completed.png")
	print("PASS: free roam → quest → material dialogue → confirmed wood → F pickup → gifts → timed progress → one bow")
	quit()
