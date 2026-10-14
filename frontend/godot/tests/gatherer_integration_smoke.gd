extends SceneTree
var scene
var failures := 0
var evidence := OS.get_environment("GATHERER_EVIDENCE") if not OS.get_environment("GATHERER_EVIDENCE").is_empty() else "/tmp/gatherer-evidence"
func _initialize(): call_deferred("run")
func check(ok: bool, text: String):
	print("PASS " if ok else "FAIL ",text)
	if not ok: failures+=1
func wait_for(condition: Callable, seconds: float=20) -> bool:
	var deadline=Time.get_ticks_msec()+int(seconds*1000)
	while not condition.call():
		# Render automation resumes OS focus pauses; explicit pause assertions use
		# their own timer and never pass through this helper.
		if DisplayServer.get_name()!="headless" and scene.menu_layer.visible: scene._resume_game()
		await process_frame
		if Time.get_ticks_msec()>deadline:
			check(false,"Timeout phase="+scene.gatherer_encounter.phase+" state="+scene.gatherer_encounter.status()+" at="+str(scene.player.position))
			finish(); return false
	return true
func capture(name: String):
	if DisplayServer.get_name()=="headless": return
	await process_frame; await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(evidence.path_join(name+".png"))
func key(code: int, pressed: bool):
	var event=InputEventKey.new(); event.keycode=code; event.physical_keycode=code; event.pressed=pressed
	Input.parse_input_event(event); Input.flush_buffered_events()
func new_run() -> bool:
	if not await wait_for(func(): return not scene._operations_pending()): return false
	scene._restart_game()
	if not await wait_for(func(): return scene.world_loaded): return false
	if not await preload("res://tests/opening_test_support.gd").arrive(scene): return false
	scene.fisherman.intro_seen=true
	return await wait_for(func(): return not scene._operations_pending())
func enter() -> bool:
	scene.player.position=scene.gatherer_encounter.mark("IntroCheckpoint")
	key(KEY_A,true)
	if not await wait_for(func(): return scene.gatherer_encounter.phase=="choice"): return false
	key(KEY_A,false)
	return true
func reload_scene() -> bool:
	if not await wait_for(func(): return not scene._operations_pending()): return false
	scene._save_position()
	if not await wait_for(func(): return not scene.position_busy): return false
	scene._load_world()
	return await wait_for(func(): return not scene.world_busy)
func help_to_combat() -> bool:
	scene.gatherer_encounter.help()
	if not await wait_for(func(): return scene.gatherer_encounter.phase=="tutorial"): return false
	check(scene.gatherer_encounter.combat.hearts==3,"Help gives three hearts")
	check(scene.gatherer_encounter.boars.all(func(b): return not b.active),"Tutorial has harmless boars")
	await capture("tutorial")
	scene.gatherer_encounter.continue_scene()
	return await wait_for(func(): return scene.gatherer_encounter.phase=="combat")
func finish():
	print("Gatherer integration failures: ",failures)
	if is_instance_valid(scene): scene.queue_free()
	quit(1 if failures else 0)
