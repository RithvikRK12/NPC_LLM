extends SceneTree
var failures:=0
func check(ok: bool,label: String) -> void:
	print("PASS " if ok else "FAIL ",label)
	if not ok: failures+=1
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var world=load("res://scripts/island_world.gd").new(); root.add_child(world)
	var beach=load("res://scripts/shipwreck_beach.gd").new(); root.add_child(beach)
	var actor:=CharacterBody2D.new(); var collider:=CollisionShape2D.new(); var shape:=RectangleShape2D.new(); shape.size=Vector2(24,16); collider.shape=shape; actor.add_child(collider); root.add_child(actor)
	var route: Array=world.LAYOUT.data().routes[0]
	var length:=0.0; var blocked:=0
	for i in range(route.size()-1):
		var a:=Vector2(route[i][0],route[i][1]); var b:=Vector2(route[i+1][0],route[i+1][1])
		length+=a.distance_to(b)
		var n:=ceili(a.distance_to(b)/16)
		for j in range(n):
			var p:=a.lerp(b,float(j)/n)
			world.update_active_chunks(p)
			await physics_frame
			if actor.test_move(Transform2D(0,p),(b-a)/n): blocked+=1
	check(blocked==0,"Full-footprint route crosses dressed chunks without collision")
	check(length/180>=18 and length/180<=22,"Direct route %.3f wu / %.3f s at unchanged 180 wu/s" % [length,length/180])
	check(world.get("dressing_chunks")!=null,"Persistent chunk dressing exists")
	if world.get("dressing_chunks")!=null:
		world.update_active_chunks(Vector2(0,3000))
		var id:=Vector2i(0,2)
		var before: Array=[]
		for prop in world.dressing_chunks[id].get_children(): before.append([prop.name,prop.position])
		world.update_active_chunks(Vector2(6000,-3000)); await process_frame
		world.update_active_chunks(Vector2(0,3000)); await physics_frame
		var after: Array=[]
		for prop in world.dressing_chunks[id].get_children(): after.append([prop.name,prop.position])
		check(before==after and not before.is_empty(),"Scenery identical after chunk unload/reload")
	world.queue_free(); beach.queue_free(); actor.queue_free(); await process_frame; await process_frame
	quit(1 if failures else 0)
