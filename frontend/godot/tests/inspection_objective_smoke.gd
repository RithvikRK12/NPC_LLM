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
	main.onboarding.state_path = "/tmp/inspection-objective.cfg"
	main.fisherman.state_path = "/tmp/inspection-rowan.cfg"
	DirAccess.remove_absolute(main.onboarding.state_path)
	DirAccess.remove_absolute(main.fisherman.state_path)
	main.onboarding.set_scope("inspection")
	main.onboarding.begin(); main.onboarding.dismiss(); main.onboarding.advance(3.0)
	main.fisherman.set_scope("inspection")
	var e := InputEventKey.new()
	e.keycode = KEY_E; e.pressed = true
	main.player.position = main.beach.marker("HullExit")+Vector2(0,80)
	await frames()
	main._unhandled_input(e)
	check(main.ui_owns_input(),"Inspecting the hull opens a modal text box")
	if not "inspection" in main:
		main.queue_free(); await frames(); quit(1); return
	check(main.inspection.visible and main.inspection.title.text == "Broken hull","Hull has a titled inspection panel")
	check(main.inspection.message.text.contains("Splintered planks"),"Hull description uses popup text")
	await frames()
	check(not main.player.is_physics_processing(),"Inspection pauses movement")
	check(not main.help_label.visible and not main.interaction_label.visible,"Inspection hides background interaction hints")
	var esc := InputEventKey.new()
	esc.keycode = KEY_ESCAPE; esc.pressed = true
	main._input(esc)
	check(not main.inspection.visible and not main.menu_layer.visible,"Escape closes inspection directly")
	main.player.position = Vector2(150,1000)
	await frames()
	check(main.interaction_label.text.contains("Inspect"),"Sign offers inspection near its grounded post")
	main._unhandled_input(e)
	check(main.inspection.visible and main.inspection.message.text == "Willowbrook","Sign reads Willowbrook")
	for dimensions in [Vector2i(960,540),Vector2i(1920,1080)]:
		root.size = dimensions
		await frames()
		check(Rect2(Vector2.ZERO,root.get_visible_rect().size).encloses(main.inspection.get_global_rect()),"Inspection fits scaled display")
		if OS.get_environment("INSPECTION_RENDER") == "1":
			await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png("/tmp/sign-inspection-%s.png" % dimensions.x)
	main.inspection.close()
	await frames()
	check(main.player.is_physics_processing(),"Close releases movement")
	main.player.position = Vector2(0,2400)
	await frames()
	check(main.fisherman.introducing,"Rowan sequence starts")
	check(main.onboarding.completed and main.onboarding.completing,"Rowan starts objective check-mark animation")
	if OS.get_environment("INSPECTION_RENDER") == "1":
		main.onboarding.advance(0.35)
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/objective-checkmark.png")
	main.onboarding.advance(maxf(0,1.77-main.onboarding.completion_elapsed))
	check(main.onboarding.objective.modulate.a == 1.0,"Fully drawn check mark holds for 1.5 seconds before fading")
	main.onboarding.advance(0.02)
	check(main.onboarding.objective.modulate.a < 1.0,"Fade begins after check-mark hold")
	main.onboarding.advance(0.5)
	await frames()
	check(not main.onboarding.objective.visible,"Completed objective disappears permanently")
	main.onboarding.set_scope("inspection"); main.onboarding.begin()
	check(not main.onboarding.objective.visible,"Reload never restores completed objective")
	main.onboarding.set_scope("fresh-run"); main.onboarding.begin(); main.onboarding.dismiss()
	check(main.onboarding.objective.visible and not main.onboarding.completed,"Fresh run gets an incomplete objective")
	main.onboarding.complete_objective(false)
	check(not main.onboarding.objective.visible,"Legacy completed encounter hides objective without animation")
	DirAccess.remove_absolute(main.onboarding.state_path)
	DirAccess.remove_absolute(main.fisherman.state_path)
	main.queue_free(); await frames()
	print("Inspection and objective checks: ",failures," failures")
	quit(1 if failures else 0)