func run():
	DirAccess.make_dir_recursive_absolute(evidence)
	Engine.time_scale=2
	scene=load("res://scenes/Main.tscn").instantiate(); scene.backend_url="http://127.0.0.1:8001"; root.add_child(scene)
	if not await wait_for(func(): return scene.world_loaded): return
	if not await preload("res://tests/opening_test_support.gd").arrive(scene): return
	if not await new_run(): return
	# A legacy/missing snapshot is refreshed automatically without trapping input.
	scene.gatherer_gateway.state={}
	# Overlay delays entry; closing it while still inside reevaluates the trigger.
	scene.inventory_drawer.show(); scene.player.position=scene.gatherer_encounter.mark("IntroCheckpoint")+Vector2(-40,0)
	await create_timer(0.1).timeout
	check(scene.gatherer_encounter.phase.is_empty(),"Overlay defers forest cutscene")
	scene.inventory_drawer.hide()
	if not await wait_for(func(): return scene.gatherer_encounter.phase=="choice"): return
	check(scene.player.position.distance_to(scene.gatherer_encounter.mark("PlayerTalkMark"))<1,"First forest entry automatically walks to talk mark")
	check(scene.gatherer_encounter.choices.get_child_count()==2,"Explicit help and decline choices")
	check(not scene.gatherer_gateway.state.is_empty(),"Missing encounter data recovers automatically from updated backend")
	check(scene.gatherer_encounter.boars.all(func(b): return b.health==3 and not b.active),"Two living boars are harmless in choice")
	await capture("choice")
	var attempt=scene.gatherer_gateway.state.attempt_id
	key(KEY_ESCAPE,true); key(KEY_ESCAPE,false); await process_frame
	check(scene.menu_layer.visible and scene.gatherer_encounter.phase=="choice","Escape opens pause without choosing")
	scene._resume_game()
	if not await help_to_combat(): return
	await capture("combat")
	check(scene.gatherer_encounter.boars.all(func(b): return not scene.gatherer_encounter.hud.get_global_rect().has_point(scene.world_view.world_to_screen(b.position))),"Combat HUD leaves both boars visible")
	var encounter=scene.gatherer_encounter
	scene._open_menu(); var old_health=encounter.combat.hearts; var old_positions=[encounter.boars[0].position,encounter.boars[1].position]
	await create_timer(0.4).timeout
	check(encounter.combat.hearts==old_health and encounter.boars[0].position==old_positions[0] and encounter.boars[1].position==old_positions[1],"Pause freezes boars and damage")
	scene._resume_game()
	if not await wait_for(func(): return encounter.phase=="combat"): return
	if not await wait_for(func(): return encounter.boars.any(func(b): return b.state=="windup")): return
	await capture("warning")
	# Reload accepted combat reconstructs start and invalidates accepted attempt.
	if not await reload_scene(): return
	if not await wait_for(func(): return encounter.phase=="choice"): return
	check(scene.gatherer_gateway.state.attempt_id!=attempt and scene.gatherer_gateway.state.accepted_attempt_id=="","Reload resets combat attempt before choices")
	if not await help_to_combat(): return
	# Let actual warning/strike simulation defeat an idle player.
	if not await wait_for(func(): return encounter.phase=="defeat",15): return
	await capture("defeat")
	check(encounter.combat.hearts==0,"Three incoming hits cause defeat")
	attempt=scene.gatherer_gateway.state.attempt_id
	encounter.retry_encounter()
	if not await wait_for(func(): return encounter.phase=="choice"): return
	check(encounter.combat.hearts==3 and encounter.boars.all(func(b): return b.health==3),"Retry restores hearts and both boars")
	check(scene.gatherer_gateway.state.attempt_id!=attempt,"Retry invalidates old attempt")
	encounter.decline()
	if not await wait_for(func(): return encounter.phase=="refusal"): return
	check(encounter.status()=="declined_retreat_pending","Refusal is durable before walking away")
	if not await reload_scene(): return
	if not await wait_for(func(): return encounter.status()=="declined_return_pending" and encounter.phase.is_empty()): return
	check(scene.player.position.distance_to(scene.gatherer_encounter.mark("VillageReturnMark"))<1,"Decline walks outside forest")
	check(encounter.status()=="declined_return_pending","Return waits for new entry")
	await create_timer(0.2).timeout
	check(encounter.phase.is_empty(),"Remaining outside cannot confront twice")
	key(KEY_A,true)
	if not await wait_for(func(): return encounter.phase=="confrontation"): return
	key(KEY_A,false)
	check(encounter.boars.all(func(b): return b.health==0),"Next entry shows both dead boars")
	await capture("confrontation")
	if not await reload_scene(): return
	if not await wait_for(func(): return encounter.phase=="confrontation"): return
	check(encounter.boars.all(func(b): return b.health==0),"Reload resumes angry confrontation with corpses")
	encounter.continue_scene(); encounter.continue_scene()
	if not await wait_for(func(): return encounter.status()=="resolved_declined"): return
	scene._update_current_npc(); scene._open_dialogue()
	check(scene.chat_windows[2].visible,"Resolved refusal unlocks normal Gatherer chat")
	scene.chat_windows[2].close_chat()
	# Independent favorable branch: real J swings through combat.
	if not await new_run(): return
	if not await enter(): return
	if not await help_to_combat(): return
	var deadline=Time.get_ticks_msec()+20000
	var save_interrupted=false
	while encounter.phase=="combat" and Time.get_ticks_msec()<deadline:
		# Advance toward the nearest boar, face it, and issue fresh attacks.
		var target=encounter.boars[0] if encounter.boars[0].health>0 else encounter.boars[1]
		if encounter.boars[0].health==0 and target.health==1 and not save_interrupted:
			scene.gatherer_gateway.backend_url="http://127.0.0.1:8002"; save_interrupted=true
		var difference: Vector2=target.position-scene.player.position
		encounter.combat.facing=difference.normalized()
		if difference.length()>40:
			key(KEY_A,difference.x < -8); key(KEY_D,difference.x > 8)
			key(KEY_W,difference.y < -8); key(KEY_S,difference.y > 8)
		else:
			for code in [KEY_A,KEY_D,KEY_W,KEY_S]: key(code,false)
		key(KEY_J,true); await physics_frame; key(KEY_J,false)
		await create_timer(0.08).timeout
	for code in [KEY_A,KEY_D,KEY_W,KEY_S,KEY_J]: key(code,false)
	if save_interrupted:
		if not await wait_for(func(): return encounter.phase=="error"): return
		check(encounter.boars.all(func(b): return b.health==0) and not encounter.combat.enabled,"Failed victory save holds dead boars without damage")
		var retry_id=scene.gatherer_gateway.pending.request_id
		scene.gatherer_gateway.backend_url=scene.backend_url
		encounter.retry_save_or_route()
		check(scene.gatherer_gateway.pending.request_id==retry_id,"Retry reuses original outcome request ID")
	if not await wait_for(func(): return encounter.phase=="thanks"): return
	check(encounter.combat.hearts>0 and encounter.boars.all(func(b): return b.health==0),"Player can win using movement and J swings")
	await capture("thanks")
	if not await reload_scene(): return
	if not await wait_for(func(): return encounter.phase=="thanks"): return
	check(encounter.status()=="saved_thanks_pending","Reload resumes thanks without replaying combat")
	encounter.continue_scene(); encounter.continue_scene(); encounter.continue_scene()
	if not await wait_for(func(): return encounter.status()=="resolved_helped"): return
	check(not encounter.owns_input() and not encounter.hud.visible,"Success restores exploration and hides combat HUD")
	scene.player.position=scene.gatherer_encounter.mark("VillageReturnMark"); await physics_frame
	scene.player.position=scene.gatherer_encounter.mark("PlayerTalkMark"); await create_timer(0.2).timeout
	check(encounter.phase.is_empty(),"Resolved rescue does not replay on reentry")
	finish()
