# Integration regression for migration/pickup/interaction presentation. Disposable backend only.
extends SceneTree
var failures := 0
func _initialize() -> void: call_deferred("run_check")
func check(ok: bool,label: String) -> void:
	print("PASS " if ok else "FAIL ",label)
	if not ok: failures+=1
func wait_for(condition: Callable) -> bool:
	var deadline := Time.get_ticks_msec()+20000
	while not condition.call():
		await process_frame
		if Time.get_ticks_msec()>deadline:
			check(false,"State integration deadline")
			quit(1)
			return false
	return true
func new_scene():
	var scene = load("res://scenes/Main.tscn").instantiate()
	scene.backend_url="http://127.0.0.1:8001"
	root.add_child(scene)
	return scene
func run_check() -> void:
	var scene=new_scene()
	if not await wait_for(func(): return scene.world_loaded and not scene._operations_pending()): return
	if not await preload("res://tests/opening_test_support.gd").arrive(scene): return
	scene._restart_game()
	if not await wait_for(func(): return scene.world_loaded): return
	if not await preload("res://tests/opening_test_support.gd").arrive(scene): return
	scene._quest_call("start")
	if not await wait_for(func(): return not scene.quest_busy): return
	scene.chat_windows[1].open_chat()
	scene.chat_windows[1].transfer_item("water","to_npc")
	if not await wait_for(func(): return not scene.chat_windows[1].pending): return
	# Simulate an older save whose position predates the new cottage collision.
	scene.player.position=Vector2(496.25,-160.75)
	scene._save_position()
	if not await wait_for(func(): return not scene.position_busy): return
	scene.queue_free()
	await process_frame
	await process_frame
	scene=new_scene()
	if not await wait_for(func(): return scene.world_loaded and not scene.position_busy): return
	if not await preload("res://tests/opening_test_support.gd").arrive(scene): return
	check(scene.village.layout.is_walkable(scene.player.position) and scene.player.position!=Vector2(496.25,-160.75),"Old position inside new cottage recovers to clear ground")
	check(not scene.recovery_notice.is_empty(),"Recovery explained to player")
	check(scene.last_saved_position==scene.player.position,"Recovered position saved through existing save path")
	check(scene.bow_state.phase=="meet" and not scene.player_items.has("water") and scene.chat_windows[1].conversation_text().contains("Thank you"),"Recovery preserves quest, inventory and history")
	# Snapshot anchor rather than decorative layout is authoritative.
	scene._update_quest({"phase":"gather","string_available":true,"string_position":{"x":-72.5,"y":242.25}})
	check(scene.string_pickup.position==Vector2(-72.5,242.25),"Pickup consumes authoritative snapshot coordinates without rounding")
	scene._update_quest(scene.bow_state.merged({"string_position":{"x":-70,"y":240}},true))
	for distance in [95.5,96.5]:
		scene.player.position=scene.npc_nodes[1].position+Vector2(distance,0)
		scene._update_current_npc()
		check((scene.current_npc!=null)==(distance<96),"Talk radius remains 96 at %s" % distance)
	var float_position := Vector2(-1700.25,1400.75)
	scene.player.position=float_position
	scene._save_position()
	if not await wait_for(func(): return not scene.position_busy): return
	scene.queue_free()
	await process_frame
	await process_frame
	scene=new_scene()
	if not await wait_for(func(): return scene.world_loaded): return
	if not await preload("res://tests/opening_test_support.gd").arrive(scene): return
	check(scene.player.position==float_position,"Old save outside detailed district retains exact floating-point position")
	print("Graphics state failures: ",failures)
	quit(1 if failures else 0)
