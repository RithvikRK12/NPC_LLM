extends SceneTree
var failures:=0
func check(ok: bool,label: String) -> void:
	print("PASS " if ok else "FAIL ",label)
	if not ok: failures+=1
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var world=load("res://scripts/island_world.gd").new(); root.add_child(world)
	var body:=CharacterBody2D.new(); var collider:=CollisionShape2D.new(); var shape:=RectangleShape2D.new(); shape.size=Vector2(24,16); collider.shape=shape; body.add_child(collider); root.add_child(body)
	await physics_frame; await physics_frame
	# Isolate global boundary sweeps from intentional trunk/rock obstacles.
	world.coast_body.collision_layer=2; body.collision_mask=2
	var layout=world.LAYOUT
	var missed:=0; var checked:=0; var blocked_seams:=0; var seams:=0
	for y in range(-160,160):
		for x in range(-224,224):
			var cell:=Vector2i(x,y)
			if not layout.land_cell(cell): continue
			var origin:=Vector2(cell*32)+Vector2(16,16)
			for d in [Vector2i.UP,Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT]:
				if not layout.land_cell(cell+d):
					for tangent in [-40,0,40]:
						var motion: Vector2=Vector2(d)*40+Vector2(d).orthogonal()*tangent
						if not body.test_move(Transform2D(0,origin),motion): missed+=1
						checked+=1
				elif (cell.x%32==0 and d.x!=0) or (cell.y%32==0 and d.y!=0):
					if body.test_move(Transform2D(0,origin),Vector2(d)*32): blocked_seams+=1
					seams+=1
	check(missed==0,"All %s straight/diagonal coast sweeps stop at water" % checked)
	check(blocked_seams==0,"All %s land chunk seam sweeps remain open" % seams)
	var coast_id: int=world.coast_body.get_instance_id()
	for at in [Vector2(0,3600),Vector2(-6000,0),Vector2(6000,0),Vector2(0,-4600),Vector2.ZERO]:
		world.update_active_chunks(at)
		check(world.chunks.has(layout.chunk_id_at(at)),"Player chunk loaded before movement at %s" % at)
		check(world.chunks.size()<=30,"Bounded active decorative chunks")
	check(coast_id==world.coast_body.get_instance_id(),"Coast collision survives every chunk unload")
	world.update_active_chunks(Vector2(10064,10032))
	check(not world.visible,"Logical interiors never render exterior land")
	world.queue_free(); body.queue_free(); await process_frame; await process_frame
	quit(1 if failures else 0)
