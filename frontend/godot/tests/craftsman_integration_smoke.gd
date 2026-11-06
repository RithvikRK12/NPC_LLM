extends SceneTree
var scene
var failures := 0
var acceptance_message := "yes"
var check_post_inspection := false
var evidence := "/tmp/craftsman-evidence"
var lifecycle := OS.get_environment("CRAFTSMAN_RECOVERY_RUN")=="1"
func _initialize() -> void: call_deferred("run")
func check(ok: bool, message: String) -> bool:
	print("PASS " if ok else "FAIL ",message)
	if not ok: failures+=1
	return ok
func wait_for(condition: Callable, seconds: float=150) -> bool:
	var deadline := Time.get_ticks_msec()+int(seconds*1000)
	while not condition.call():
		await process_frame
		if Time.get_ticks_msec()>deadline:
			check(false,"Timed out: "+scene.craftsman_encounter.phase+" / "+scene.craftsman_activity.mode+" / "+str(scene.craftsman_activity.actor.position)+" reason="+scene.craftsman_activity.wait_reason+" player="+str(scene.player.position))
			finish(); return false
	return true
func capture(label: String) -> void:
	if DisplayServer.get_name()=="headless": return
	await process_frame; await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(evidence.path_join(label+".png"))
func say(message: String) -> bool:
	var chat=scene.chat_windows[1]
	chat.open_chat(); chat.message_input.text=message; chat.submit()
	if not await wait_for(func(): return not chat.pending): return false
	if message==acceptance_message:
		check(not chat.visible,"Accepted inspection automatically closes chat")
		check(scene.craftsman_objective.objective.visible,"Accepted inspection shows boat guidance")
	print("Talked: ",message)
	chat.close_chat(); return true
func walk(target: Vector2) -> bool:
	var router=load("res://scripts/actor_router.gd").new()
	if not router.set_target(scene.player.position,target,scene.village.layout):
		check(false,"Player route exists to "+str(target)); return false
	scene.player.set_control_enabled(false)
	var deadline := Time.get_ticks_msec()+15000
	while not router.path.is_empty():
		await physics_frame
		if router.advance(scene.player,1.0/60*Engine.time_scale,180)=="blocked" or Time.get_ticks_msec()>deadline:
			check(false,"Player physically reaches route target "+str(target)+" from "+str(scene.player.position)); return false
	scene.player.set_control_enabled(true)
	return true
func reload_checkpoint() -> bool:
	if not await wait_for(func(): return not scene._operations_pending()): return false
	scene.craftsman_gateway.save_checkpoint(scene.craftsman_activity.checkpoint())
	if not await wait_for(func(): return not scene.craftsman_gateway.busy): return false
	scene._save_position()
	if not await wait_for(func(): return not scene.position_busy): return false
	scene._load_world()
	var loaded: bool=await wait_for(func(): return not scene.world_busy)
	scene.fisherman.intro_seen=true # Keep the independent Rowan presentation excluded after reload too.
	return loaded
func finish() -> void:
	if is_instance_valid(scene): scene.queue_free()
	print("Craftsman integration: ",failures," failures")
	quit(1 if failures else 0)
