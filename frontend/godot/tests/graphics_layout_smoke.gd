extends SceneTree
var failures := 0
func check(ok: bool, text: String) -> void:
	print("PASS " if ok else "FAIL ",text)
	if not ok: failures += 1
func _initialize() -> void: call_deferred("run_check")
func run_check() -> void:
	if not ResourceLoader.exists("res://scripts/world_view.gd") or not ResourceLoader.exists("res://resources/village_layout.tres"):
		check(false,"Integer world renderer and authored village layout exist")
		quit(1)
		return
	var view = load("res://scripts/world_view.gd").new()
	root.add_child(view)
	for size in [Vector2i(960,540),Vector2i(1280,720),Vector2i(1920,1080),Vector2i(1001,701)]:
		view.resize_world(size)
		check(view.enlargement == (3 if size.x==1920 else 2),"Integer enlargement at %s" % size)
		check(view.world_viewport.size * view.enlargement + Vector2i(view.remainder) == size,"Viewport covers window with only integer remainder at %s" % size)
		check(view.world_camera.zoom == Vector2(0.75,0.75),"World magnification is 1.5 times the previous framing at %s" % size)
	var layout = load("res://resources/village_layout.tres")
	var village = load("res://scripts/village.gd").new()
	view.world.add_child(village)
	await physics_frame
	village.set_reduced_motion(false)
	var ambient_count := 0
	var ambient_correct := true
	for prop in village.props:
		if prop.entry.ambient:
			ambient_count+=1
			prop.clock=0
			prop.last_phase=0
			prop._process(1.3)
			if prop.last_phase!=1: ambient_correct=false
	check(ambient_count>0 and ambient_correct,"Limited ambient props advance independently")
	village.set_reduced_motion(true)
	for prop in village.props:
		if prop.entry.ambient:
			prop._process(0)
			if prop.last_phase!=0: ambient_correct=false
			if prop.entry.get("smoke",false) and prop.sprite.visible: ambient_correct=false
	check(ambient_correct,"Reduced scenery motion freezes leaf/cloth frames and hides smoke")
	check(village.layout == layout,"Visuals and collisions share one layout")
	for p in [Vector2.ZERO,Vector2(110,-20),Vector2(-650,134),Vector2(-70,288),Vector2(496,-48),Vector2(720,-80),Vector2(480,20),Vector2(624,36)]:
		check(layout.is_walkable(p),"Clear approach at %s" % p)
		check(layout.route_exists(Vector2.ZERO,p),"Connected route to %s" % p)
	for entry in layout.objects():
		if entry.has("approach"):
			var approach := Vector2(entry.approach[0],entry.approach[1])
			check(layout.route_exists(Vector2.ZERO,approach),"Authored approach reachable: " + entry.id)
	for p in [Vector2(496,-160),Vector2(720,-190),Vector2(576,-30)]:
		var recovered: Vector2 = layout.recover_position(p)
		check(layout.is_walkable(recovered) and recovered != p,"Recover only trapped position %s" % p)
	for p in [Vector2(123.25,17.75),Vector2(-1700.25,1400.75)]:
		check(layout.recover_position(p)==p,"Preserve valid old floating-point position %s" % p)
	var routes := [village.PATH,[Vector2.ZERO,Vector2(-112,128),Vector2(-70,288)]]
	for route in routes:
		var clear := true
		for i in range(route.size()-1):
			var a: Vector2 = route[i]
			var b: Vector2 = route[i+1]
			var perpendicular := (b-a).normalized().orthogonal()
			for step in range(ceili(a.distance_to(b)/8)+1):
				var p := a.lerp(b,minf(1.0,step*8.0/a.distance_to(b)))
				for offset in [-24,0,24]:
					if not layout.is_walkable(p+perpendicular*offset): clear=false
		check(clear,"Continuous route plus foot clearance across path bends")
	check(layout.footprint("workshop")==Rect2(80,-222.5,230,125),"Original workshop collision retained exactly")
	var actor := CharacterBody2D.new()
	var collision := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = Vector2(24,16)
	collision.shape = shape
	actor.add_child(collision)
	view.world.add_child(actor)
	actor.position = Vector2(496,-56)
	await physics_frame
	var hit := actor.move_and_collide(Vector2(0,-80))
	check(hit != null and actor.position.y >= -88,"Cottage physically blocks feet before facade")
	actor.position = Vector2(110,-20)
	await physics_frame
	check(actor.move_and_collide(Vector2(-210,55))==null,"Quest route physically traversable")
	var person = load("res://scripts/person.gd").new()
	actor.add_child(person)
	for role in ["player","craftsman","gatherer"]:
		person.identity = role
		person.rebuild_frames()
		check(Array(person.sprite.sprite_frames.get_animation_names()).filter(func(animation): return String(animation).begins_with("idle_") or String(animation).begins_with("walk_")).size()==8,"Four idle/walk directions for %s" % role)
		check(person.sprite.position==Vector2(-24,-60) and person.sprite.scale==Vector2(2,2),"Stable (12,30) foot pivot for %s" % role)
	view.follow(Vector2(13.25,20.75))
	check(view.world_camera.position == Vector2(14,20),"Camera snaps presentation without modifying simulation")
	var point: Vector2 = view.world_to_screen(view.world_camera.position)
	check(point.distance_to(Vector2(view.world_viewport.size)*view.enlargement/2+view.presentation.position)<2,"Speaker projection uses viewport enlargement and margin")
	print("Graphics layout failures: ",failures)
	quit(1 if failures else 0)
