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
	var script = load("res://scripts/onboarding.gd")
	if script == null:
		check(false,"First-control onboarding must exist")
		quit(1)
		return
	var main = load("res://tests/fisherman_test_main.gd").new()
	main.backend_url="http://127.0.0.1:1"
	root.add_child(main)
	main.world_loaded = true
	main.player.position = main.beach.marker("ControlHandoff")
	main.inventory_label.text = ""
	main.game_scope = "onboarding-test"
	main.onboarding.state_path = "/tmp/onboarding-smoke.cfg"
	DirAccess.remove_absolute(main.onboarding.state_path)
	main.onboarding.set_scope(main.game_scope)
	main.onboarding.begin()
	await frames()
	check(main.onboarding.modal.visible and main.ui_owns_input(),"First handoff shows modal and owns input")
	check(not main.player.is_physics_processing(),"Controls popup pauses movement")
	check(not main.onboarding.objective.visible,"Objective waits for dismissal")
	for dimensions in [Vector2i(960,540),Vector2i(1920,1080)]:
		root.size = dimensions
		await frames()
		check(Rect2(Vector2.ZERO,root.get_visible_rect().size).encloses(main.onboarding.card.get_global_rect()),"Controls card fits viewport")
		if OS.get_environment("ONBOARDING_RENDER") == "1":
			await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png("/tmp/controls-%s.png" % dimensions.x)
	main.onboarding.dismiss()
	await frames()
	check(not main.ui_owns_input() and main.player.is_physics_processing(),"Dismissal releases control")
	check(main.onboarding.objective.visible,"Dismissal reveals objective")
	check(main.onboarding.objective.position.y > 150,"Objective begins near center")
	if OS.get_environment("ONBOARDING_RENDER") == "1":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/objective-center.png")
	main._open_menu()
	var elapsed: float = main.onboarding.elapsed
	for i in range(12): await process_frame
	check(main.onboarding.elapsed == elapsed,"Menu pauses objective movement")
	main._resume_game()
	var deadline := Time.get_ticks_msec()+5000
	while main.onboarding.animating and Time.get_ticks_msec()<deadline: await process_frame
	check(not main.onboarding.animating,"Objective finishes transition")
	check(main.onboarding.objective.position.distance_to(Vector2(24,100))<1,"Objective docks upper-left below heading")
	check(main.onboarding.objective.scale.x < 0.8,"Docked objective is smaller")
	if OS.get_environment("ONBOARDING_RENDER") == "1":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/objective-docked.png")
	main.quest_panel.show()
	await frames()
	check(not main.onboarding.objective.visible,"Objective does not cover quest panel")
	main.quest_panel.hide()
	await frames()
	check(main.onboarding.objective.visible,"Objective returns after closing quest panel")
	main.onboarding.set_scope(main.game_scope)
	main.onboarding.begin()
	check(not main.onboarding.modal.visible and not main.onboarding.animating,"Same save resumes without replay")
	main.onboarding.set_scope("new-run")
	main.onboarding.begin()
	check(main.onboarding.modal.visible,"Fresh game gets controls again")
	main.onboarding.reset_presentation()
	check(not main.onboarding.modal.visible and not main.onboarding.objective.visible,"Restart clears presentation")
	var world := {"game_scope":"handoff-test","state_revisions":{"world":1},"opening_version":1,"map_version":2,"opening_capability":1,"opening_state":"pending","player_position":{"x":0,"y":0}}
	main.restart_in_flight=true # This fixture intentionally replaces the saved run.
	main._world_completed(HTTPRequest.RESULT_SUCCESS,200,PackedStringArray(),JSON.stringify(world).to_utf8_buffer())
	check(main.cinematic and not main.onboarding.modal.visible,"Controls remain hidden throughout cinematic")
	if main.opening == null:
		main.queue_free(); await process_frame; quit(1); return
	main.opening.fake = true
	main.opening.director.checkpoint_ready = true
	main.opening.director.advance_clock(60.0,false)
	await frames()
	check(not main.cinematic and main.onboarding.modal.visible,"Actual opening completion shows controls")
	check(not main.player.is_physics_processing(),"Actual handoff blocks movement until dismissal")
	main.onboarding.dismiss()
	world.opening_state = "complete"
	world.state_revisions.world = 2 # Changed world state requires a new server revision.
	main.world_loaded = false # A reload starts without a loaded world; refresh preserves active presentation.
	main.restart_in_flight=true # This fixture intentionally replaces the saved run.
	main._world_completed(HTTPRequest.RESULT_SUCCESS,200,PackedStringArray(),JSON.stringify(world).to_utf8_buffer())
	await frames()
	check(not main.onboarding.modal.visible and main.onboarding.objective.visible,"Completed saved run restores docked objective")
	check(main.onboarding.objective.position == Vector2(24,100),"Reload does not replay center animation: pos="+str(main.onboarding.objective.position)+" elapsed="+str(main.onboarding.elapsed)+" acknowledged="+str(main.onboarding.acknowledged)+" animating="+str(main.onboarding.animating))
	main.onboarding.set_scope("reduced-motion")
	main.onboarding.begin()
	main.onboarding.dismiss()
	main.onboarding.advance(1.7,true)
	check(not main.onboarding.animating and main.onboarding.objective.position == Vector2(24,100),"Reduced motion docks without travel")
	DirAccess.remove_absolute(main.onboarding.state_path)
	main.queue_free()
	await frames()
	print("Onboarding checks: ",failures," failures")
	quit(1 if failures else 0)
