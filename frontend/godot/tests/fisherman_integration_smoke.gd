extends SceneTree
var failures := 0
func check(ok: bool, message: String) -> void:
	if not ok:
		failures += 1
		push_error(message)
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var main = load("res://tests/fisherman_test_main.gd").new()
	root.add_child(main)
	main.world_request.cancel_request()
	main.world_busy = false
	main.world_loaded = true
	main.fisherman.state_path = "/tmp/fisherman-integration.cfg"
	DirAccess.remove_absolute(main.fisherman.state_path)
	main.fisherman.set_scope("integration")
	main.player.position = Vector2(0,2400)
	await process_frame
	await process_frame
	check(main.fisherman.introducing and main.ui_owns_input(), "Approach automatically starts blocking introduction")
	main._open_menu()
	check(main.fisherman.panel.get_index() < main.menu_layer.get_index(), "Menu covers and blocks the static panel")
	var elapsed: float = main.fisherman.intro_elapsed
	await process_frame
	check(main.fisherman.intro_elapsed == elapsed, "Menu pauses introduction")
	main._resume_game()
	var deadline := Time.get_ticks_msec()+8000
	while main.fisherman.approaching and Time.get_ticks_msec()<deadline: await physics_frame
	check(not main.fisherman.approaching, "Automatic walk arrives before look-up")
	main.fisherman.advance_intro(2.0)
	await process_frame
	check(main.fisherman.panel.visible and not main.player.is_physics_processing(), "Dialogue blocks movement")
	var esc := InputEventKey.new()
	esc.keycode = KEY_ESCAPE; esc.pressed = true
	main._input(esc)
	check(not main.fisherman.owns_input() and not main.menu_layer.visible, "Escape closes Rowan directly")
	main.player.position = Vector2(195,2290)
	await process_frame
	main._open_dialogue()
	check(main.fisherman.panel.visible and main.fisherman.current_id == "F00", "E interaction opens Rowan without AI NPC selection")
	for choice in [0,0,0]: main.fisherman.choose(choice)
	main.fisherman.choices.get_child(0).pressed.emit()
	await process_frame; await process_frame
	check(not main.fisherman.panel.visible and main.player.is_physics_processing(), "Final Continue closes dialogue and restores movement")
	var interact := InputEventKey.new()
	interact.keycode = KEY_E; interact.pressed = true
	main._unhandled_input(interact)
	check(main.fisherman.panel.visible and main.fisherman.current_id == "F00", "E reopens Rowan after final Continue")
	check(main.world_view.world_camera.zoom == Vector2(0.75,0.75), "World camera uses required zoom")
	for size in [Vector2i(960,540),Vector2i(1280,720)]:
		root.size = size
		await process_frame
		await process_frame
		check(main.fisherman.panel.size.y <= size.y, "Dialogue fits viewport")
		if OS.get_environment("FISHERMAN_RENDER") == "1":
			await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png("/tmp/fisherman-%s.png" % size.x)
			main.fisherman.panel.hide()
			await process_frame
			await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png("/tmp/fisherman-seat-%s.png" % size.x)
			main.fisherman.panel.show()
	main.fisherman.close_dialogue()
	await process_frame
	await process_frame
	check(main.player.is_physics_processing(), "Close restores movement")
	DirAccess.remove_absolute(main.fisherman.state_path)
	main.queue_free()
	await process_frame
	print("Fisherman integration: ", failures, " failures")
	quit(1 if failures else 0)
