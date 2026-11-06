extends SceneTree
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var scene=load("res://tests/fisherman_test_main.gd").new(); root.add_child(scene)
	scene.world_loaded=true; scene.fisherman.intro_seen=true
	scene.craftsman_activity.intro_seen=true
	scene.player.position=Vector2(10000,10128)
	var points: Dictionary={}
	var last_capture := -1
	var deadline := Time.get_ticks_msec()+120000
	var start := Time.get_ticks_msec()
	DirAccess.make_dir_recursive_absolute("/tmp/craftsman-routine")
	while Time.get_ticks_msec()<deadline:
		await physics_frame
		var actor=scene.npc_nodes[1]
		if not scene.village.layout.is_walkable(actor.position):
			push_error("Routine left collision-clear ground"); quit(1); return
		if actor.velocity.length()<1: points[Vector2i(actor.position.round())]=true
		var elapsed := int((Time.get_ticks_msec()-start)/1000)
		if DisplayServer.get_name()!="headless" and elapsed/20>last_capture:
			last_capture=elapsed/20
			await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png("/tmp/craftsman-routine/workshop-%02d.png" % elapsed)
	if points.size()<3: push_error("Too few distinct workshop pauses"); quit(1); return
	print("Two-minute routine: ",points.size()," distinct idle positions, no nonwalkable positions")
	scene.queue_free(); await process_frame; quit()
