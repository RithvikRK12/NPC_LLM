extends SceneTree
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var view=load("res://scripts/world_view.gd").new(); root.add_child(view)
	var before: float=Performance.get_monitor(Performance.MEMORY_STATIC)
	var island=load("res://scripts/island_world.gd").new(); view.world.add_child(island)
	var beach=load("res://scripts/shipwreck_beach.gd").new(); view.world.add_child(beach)
	for size in [Vector2i(960,540),Vector2i(1920,1080)]:
		root.size=size
		await process_frame
		for place in [["north",Vector2(0,-4800)],["east",Vector2(6600,0)],["south",Vector2(0,3820)],["west",Vector2(-6800,0)]]:
			island.view_half_extent=Vector2(view.world_viewport.size)
			island.update_active_chunks(place[1]); view.follow(place[1])
			for i in range(4): await process_frame
			await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png(ProjectSettings.globalize_path("res://../../docs/evidence/starting-cutscene/coast-%s-%s.png" % [place[0],size.x]))
			print("COAST ",place[0]," window=",size," chunks=",island.chunks.size()," static memory MiB=",(Performance.get_monitor(Performance.MEMORY_STATIC)-before)/1048576," terrain texture budget MiB=",island.chunks.size()*512*512*4/1048576)
	quit()
