# Rendered verification against disposable backend only. Fails on broken transforms/pixels.
extends SceneTree
var scene
var failures := 0
var directory := "res://../../docs/evidence/graphics-overhaul/"
func _initialize() -> void: call_deferred("run_check")
func check(ok: bool,label: String) -> void:
	print("PASS " if ok else "FAIL ",label)
	if not ok: failures += 1
func settle() -> void:
	for i in range(6): await process_frame
	await RenderingServer.frame_post_draw
func capture(label: String) -> void:
	await settle()
	root.get_texture().get_image().save_png(ProjectSettings.globalize_path(directory+label+".png"))
func wait_for(condition: Callable) -> bool:
	var deadline := Time.get_ticks_msec()+20000
	while not condition.call():
		await process_frame
		if Time.get_ticks_msec()>deadline:
			check(false,"Backend response within deadline")
			quit(1)
			return false
	return true
func run_check() -> void:
	print("Native display scale: ",DisplayServer.screen_get_scale()," • render method: ",RenderingServer.get_current_rendering_method())
	scene=load("res://scenes/Main.tscn").instantiate()
	scene.backend_url="http://127.0.0.1:8001"
	root.add_child(scene)
	if not await wait_for(func(): return scene.world_loaded and not scene._operations_pending()): return
	scene.village.set_reduced_motion(true)
	for dimensions in [Vector2i(960,540),Vector2i(1280,720),Vector2i(1920,1080),Vector2i(1001,701)]:
		root.content_scale_size=dimensions
		root.size=dimensions
		for place in ["core","market"]:
			scene.player.position=Vector2.ZERO if place=="core" else Vector2(580,32)
			await capture("%s-%s" % [place,dimensions.x])
			var source: Image = scene.world_view.world_viewport.get_texture().get_image()
			var output: Image = root.get_texture().get_image()
			var k: int = scene.world_view.enlargement
			var margin: Vector2i = Vector2i(scene.world_view.presentation.position)
			if place=="core":
				var path_pixel := Vector2i(scene.world_view.world_to_screen(Vector2(50,0)))
				var path_color := output.get_pixelv(path_pixel)
				check(path_color.r > path_color.g,"Authored warm dirt path is visible above background")
			var exact := true
			# Sample only the unobscured central world, not the separate full-res HUD.
			for y in range(90,source.get_height()-50,17):
				for x in range(30,source.get_width()-30,19):
					var screen := Vector2(x*k+margin.x,y*k+margin.y)
					var over_label := false
					for npc in scene.npc_nodes.values():
						if npc.label.visible and npc.label.get_global_rect().grow(4).has_point(screen): over_label=true
					if over_label: continue
					var color := output.get_pixel(x*k+margin.x,y*k+margin.y)
					for dy in range(k):
						for dx in range(k):
							if output.get_pixel(x*k+dx+margin.x,y*k+dy+margin.y)!=color: exact=false
			check(exact,"Whole %sx%s source-pixel blocks: %s at %s" % [k,k,place,dimensions.x])
			check(scene.player.position==(Vector2.ZERO if place=="core" else Vector2(580,32)),"Rendering preserves simulation position")
		# Check dialogue projection at each size.
		scene.player.position=Vector2(10064,10032)
		scene._update_current_npc()
		scene._open_dialogue()
		var chat=scene.chat_windows[1]
		chat.present("Craftsman","Bring sound wood and string to my workshop. I can make a bow for you.")
		await capture("dialogue-%s" % dimensions.x)
		var portrait_pixel := Vector2i(chat.portrait.global_position+Vector2(12,12))
		check(root.get_texture().get_image().get_pixelv(portrait_pixel)!=Color.WHITE,"Portrait texture persists through draw submission")
		check(chat.speaker_visible and chat.speaker_screen.distance_to(scene.world_view.world_to_screen(scene.npc_nodes[1].position-Vector2(0,48)))<1,"Dialogue tail uses actual viewport transform at %s" % dimensions.x)
		chat.close_chat()
	root.content_scale_size=Vector2i(1280,720)
	root.size=Vector2i(1280,720)
	scene.village.set_reduced_motion(false)
	scene.player.position=Vector2(240,-80)
	await capture("atmosphere-1280")
	scene.village.set_reduced_motion(true)
	scene.player.position=Vector2(-350,10)
	await capture("forest-1280")
	scene.player.position=Vector2(580,32)
	scene.village.set_debug(true)
	await capture("market-debug-1280")
	scene.village.set_debug(false)
	# Actor behind then in front of the same tall tree (feet clear the trunk).
	for y in [-78,-28]:
		scene.player.position=Vector2(-370,y)
		await capture("overlap-%s" % ("behind" if y< -54 else "front"))
	# Drive real keyboard input and physics at slow speed; inspect presented foot pixels.
	scene.player.position=Vector2(10.25,50.75)
	var start: Vector2 = scene.player.position
	var original_speed: float = scene.player.speed
	scene.player.speed=12.0
	for code in [KEY_D,KEY_S]:
		var event := InputEventKey.new()
		event.keycode=code
		event.pressed=true
		Input.parse_input_event(event)
	var snapped := true
	var walking := false
	var fractional := false
	var observed_frames := {}
	for i in range(90):
		await physics_frame
		await process_frame
		await RenderingServer.frame_post_draw
		var person: Node2D = scene.player.get_child(0)
		var foot: Vector2 = scene.world_view.world_viewport.canvas_transform * (scene.player.position+person.position)
		if foot.distance_to(foot.round())>0.001: snapped=false
		walking = walking or person.sprite.animation=="walk_down"
		fractional = fractional or scene.player.position.distance_to(scene.player.position.round())>0.001
		observed_frames[person.sprite.frame]=true
		if i in [0,30,60,89]: await capture("slow-diagonal-%s" % i)
	for code in [KEY_D,KEY_S]:
		var event := InputEventKey.new()
		event.keycode=code
		event.pressed=false
		Input.parse_input_event(event)
	scene.player.speed=original_speed
	check(scene.player.position.x>start.x+2 and scene.player.position.y>start.y+2,"Keyboard-driven slow diagonal advances real physics")
	check(snapped and fractional,"Rendered feet remain on integer source pixels while physics stays fractional")
	check(walking and observed_frames.size()==4,"Slow movement exercises all four walk frames")
	# Normal-speed four-direction walking, then real doorway travel at the cottage.
	for direction in [[KEY_D,"right"],[KEY_W,"up"],[KEY_A,"left"],[KEY_S,"down"]]:
		var event := InputEventKey.new()
		event.keycode=direction[0]
		event.pressed=true
		Input.parse_input_event(event)
		for i in range(8):await physics_frame
		await process_frame
		check(scene.player.get_child(0).sprite.animation=="walk_"+direction[1],"Real directional walk: "+direction[1])
		event.pressed=false
		Input.parse_input_event(event)
	scene.player.position=Vector2(496,-56)
	var up := InputEventKey.new()
	up.keycode=KEY_W
	up.pressed=true
	Input.parse_input_event(up)
	for i in range(45):await physics_frame
	up.pressed=false
	Input.parse_input_event(up)
	check(scene.village.layout.interior_at(scene.player.position)=="cottage-a","Keyboard movement enters cottage through doorway")
	await capture("cottage-collision")
	print("Rendered graphics failures: ",failures)
	quit(1 if failures else 0)
