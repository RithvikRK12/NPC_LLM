# Native full route traversal with collision and the established village anchors.
extends SceneTree
func _initialize() -> void: call_deferred("run")
func run() -> void:
	root.size=Vector2i(960,540) if OS.get_cmdline_user_args().has("--small") else Vector2i(1920,1080)
	var view=load("res://scripts/world_view.gd").new(); root.add_child(view)
	var island=load("res://scripts/island_world.gd").new(); view.world.add_child(island)
	var beach=load("res://scripts/shipwreck_beach.gd").new(); view.world.add_child(beach)
	var village=load("res://scripts/village.gd").new(); view.world.add_child(village)
	var player:=CharacterBody2D.new(); view.world.add_child(player)
	var person=load("res://scripts/person.gd").new(); player.add_child(person)
	var collision:=CollisionShape2D.new(); var shape:=RectangleShape2D.new(); shape.size=Vector2(24,16); collision.shape=shape; player.add_child(collision)
	var layer:=CanvasLayer.new(); root.add_child(layer)
	var label:=Label.new(); label.position=Vector2(16,16); layer.add_child(label)
	var route: Array=island.LAYOUT.data().routes[0]
	player.position=Vector2(route[0][0],route[0][1])
	view.follow(player.position); island.prepare_region(&"south")
	for i in range(6): await process_frame
	var frames:=0; var distance:=0.0; var blocked:=false; var peak_chunks:=0; var peak_props:=0
	var captured: Dictionary={}
	var started:=Time.get_ticks_usec(); var worst:=0
	for index in range(1,route.size()):
		var target:=Vector2(route[index][0],route[index][1])
		while player.position.distance_to(target)>.01:
			await process_frame
			var before:=Time.get_ticks_usec()
			var motion: Vector2=player.position.direction_to(target)*minf(6,player.position.distance_to(target))
			player.velocity=motion*30
			if player.move_and_collide(motion): blocked=true; break
			distance+=motion.length(); frames+=1
			island.view_half_extent=Vector2(view.world_viewport.size)
			island.update_active_chunks(player.position); view.follow(player.position)
			peak_chunks=maxi(peak_chunks,island.chunks.size())
			var props:=0
			for owner in island.dressing_chunks.values(): props+=owner.get_child_count()
			peak_props=maxi(peak_props,props)
			worst=maxi(worst,Time.get_ticks_usec()-before)
			label.text="BEACH → WILLOWBROOK · %.2f s · %.0f wu" % [distance/180,distance]
			for y in [3600,3200,2900,2250,1580,940,600,128,0]:
				if player.position.y<=y and not captured.has(y):
					captured[y]=true
					await RenderingServer.frame_post_draw
					root.get_texture().get_image().save_png(ProjectSettings.globalize_path("res://../../docs/evidence/starting-cutscene/second-pass/route-%s-%s.png" % [root.size.x,y]))
		if blocked: break
	for i in range(10): await process_frame
	print("PASS " if not blocked else "FAIL ","Native route: ",distance," wu / ",distance/180," s; frames=",frames," endpoint=",player.position," peak chunks=",peak_chunks," peak props=",peak_props," max update us=",worst," generation ms=",(Time.get_ticks_usec()-started)/1000)
	view.queue_free(); await process_frame; await process_frame
	quit(1 if blocked else 0)
