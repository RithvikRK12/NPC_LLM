extends SceneTree
var failures := 0
func check(ok: bool, message: String) -> void:
	if not ok:
		failures += 1
		push_error(message)
func _initialize() -> void: call_deferred("run")
func frames() -> void:
	for i in range(4): await process_frame
func run() -> void:
	var main = load("res://tests/fisherman_test_main.gd").new()
	root.add_child(main)
	main.world_loaded = true
	main.fisherman.state_path = "/tmp/fullscreen-rowan.cfg"
	DirAccess.remove_absolute(main.fisherman.state_path)
	main.fisherman.set_scope("fullscreen")
	main.fisherman.intro_seen = true
	main.player.position = Vector2(195,2290)
	for dimensions in [Vector2i(960,540),Vector2i(1920,1080),Vector2i(2560,1440),Vector2i(3840,2160),Vector2i(2560,1080)]:
		root.size = dimensions
		await frames()
		var physical: Vector2 = root.get_visible_rect().size
		check(main.ui.scale.x >= (1.5 if dimensions.y >= 1080 else 1.0), "UI grows on large displays: %s" % dimensions)
		check((main.ui.size * main.ui.scale).distance_to(physical) < 2, "Scaled UI fills window %s: logical %s, scale %s, actual %s" % [dimensions,main.ui.size,main.ui.scale,root.get_visible_rect().size])
		main.fisherman.open_dialogue()
		await frames()
		check(Rect2(Vector2.ZERO,physical).encloses(main.fisherman.panel.get_global_rect()), "Rowan panel fits display")
		if OS.get_environment("FISHERMAN_RENDER") == "1":
			await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png("/tmp/fullscreen-rowan-%s-%s.png" % [dimensions.x,dimensions.y])
		main.fisherman.close_dialogue()
		var chat = main.chat_windows[1]
		chat.show()
		chat.present("Craftsman","Bring me wood and string, and I can make you a bow.")
		await frames()
		check(Rect2(Vector2.ZERO,physical).encloses(chat.get_global_rect()), "AI dialogue fits scaled UI")
		chat.history_panel.show()
		await frames()
		check(Rect2(Vector2.ZERO,physical).encloses(chat.history_panel.get_global_rect()), "History stays above scaled dialogue")
		chat.close_chat()
		main._open_menu()
		await frames()
		check(Rect2(Vector2.ZERO,physical).encloses(main.menu_panel.get_global_rect()), "Menu fits scaled UI")
		if OS.get_environment("FISHERMAN_RENDER") == "1":
			await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png("/tmp/fullscreen-menu-%s-%s.png" % [dimensions.x,dimensions.y])
		main._resume_game()
	if OS.get_environment("FISHERMAN_RENDER") == "1":
		root.mode = Window.MODE_FULLSCREEN
		await frames()
		var physical: Vector2 = root.get_visible_rect().size
		check((main.ui.size*main.ui.scale).distance_to(physical)<2,"UI fits actual fullscreen viewport")
		check(main.ui.scale.x == load("res://scripts/ui_scaling.gd").factor(physical),"Actual fullscreen uses enlarged UI")
		main.fisherman.open_dialogue()
		await frames()
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/rowan-actual-fullscreen.png")
		main.fisherman.close_dialogue()
		root.mode = Window.MODE_WINDOWED
		await frames()
	root.size = Vector2i(1280,720)
	await frames()
	main.fisherman.set_scope("walk")
	main.player.position = Vector2(0,2400)
	await frames()
	check(main.fisherman.owns_input() and not main.fisherman.panel.visible, "Approach locks controls without opening dialogue")
	var initial: Vector2 = main.player.position
	for i in range(20): await physics_frame
	check(main.player.position.distance_to(initial) > 20, "Player automatically walks toward Rowan")
	check(not main.fisherman.panel.visible, "Dialogue waits for arrival")
	main._open_menu()
	var paused: Vector2 = main.player.position
	for i in range(8): await physics_frame
	check(main.player.position == paused, "Menu pauses automatic walking")
	main._resume_game()
	var deadline := Time.get_ticks_msec()+8000
	while not main.fisherman.panel.visible and Time.get_ticks_msec()<deadline: await physics_frame
	check(main.fisherman.panel.visible, "Walk and look-up finish in dialogue")
	check(main.player.position.distance_to(Vector2(250,2310)) < 6, "Player stops in front of log")
	check(main.village.layout.is_walkable(main.player.position), "Arrival does not overlap trunk")
	main.fisherman.close_dialogue()
	await frames()
	check(main.player.is_physics_processing(), "Dialogue close restores control")
	# Exercise routes from behind and both ends of the solid log, plus cancel.
	for start in [Vector2(250,2000),Vector2(0,2250),Vector2(500,2250),Vector2(400,2450)]:
		main.player.position = main.village.layout.recover_position(start)
		main.fisherman.introducing = true
		main.fisherman.begin_approach(main.player,main.village.layout)
		check(main.fisherman.approaching, "Route exists from %s" % start)
		for i in range(600):
			if not main.fisherman.approaching: break
			main.fisherman.advance_approach(main.player,1.0/60)
		check(main.player.position.distance_to(Vector2(250,2310)) < 6, "Walk routes around obstacles from %s" % start)
		main.fisherman.close_dialogue()
	main.player.position = Vector2(0,2400)
	main.fisherman.introducing = true
	main.fisherman.begin_approach(main.player,main.village.layout)
	var esc := InputEventKey.new()
	esc.keycode = KEY_ESCAPE; esc.pressed = true
	main._input(esc)
	await frames()
	check(not main.fisherman.approaching and main.player.is_physics_processing(), "Escape cancels automatic walking")
	DirAccess.remove_absolute(main.fisherman.state_path)
	main.queue_free()
	await frames()
	print("Fullscreen and Rowan walk: ",failures," failures")
	quit(1 if failures else 0)
