# Disposable port-8001 world only. Run rendered to produce visual evidence.
extends SceneTree

var scene
var failures := 0
var evidence := "/tmp/willowbrook-ui"

func _initialize() -> void: call_deferred("run_check")

func check(ok: bool, label: String) -> void:
	print("PASS " if ok else "FAIL ", label)
	if not ok: failures += 1

func wait_for(condition: Callable) -> void:
	var deadline := Time.get_ticks_msec() + 20000
	while not condition.call():
		await process_frame
		if Time.get_ticks_msec() > deadline:
			push_error("UI check timed out")
			quit(1)
			return

func frames() -> void:
	for i in range(4): await process_frame

func snapshot(name: String) -> void:
	await frames()
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png(evidence.path_join(name + ".png"))

func escape() -> void:
	var event := InputEventKey.new()
	event.keycode = KEY_ESCAPE
	event.pressed = true
	Input.parse_input_event(event)

func run_check() -> void:
	root.size=Vector2i(1280,720)
	DirAccess.make_dir_recursive_absolute(evidence)
	scene = load("res://scenes/Main.tscn").instantiate()
	scene.backend_url = "http://127.0.0.1:8001"
	root.add_child(scene)
	await wait_for(func(): return scene.world_loaded and not scene._operations_pending())
	if not await preload("res://tests/opening_test_support.gd").arrive(scene): return
	scene._restart_game()
	await wait_for(func(): return scene.world_loaded)
	if not await preload("res://tests/opening_test_support.gd").arrive(scene): return
	check(scene.npc_nodes[2].position.x < -500, "Gatherer works deeper in the forest, away from village")
	check(scene.village.layout.route_exists(Vector2.ZERO, scene.npc_nodes[2].position + Vector2(0,64)), "Forest Gatherer remains reachable from village")
	await snapshot("exploration-1280")
	scene.player.position = Vector2(10064, 10032)
	scene._update_current_npc()
	scene._open_dialogue()
	var chat = scene.chat_windows[1]
	chat.present("Craftsman", "A good bow begins with sound wood and a sturdy string. Bring both to my workshop, and I will see what I can make for you.")
	chat.message_input.text = "My unsent reply: WASD"
	await snapshot("dialogue-1280")
	check(Rect2(Vector2.ZERO,scene.ui.size).encloses(chat.get_global_rect()), "Default dialogue panel fits viewport")
	check(chat.message_input.get_global_rect().end.y <= scene.ui.size.y, "Default reply remains fully visible")
	check(not scene.player.is_physics_processing(), "Dialogue blocks movement")
	escape()
	await frames()
	check(scene.menu_layer.visible and root.gui_get_focus_owner() == scene.resume_button, "Esc from focused reply opens menu and focuses Resume")
	await snapshot("menu-1280")
	var navigation := InputEventKey.new()
	navigation.keycode = KEY_DOWN
	navigation.pressed = true
	Input.parse_input_event(navigation)
	await frames()
	check(root.gui_get_focus_owner() == scene.restart_button, "Arrow navigation stays inside menu")
	escape()
	await frames()
	check(not scene.menu_layer.visible and chat.message_input.text == "My unsent reply: WASD" and root.gui_get_focus_owner() == chat.message_input, "Resume preserves unsent reply and focus")
	chat.message_input.text = "What materials do you need?"
	chat.submit()
	escape()
	await wait_for(func(): return not chat.pending)
	check(scene.menu_layer.visible and root.gui_get_focus_owner() == scene.resume_button, "Response while menu open preserves menu focus")
	escape()
	await frames()
	chat.toggle_overlay(chat.history_panel)
	await snapshot("history-1280")
	escape()
	await frames()
	check(scene.menu_layer.visible and chat.history_panel.visible, "Menu preserves history overlay")
	escape()
	await frames()
	chat.toggle_overlay(chat.supplies_panel)
	escape()
	await frames()
	check(scene.menu_layer.visible and chat.supplies_panel.visible, "Esc preserves supplies overlay")
	escape()
	await frames()
	chat.item_grid.select_item("rope")
	await snapshot("supplies-1280")
	check(chat.supplies_panel.visible and not chat.history_panel.visible, "Only one dialogue overlay opens")
	scene._toggle_bag()
	scene.player_grid.select_item("food")
	await snapshot("inventory-1280")
	escape()
	await frames()
	check(scene.menu_layer.visible and scene.inventory_drawer.visible, "Esc preserves satchel")
	escape()
	await frames()
	scene.player.position = Vector2(-650, 134)
	scene._update_current_npc()
	check(scene._give_recipient().npc_id == 1, "Conversation pins gift recipient despite nearby NPC change")
	chat.close_chat()
	scene.inventory_drawer.hide()
	scene.quest_panel.show()
	escape()
	await frames()
	check(scene.menu_layer.visible and scene.quest_panel.visible, "Esc preserves quest panel")
	escape()
	await frames()
	scene.quest_panel.hide()
	var test_grid = preload("res://scripts/item_grid.gd").new()
	scene.ui.add_child(test_grid)
	test_grid.populate(["wood", "wood", "an unknown item with a very long name"])
	test_grid.select_item("wood")
	test_grid.populate(["wood"])
	check(test_grid.selected_item == "wood", "Selection survives quantity refresh")
	test_grid.populate([])
	check(test_grid.selected_item.is_empty() and test_grid.get_child_count() == 16, "Empty inventory clears selection and retains decorative slots")
	test_grid.queue_free()
	chat.open_chat()
	chat.present("Craftsman", "Welcome to Willowbrook. " .repeat(80))
	await frames()
	check(chat.pages.size() > 1, "Long response paginates")
	check("".join(PackedStringArray(chat.pages)) == chat.active_message, "Pagination retains every character")
	chat.advance_page()
	check(chat.page_index == 1 and chat.active_text.text != "", "Continue advances locally")
	chat.close_chat()
	for dimensions in [Vector2i(960, 540), Vector2i(1920, 1080)]:
		root.content_scale_size = dimensions
		root.size = dimensions
		await frames()
		await snapshot("exploration-%s" % dimensions.x)
		chat.open_chat()
		chat.present("Craftsman", "The forest provides the wood. A string will bind it into a bow. Bring the materials to my workshop.")
		await snapshot("dialogue-%s" % dimensions.x)
		check(Rect2(Vector2.ZERO,scene.ui.size).encloses(chat.get_global_rect()), "Dialogue panel fits at %s" % dimensions.x)
		scene._toggle_bag()
		await snapshot("inventory-with-dialogue-%s" % dimensions.x)
		check(scene.inventory_drawer.get_global_rect().end.y < chat.message_input.global_position.y, "Inventory keeps reply visible at %s" % dimensions.x)
		check(scene.inventory_drawer.get_global_rect().end.y < chat.global_position.y, "Satchel gift action stays above dialogue at %s" % dimensions.x)
		scene.inventory_drawer.hide()
		chat.toggle_overlay(chat.history_panel)
		await snapshot("history-%s" % dimensions.x)
		chat.toggle_overlay(chat.supplies_panel)
		await snapshot("supplies-%s" % dimensions.x)
		check(Rect2(Vector2.ZERO,scene.ui.size).encloses(chat.supplies_panel.get_global_rect()), "Supplies remains inside viewport at %s" % dimensions.x)
		chat.close_chat()
		scene._toggle_bag()
		await snapshot("inventory-%s" % dimensions.x)
		scene.inventory_drawer.hide()
		scene._open_menu()
		await snapshot("menu-%s" % dimensions.x)
		check(Rect2(Vector2.ZERO,scene.ui.size).encloses(scene.menu_panel.get_global_rect()), "Menu panel fits at %s" % dimensions.x)
		scene.restart_button.pressed.emit()
		await snapshot("restart-%s" % dimensions.x)
		scene.restart_dialog.hide()
		scene.quitting = true
		scene._save_failed()
		await snapshot("save-error-%s" % dimensions.x)
		scene.back_button.pressed.emit()
		scene._resume_game()
		if dimensions.x == 960:
			scene._open_menu()
			var setting = scene.menu_panel.get_child(0).get_child(4)
			setting.button_pressed = true
			scene._resume_game()
			chat.open_chat()
			chat.present("Craftsman", "Larger text keeps your reply and actions visible. Apostrophes: I'm ready. Numbers: 1234567890. Arrows: → ←. Unicode: café, 你好.")
			await snapshot("dialogue-960-large")
			check(chat.message_input.get_global_rect().end.y <= dimensions.y, "Large-text reply fits compact viewport")
			chat.advance_page()
			await snapshot("dialogue-960-fallback")
			chat.toggle_overlay(chat.supplies_panel)
			await snapshot("supplies-960-large")
			var supply_scroll = chat.supplies_panel.get_child(0).get_child(2)
			check(supply_scroll.size.y >= 72, "Large-text supplies expose a full item row at compact size")
			check(chat.supplies_panel.get_global_rect().end.y < chat.global_position.y, "Large-text supplies stay above dialogue")
			chat.close_overlays()
			scene._toggle_bag()
			await snapshot("inventory-dialogue-960-large")
			check(scene.player_scroll.size.y >= 72, "Large-text satchel exposes a full item row at compact size")
			check(scene.inventory_drawer.get_global_rect().end.y < chat.global_position.y, "Large-text satchel stays above dialogue")
			scene.inventory_drawer.hide()
			chat.close_chat()
			scene._open_menu()
			await snapshot("menu-960-large")
			check(Rect2(Vector2.ZERO,scene.ui.size).encloses(scene.menu_panel.get_global_rect()), "Large-text menu fits compact viewport")
			scene.restart_button.pressed.emit()
			await snapshot("restart-960-large")
			escape()
			await frames()
			check(not scene.restart_dialog.visible and scene.menu_layer.visible, "Esc cancels restart confirmation before menu")
			scene._resume_game()
			setting.button_pressed = false
	root.content_scale_size = Vector2i(1280, 720)
	root.size = Vector2i(1280, 720)
	await frames()
	scene._open_menu()
	# Exercise the exact save completion failure path without changing backend state.
	scene.quitting = true
	scene._position_completed(HTTPRequest.RESULT_CANT_CONNECT, 0, PackedStringArray(), PackedByteArray())
	check(not scene.quitting and scene.menu_layer.visible and scene.retry_button.visible and scene.back_button.visible, "Save failure keeps application open with Retry and Back")
	await snapshot("save-error-1280")
	scene.back_button.pressed.emit()
	scene._resume_game()
	chat.open_chat()
	chat.message_input.text = "A retained failed message"
	chat.failed_message = chat.message_input.text
	chat.message_input.clear()
	chat.operation = "chat"
	chat._completed(HTTPRequest.RESULT_CANT_CONNECT, 0, PackedStringArray(), PackedByteArray())
	check(chat.message_input.text == "A retained failed message", "Failed chat retained for manual retry")
	await snapshot("chat-error-1280")
	chat.close_chat()
	var edge_items: Array = ["an unknown item with a very long name"]
	for i in range(1234): edge_items.append("wood")
	scene.player_grid.populate(edge_items)
	check(scene.player_grid.cards.size() == 2 and scene.player_grid.items.count("wood") == 1234, "Large stacks keep one slot per distinct item")
	scene._toggle_bag()
	scene.player_grid.select_item("an unknown item with a very long name")
	await snapshot("inventory-edge-cases-1280")
	check(scene.inventory_drawer.get_global_rect().end.x <= scene.ui.size.x, "Long unknown item details fit viewport")
	scene.inventory_drawer.hide()
	chat.open_chat()
	chat.clear_chat()
	await wait_for(func(): return not chat.pending)
	check(not chat.conversation_text().contains("What materials"), "Clear chat clears transcript")
	chat.transfer_item("water", "to_npc")
	chat.close_chat()
	var other = scene.chat_windows[2]
	other.open_chat()
	other.message_input.text = "Unsent to Gatherer"
	await wait_for(func(): return not chat.pending)
	check(not chat.visible and chat.conversation_text().contains("Thank you") and not other.conversation_text().contains("Thank you") and not scene.player_items.has("water"), "Gift response after closure updates correct NPC and world exactly once")
	check(other.message_input.text == "Unsent to Gatherer", "Late response preserves other NPC's reply")
	print("UI rework failures: ", failures)
	quit(1 if failures else 0)
