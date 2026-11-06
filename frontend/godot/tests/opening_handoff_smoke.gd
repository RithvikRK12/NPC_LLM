# Destructive: only the disposable port-8001 backend is used.
extends SceneTree
var failures:=0
var scene
func check(ok: bool,label: String) -> void:
	print("PASS " if ok else "FAIL ",label)
	if not ok: failures+=1
func wait_for(condition: Callable) -> bool:
	var end:=Time.get_ticks_msec()+15000
	while not condition.call():
		await process_frame
		if Time.get_ticks_msec()>end: check(false,"Response within deadline"); return false
	return true
func _initialize() -> void: call_deferred("run")
func run() -> void:
	root.size=Vector2i(1280,720)
	scene=load("res://scenes/Main.tscn").instantiate(); scene.backend_url="http://127.0.0.1:8001"; root.add_child(scene)
	if not await wait_for(func(): return scene.world_loaded): quit(1); return
	if not await wait_for(func(): return not scene._operations_pending()): quit(1); return
	scene._restart_game()
	if not await wait_for(func(): return scene.world_loaded and scene.cinematic): quit(1); return
	var opening=scene.opening
	opening.set_process(false)
	check(not opening.fake,"Real backend checkpoint adapter")
	# Intermittent acceleration, physics recovery and a deliberately delayed acknowledgment.
	for i in range(280):
		# This driver samples an offline mixed-rate timeline; desktop focus is tested separately.
		if not opening.director.focused: opening.director.set_focused(true)
		opening.director.set_paused(false); opening.director.advance_clock(0,false)
		var held: bool=i%120<60
		var rate:=2.0 if held else 1.0
		opening.director.advance_clock(minf(0.25,(59.8-opening.director.time)/rate),held)
		await physics_frame
		if opening.director.time>=59.8: break
	if not await wait_for(func(): return not opening.busy): quit(1); return
	print("CHECKPOINT time=",opening.director.time," focused=",opening.director.focused," paused=",opening.director.paused," error=",opening.checkpoint_error)
	check(opening.director.checkpoint_ready,"Durable checkpoint acknowledged")
	if not opening.director.checkpoint_ready: scene.queue_free(); await process_frame; quit(1); return
	var surf_id: int=opening.audio.ambience.get_instance_id()
	opening.director.advance_clock(0.2,false)
	await physics_frame; await process_frame
	check(not scene.cinematic and scene.player.position==scene.beach.marker("ControlHandoff"),"Final step releases control at exact shared marker")
	check(scene.player.velocity==Vector2.ZERO,"No residual cinematic velocity")
	check(not scene.travel_fade.visible and scene.travel_fade.color.a==0,"Fade releases gameplay")
	check(scene.world_view.world_camera.position==scene.player.position,"Single camera aligns at handoff")
	check(not scene.player.get_child(0).scripted_mode,"Animation returns to gameplay")
	check(scene.onboarding.owns_input() and scene.onboarding.modal.visible,"Handoff opens controls popup")
	check(not scene.player.is_physics_processing(),"Controls popup pauses player movement")
	scene.onboarding.dismiss()
	scene.onboarding.advance(3.0)
	await process_frame; await process_frame
	check(not scene.ui_owns_input(),"Dismissing controls releases gameplay")
	check(scene.player.is_physics_processing(),"Normal player physics restored")
	print("SURF playing=",scene.beach.ambience.playing," paused=",scene.beach.ambience.stream_paused," same voice=",scene.beach.ambience.get_instance_id()==surf_id," released=",opening.audio.ambience==null," loop end=",scene.beach.ambience.stream.loop_end)
	check(scene.beach.ambience.playing and opening.audio.ambience==null and scene.beach.ambience.get_instance_id()==surf_id,"Playing surf ownership transfers to persistent beach")
	check(scene.bag_button.is_visible_in_tree() and not scene.inventory_drawer.visible,"HUD appears without automatic panels")
	if DisplayServer.get_name()!="headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png(ProjectSettings.globalize_path("res://../../docs/evidence/starting-cutscene/gameplay-handoff.png"))
	scene.player.position=scene.beach.marker("SupplyApproach")
	scene._collect_salvage()
	if not await wait_for(func(): return not scene.salvage_busy): quit(1); return
	check(scene.player_items.count("rope")==1,"Salvage adds exactly one rope")
	scene.player.position=Vector2(0,3440.125); scene._save_position()
	if not await wait_for(func(): return not scene.position_busy): quit(1); return
	scene.queue_free(); await process_frame; await process_frame
	scene=load("res://scenes/Main.tscn").instantiate(); scene.backend_url="http://127.0.0.1:8001"; root.add_child(scene)
	if not await wait_for(func(): return scene.world_loaded): quit(1); return
	check(not scene.cinematic and scene.player.position==Vector2(0,3440.125),"Completed run resumes exact float position")
	await process_frame; await process_frame
	check(scene.beach.ambience.playing,"Completed beach reload resumes persistent ambience")
	check(not scene.beach.salvage_available and scene.player_items.count("rope")==1,"Pickup persists across reload")
	scene.queue_free(); await process_frame; await process_frame
	quit(1 if failures else 0)
