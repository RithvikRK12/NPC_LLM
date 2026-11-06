extends SceneTree
var failures := 0
func check(ok: bool, message: String) -> void:
	if not ok: failures += 1; push_error(message)
func _initialize() -> void: call_deferred("run")
func run() -> void:
	check(ResourceLoader.exists("res://scripts/actor_router.gd"), "Craftsman has a physical routing controller")
	if failures: quit(1); return
	var layout = load("res://resources/village_layout.tres")
	var router = load("res://scripts/actor_router.gd").new()
	var from := Vector2(10000,10128)
	var to := Vector2(10064,9952)
	var path: Array[Vector2] = router.find_path(from,to,layout)
	check(not path.is_empty(), "Workshop approach is reachable")
	var previous := from
	for point in path:
		check(router.clear_segment(previous,point,layout), "Every path segment clears furniture")
		previous = point
	check(router.find_path(from,Vector2(10064,9888),layout).is_empty(), "Furniture center is rejected")
	check(router.find_path(from,Vector2.ZERO,layout).is_empty(), "Routing cannot cross portal coordinate gaps")
	var npc = load("res://scripts/craftsman_actor.gd").new()
	check(npc is CharacterBody2D, "Craftsman is a physical character")
	root.add_child(npc)
	check(npc.collision_layer == 2 and npc.collision_mask == 1, "Actors overlap but collide with world")
	check(not router.clear_segment(Vector2(370,200),Vector2(370,240),layout),"Routes keep a numerical margin beside the fence corner")
	var portals=load("res://scripts/actor_portals.gd").new(layout)
	npc.position=layout.interior_origin("workshop")+Vector2(0,176)
	check(portals.traverse_actor(npc,"workshop",false),"NPC can exit workshop onto clear exterior ground")
	check(layout.interior_at(npc.position).is_empty(),"Portal actually crosses navigation space")
	npc.queue_free()
	print("Craftsman navigation: ", failures, " failures")
	quit(1 if failures else 0)