func run() -> void:
	DirAccess.make_dir_recursive_absolute(evidence)
	Engine.time_scale=3
	scene=load("res://scenes/Main.tscn").instantiate(); scene.backend_url="http://127.0.0.1:8001"; root.add_child(scene)
	if not await wait_for(func(): return scene.world_loaded): return
	if not await preload("res://tests/opening_test_support.gd").arrive(scene): return
	if not await wait_for(func(): return not scene._operations_pending()): return
	scene._restart_game()
	if not await wait_for(func(): return scene.world_loaded): return
	if not await preload("res://tests/opening_test_support.gd").arrive(scene): return
	if not await wait_for(func(): return not scene._operations_pending()): return
	scene.fisherman.intro_seen=true # Rowan is covered by his own encounter regression.
	scene.player.position=scene.village.layout.exterior_spawn("workshop")
	scene._enter_building("workshop")
	if not await wait_for(func(): return scene.craftsman_encounter.phase=="intro_dialogue"): return
	check(scene.player.position.distance_to(scene.npc_nodes[1].position)<=96,"First entry walks into conversation range")
	await capture("01-introduction")
	if not await wait_for(func(): return not scene.craftsman_gateway.busy): return
	scene.craftsman_encounter.continue_button.pressed.emit()
	scene.craftsman_encounter.continue_button.pressed.emit()
	if not await wait_for(func(): return scene.craftsman_activity.intro_seen and scene.chat_windows[1].visible): return
	check(scene.bow_state.phase=="available","Introduction does not start bow quest")
	if not await say("Do you enjoy working here?"): return
	if not await say("The storm broke my ship."): return
	check(not scene.craftsman_activity.outing_active,"Report alone waits for agreement")
	if not await say(acceptance_message): return
	check(scene.craftsman_activity.outing_active,"Inspection acceptance starts outing")
	if not await say("Wait here"): return
	var stopped: Vector2=scene.npc_nodes[1].position
	for i in range(20): await physics_frame
	check(scene.npc_nodes[1].position==stopped,"Wait command holds a safe position")
	if not await say("Let's go"): return
	# Walk to the real exit; shared travel routes the Craftsman before fading.
	if not await walk(scene.village.layout.interior_origin("workshop")+Vector2(0,176)): finish(); return
	scene._travel_to(scene.village.layout.exterior_spawn("workshop"),"down")
	if not await wait_for(func(): return not scene.travelling): return
	check(scene.craftsman_activity.space=="exterior","Shared doorway moves both actors outside")
	await capture("02-shared-departure")
	# Detour through an unrelated cottage, then return to the exterior.
	var cottage: Vector2=scene.village.layout.exterior_spawn("cottage-a")
	if not await walk(cottage): finish(); return
	scene._enter_building("cottage-a")
	if not await wait_for(func(): return not scene.travelling): return
	if not await wait_for(func(): return scene.craftsman_activity.wait_reason=="interior"): return
	check(scene.craftsman_activity.space=="exterior","Craftsman waits outside unrelated cottage")
	scene._travel_to(cottage,"down")
	if not await wait_for(func(): return not scene.travelling): return
	if not await wait_for(func(): return scene.craftsman_activity.mode=="following_player"): return
	# Follow the authored inland corridor in bounded physical segments.
	for target in [Vector2(0,384),Vector2(0,704),Vector2(0,1024),Vector2(0,1344),Vector2(0,1664),Vector2(0,1984),Vector2(0,2304),Vector2(0,2624),Vector2(0,2944),Vector2(0,3264),Vector2(0,3504)]:
		print("Segment ",target," actor=",scene.npc_nodes[1].position," mode=",scene.craftsman_activity.mode," reason=",scene.craftsman_activity.wait_reason," clear=",scene.village.layout.is_walkable(scene.npc_nodes[1].position))
		if not await walk(target): finish(); return
		if lifecycle and target==Vector2(0,1664):
			if not await reload_checkpoint(): return
			check(scene.craftsman_activity.outing_active and scene.craftsman_activity.mode=="following_player","Reload during following resumes accepted outing")
	if not await wait_for(func(): return scene.craftsman_encounter.phase=="inspection_recognition"): return
	await capture("03-recognition")
	scene.craftsman_encounter.continue_scene()
	if not await wait_for(func(): return scene.craftsman_encounter.phase=="inspection_dialogue"): return
	await capture("04-inspection")
	check(scene.player.position.distance_to(Vector2(-32,3632))<2 and scene.npc_nodes[1].position.distance_to(Vector2(32,3632))<2,"Both actors stage outside hull")
	if not await wait_for(func(): return not scene.craftsman_gateway.busy): return
	if lifecycle:
		scene.craftsman_encounter.continue_scene()
		if not await reload_checkpoint(): return
		check(scene.craftsman_encounter.phase=="inspection_dialogue" and scene.craftsman_encounter.beat==2 and scene.craftsman_encounter.panel.visible,"Reload resumes the current visible inspection beat")
		scene.craftsman_encounter.skip()
	else:
		scene.craftsman_encounter.continue_scene(); scene.craftsman_encounter.continue_scene()
		await capture("05-requirements")
		scene.craftsman_encounter.continue_scene()
	if not await wait_for(func(): return scene.craftsman_encounter.phase=="farewell"): return
	check(scene.craftsman_gateway.state.inspection_complete,"Inspection result confirmed by server")
	check(scene.bow_state.phase=="available" and not scene.player_items.has("bow"),"Ship quest leaves bow and inventory independent")
	await capture("06-farewell")
	scene.craftsman_encounter.continue_scene()
	if check_post_inspection:
		if not await say("Thanks for looking at my ship!"): return
		var answer: String = scene.chat_windows[1].active_message.to_lower()
		print("Post-inspection answer: ",answer)
		check(not answer.contains("my ship") and not answer.contains("if you'd like"),"Thanks keeps NPC perspective and does not reopen inspection")
		check(scene.craftsman_activity.inspection_complete and not scene.craftsman_activity.outing_active,"Gratitude preserves completed inspection")
		scene.craftsman_objective.advance(scene.craftsman_objective.COMPLETION_END)
		check(not scene.craftsman_objective.objective.visible,"Gratitude does not replay escort guidance")
	scene.quest_panel.show(); await capture("07-main-quest"); scene.quest_panel.hide()
	var player_at: Vector2=scene.player.position
	if lifecycle:
		if not await say("Do you enjoy working here?"): return
		check(scene.craftsman_activity.mode=="returning_to_workshop","Conversation preserves return activity")
		if not await wait_for(func(): return scene.npc_nodes[1].position.y<3400): return
		if not await reload_checkpoint(): return
		check(scene.craftsman_activity.mode=="returning_to_workshop" and scene.craftsman_activity.inspection_complete,"Reload during solo return resumes committed journey")
	if not await wait_for(func(): return scene.craftsman_activity.mode=="workshop_routine",45): return
	check(scene.craftsman_activity.space=="workshop","Craftsman independently returns through workshop portal")
	check(scene.player.position==player_at,"Solo return leaves player at wreck")
	if not await wait_for(func(): return not scene._operations_pending()): return
	scene._load_world()
	if not await wait_for(func(): return not scene.world_busy): return
	check(scene.craftsman_activity.intro_seen and scene.craftsman_activity.inspection_complete,"Reload preserves introduction and inspection")
	check(scene.craftsman_activity.mode=="workshop_routine","Reload resumes routine after return")
	finish()
