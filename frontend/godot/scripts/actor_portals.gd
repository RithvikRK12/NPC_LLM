extends RefCounted
var layout: Resource
func _init(world_layout: Resource) -> void: layout=world_layout
func traverse_actor(actor: Node2D, portal_id: String, entering: bool) -> bool:
	if not layout.interiors().has(portal_id): return false
	var outside: Vector2=layout.exterior_spawn(portal_id)
	var origin: Vector2=layout.interior_origin(portal_id)
	var source: Vector2=outside if entering else origin+Vector2(0,176)
	var at: Vector2=origin+Vector2(48,128) if entering else outside+Vector2(-40,16)
	if actor.position.distance_to(source)>64 or not layout.is_walkable(at): return false
	actor.position=at
	if actor is CharacterBody2D: actor.velocity=Vector2.ZERO
	return true
