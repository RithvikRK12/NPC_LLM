extends SceneTree
var scene
var failures := 0
func _initialize(): call_deferred("run")
func check(ok: bool, label: String):
	print("PASS " if ok else "FAIL ",label)
	if not ok: failures+=1
func wait_for(condition: Callable) -> bool:
	var end=Time.get_ticks_msec()+18000
	while not condition.call():
		if DisplayServer.get_name()!="headless" and scene.menu_layer.visible: scene._resume_game()
		await process_frame
		if Time.get_ticks_msec()>end:
			check(false,"Approach timed out: "+scene.gatherer_encounter.phase+" "+str(scene.player.position)); quit(1); return false
	return true
func run():
	Engine.time_scale=3
	scene=load("res://scenes/Main.tscn").instantiate(); scene.backend_url="http://127.0.0.1:8001"; root.add_child(scene)
	if not await wait_for(func(): return scene.world_loaded): return
	if not await preload("res://tests/opening_test_support.gd").arrive(scene): return
	for entry in [["east",Vector2(-1370,70),Vector2(-1420,70)],["north",Vector2(-1800,-380),Vector2(-1800,-340)],["south",Vector2(-1800,430),Vector2(-1800,400)],["west",Vector2(-2270,70),Vector2(-2230,70)]]:
		if not await wait_for(func(): return not scene._operations_pending()): return
		scene._restart_game()
		if not await wait_for(func(): return scene.world_loaded): return
		if not await preload("res://tests/opening_test_support.gd").arrive(scene): return
		if not await wait_for(func(): return not scene._operations_pending()): return
		scene.fisherman.intro_seen=true; scene.player.position=entry[1]
		var router=load("res://scripts/actor_router.gd").new()
		check(router.set_target(scene.player.position,entry[2],scene.village.layout),"Clear "+entry[0]+" entrance")
		scene.player.set_control_enabled(false)
		var end=Time.get_ticks_msec()+5000
		while not scene.gatherer_encounter.owns_input() and Time.get_ticks_msec()<end:
			await physics_frame
			router.advance(scene.player,1.0/60*Engine.time_scale,180)
		if not await wait_for(func(): return scene.gatherer_encounter.phase=="choice"): return
		check(scene.player.position.distance_to(scene.gatherer_encounter.mark("PlayerTalkMark"))<1,"Collision-aware automatic approach from "+entry[0])
		if DisplayServer.get_name()!="headless":
			await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png("/tmp/gatherer-approach-"+entry[0]+".png")
		check(scene.gatherer_encounter.boars.all(func(b): return b.health==3 and not b.active),"Harmless visible threats from "+entry[0])
	scene.queue_free(); await process_frame
	print("Gatherer approach failures: ",failures)
	quit(1 if failures else 0)
