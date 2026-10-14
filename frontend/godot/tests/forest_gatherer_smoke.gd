# Drives real walking and interaction against the disposable port-8001 backend.
extends SceneTree

var scene
var failures := 0

func _initialize() -> void: call_deferred("run_check")

func check(ok: bool, label: String) -> void:
	print("PASS " if ok else "FAIL ",label)
	if not ok: failures += 1

func wait_for(condition: Callable) -> bool:
	var deadline := Time.get_ticks_msec() + 25000
	while not condition.call():
		await process_frame
		if Time.get_ticks_msec() > deadline:
			check(false,"Forest walk completes within deadline")
			quit(1)
			return false
	return true

func key(code: int, pressed: bool) -> void:
	var event := InputEventKey.new()
	event.keycode = code
	event.pressed = pressed
	Input.parse_input_event(event)
	Input.flush_buffered_events()

func run_check() -> void:
	scene = load("res://scenes/Main.tscn").instantiate()
	scene.backend_url = "http://127.0.0.1:8001"
	root.add_child(scene)
	if not await wait_for(func(): return scene.world_loaded and not scene._operations_pending()): return
	if not await preload("res://tests/opening_test_support.gd").arrive(scene): return
	scene._restart_game()
	if not await wait_for(func(): return scene.world_loaded): return
	if not await preload("res://tests/opening_test_support.gd").arrive(scene): return
	scene.player.position = Vector2(0,70)
	scene._update_current_npc()
	check(scene.current_npc == null,"Gatherer cannot be reached for conversation from village")
	key(KEY_A,true)
	if not await wait_for(func(): return scene.gatherer_encounter.phase == "choice"): return
	key(KEY_A,false)
	await physics_frame
	check(scene.gatherer_encounter.boars.size()==2,"Walking west triggers Gatherer encounter with two boars")
	scene.gatherer_encounter.decline()
	if not await wait_for(func(): return scene.gatherer_encounter.phase=="refusal"): return
	scene.gatherer_encounter.continue_scene()
	if not await wait_for(func(): return scene.gatherer_encounter.phase.is_empty()): return
	check(not scene.gatherer_encounter.bounds("ForestEntryRegion").has_point(scene.player.position),"Refusal automatically returns toward village")
	key(KEY_A,true)
	if not await wait_for(func(): return scene.gatherer_encounter.phase=="confrontation"): return
	key(KEY_A,false)
	check(scene.gatherer_encounter.boars.all(func(b): return b.health==0),"Return reveals two dead boars")
	scene.gatherer_encounter.continue_scene()
	scene.gatherer_encounter.continue_scene()
	if not await wait_for(func(): return scene.gatherer_encounter.phase.is_empty()): return
	scene._update_current_npc()
	check(scene.current_npc == scene.npc_nodes[2],"Resolving introduction unlocks Gatherer")
	if DisplayServer.get_name() != "headless":
		for i in range(6): await process_frame
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/npc-forest-gatherer.png")
	key(KEY_E,true)
	key(KEY_E,false)
	await process_frame
	check(scene.chat_windows[2].visible,"E opens Gatherer's conversation in forest")
	scene.chat_windows[2].close_chat()
	key(KEY_D,true)
	if not await wait_for(func(): return scene.player.position.x > -16): return
	key(KEY_D,false)
	scene._update_current_npc()
	check(scene.current_npc == null,"Walking back returns to village away from Gatherer")
	print("Forest Gatherer failures: ",failures)
	quit(1 if failures else 0)
