# Uses the disposable test backend on port 8001. Also runs rendered for screenshots.
extends SceneTree

var failures := 0
var scene
const EVIDENCE := "/tmp/willowbrook-interiors"

func _initialize() -> void: call_deferred("run_check")

func check(ok: bool, label: String) -> void:
	print("PASS " if ok else "FAIL ", label)
	if not ok: failures += 1

func wait_for(condition: Callable) -> bool:
	var deadline := Time.get_ticks_msec() + 15000
	while not condition.call():
		await process_frame
		if Time.get_ticks_msec() > deadline:
			check(false, "Interior operation completed within deadline")
			quit(1)
			return false
	return true

func new_scene() -> void:
	scene = load("res://scenes/Main.tscn").instantiate()
	scene.backend_url = "http://127.0.0.1:8001"
	root.add_child(scene)

func key(code: int, pressed: bool) -> void:
	var event := InputEventKey.new()
	event.keycode = code
	event.pressed = pressed
	Input.parse_input_event(event)

func capture(label: String) -> void:
	if DisplayServer.get_name() == "headless": return
	for i in range(6): await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(EVIDENCE.path_join(label + ".png"))

func run_check() -> void:
	var layout = load("res://resources/village_layout.tres")
	check(layout.has_method("interiors"), "Every village building has an authored interior")
	if failures:
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(EVIDENCE)
	new_scene()
	if not await wait_for(func(): return scene.world_loaded and not scene._operations_pending()): return
	if not await preload("res://tests/opening_test_support.gd").arrive(scene): return
	scene._restart_game()
	if not await wait_for(func(): return scene.world_loaded): return
	if not await preload("res://tests/opening_test_support.gd").arrive(scene): return
	var count := 0
	for entry in layout.objects():
		if entry.art not in ["workshop", "cottage-a", "cottage-b"]: continue
		count += 1
		var room: Dictionary = layout.interiors()[entry.id]
		var outside := Vector2(entry.at[0], entry.at[1] + 44)
		scene.player.position = outside
		# Menus must stop both walking and door activation.
		scene._open_menu()
		key(KEY_W, true)
		for i in range(12): await physics_frame
		key(KEY_W, false)
		check(scene.player.position == outside, "Menu blocks doorway travel: " + entry.id)
		scene._resume_game()
		key(KEY_W, true)
		if not await wait_for(func(): return not layout.interior_at(scene.player.position).is_empty()): return
		key(KEY_W, false)
		if not await wait_for(func(): return not scene.travelling): return
		check(layout.interior_at(scene.player.position) == entry.id, "Walking into correct interior: " + entry.id)
		check(layout.is_walkable(scene.player.position), "Arrival leaves feet clear of furniture: " + entry.id)
		await capture(entry.id)
		var origin := Vector2(room.origin[0], room.origin[1])
		# Real physics blocks walls and furniture, with player-sized foot clearance.
		scene.player.position = origin + Vector2(-280, 64)
		await physics_frame
		check(scene.player.move_and_collide(Vector2(-100, 0)) != null, "Interior wall blocks walking: " + entry.id)
		var prop: Dictionary = room.furniture[0]
		var f: Array = prop.footprint
		var furniture_at := origin + Vector2(prop.at[0], prop.at[1])
		scene.player.position = furniture_at + Vector2(f[0] + f[2]/2.0, f[1] + f[3] + 32)
		await physics_frame
		check(scene.player.move_and_collide(Vector2(0, -48)) != null, "Furniture has foot collision: " + entry.id)
		scene.player.position = origin + Vector2(0, 128)
		scene._update_current_npc()
		if entry.id == "workshop":
			check(layout.interior_at(scene.npc_nodes[1].position) == "workshop", "Craftsman lives inside workshop")
			scene.player.position = scene.npc_nodes[1].position + Vector2(0, 64)
			scene._update_current_npc()
			check(scene.current_npc == scene.npc_nodes[1], "Craftsman is reachable for talking and gifts")
			scene._open_dialogue()
			check(scene.chat_windows[1].visible, "E interaction opens workshop conversation")
			await capture("workshop-dialogue")
			scene.chat_windows[1].close_chat()
		else:
			check(scene.current_npc == null, "No NPC interaction leaks into cottages")
		# The existing save endpoint must restore the room without adding a second save.
		scene.player.position = origin + Vector2(0.25, 128.75)
		if not await wait_for(func(): return not scene.position_busy): return
		scene._save_position()
		if not await wait_for(func(): return not scene.position_busy): return
		scene.queue_free()
		await process_frame
		await process_frame
		new_scene()
		if not await wait_for(func(): return scene.world_loaded): return
		if not await preload("res://tests/opening_test_support.gd").arrive(scene): return
		check(scene.player.position == origin + Vector2(0.25, 128.75), "Save resumes exact interior position: " + entry.id)
		key(KEY_S, true)
		if not await wait_for(func(): return layout.interior_at(scene.player.position).is_empty()): return
		key(KEY_S, false)
		if not await wait_for(func(): return not scene.travelling): return
		check(scene.player.position.distance_to(outside) < 12, "Exit returns to matching outside doorway: " + entry.id)
		for i in range(20): await physics_frame
		check(layout.interior_at(scene.player.position).is_empty(), "Exit does not immediately re-enter: " + entry.id)
		scene._update_current_npc()
		check(scene.current_npc == null, "Cannot talk to craftsman through exterior walls")
	check(count == 3, "Workshop and both cottages can be entered and exited")
	await capture("village-doors")
	if not await wait_for(func(): return not scene._operations_pending()): return
	scene.player.position = Vector2(195,-53.5)
	var enter := InputEventKey.new()
	enter.keycode = KEY_E
	enter.pressed = true
	scene._unhandled_input(enter)
	check(scene.travelling, "E enters a building from its door apron")
	check(scene._operations_pending(), "Door fade prevents restart and shutdown races")
	if not await wait_for(func(): return not scene.travelling): return
	check(layout.interior_at(scene.player.position) == "workshop", "E arrives inside workshop")
	print("Building interior failures: ", failures)
	quit(1 if failures else 0)
