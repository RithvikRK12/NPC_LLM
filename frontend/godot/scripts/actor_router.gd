extends RefCounted
# Static geometry cache belongs to this router, not to durable saves.
var path: Array[Vector2] = []
var cache: Dictionary = {}
var stalled := 0.0
var last_position := Vector2.INF
func point_clear(at: Vector2, layout: Resource) -> bool:
	if cache.size()>32768: cache.clear()
	if not cache.has(at):
		var clear := true
		# WorldLayout already includes the foot box; this 2-unit tolerance only
		# prevents sampled corner grazing and physics safe-margin drift.
		for offset in [Vector2.ZERO,Vector2(-2,-2),Vector2(2,-2),Vector2(-2,2),Vector2(2,2)]:
			if not layout.is_walkable(at+offset): clear=false; break
		cache[at]=clear
	return cache[at]
func clear_segment(from: Vector2, to: Vector2, layout: Resource) -> bool:
	var steps := maxi(1,ceili(from.distance_to(to)/4.0))
	for i in range(steps+1):
		if not point_clear(from.lerp(to,float(i)/steps),layout): return false
	return true
func nearest(at: Vector2, grid: AStarGrid2D, layout: Resource) -> Vector2i:
	var center := Vector2i((at/16).round())
	var best := Vector2i.MAX
	var distance := INF
	for y in range(-2,3):
		for x in range(-2,3):
			var id := center+Vector2i(x,y)
			var point := Vector2(id)*16
			if not grid.region.has_point(id) or grid.is_point_solid(id): continue
			if point.distance_squared_to(at)<distance and clear_segment(at,point,layout):
				best=id; distance=point.distance_squared_to(at)
	return best
func find_path(from: Vector2, to: Vector2, layout: Resource) -> Array[Vector2]:
	var result: Array[Vector2] = []
	if layout.interior_at(from)!=layout.interior_at(to) or from.distance_to(to)>1400: return result
	if not point_clear(from,layout) or not point_clear(to,layout): return result
	if clear_segment(from,to,layout): result.append(to); return result
	var start := Vector2i((from/16).floor())
	var end := Vector2i((to/16).floor())
	var low := Vector2i(mini(start.x,end.x)-10,mini(start.y,end.y)-10)
	var high := Vector2i(maxi(start.x,end.x)+11,maxi(start.y,end.y)+11)
	var grid := AStarGrid2D.new()
	grid.region=Rect2i(low,high-low)
	grid.cell_size=Vector2(16,16)
	grid.diagonal_mode=AStarGrid2D.DIAGONAL_MODE_NEVER
	grid.update()
	for y in range(low.y,high.y):
		for x in range(low.x,high.x):
			grid.set_point_solid(Vector2i(x,y),not point_clear(Vector2(x,y)*16,layout))
	var a := nearest(from,grid,layout)
	var b := nearest(to,grid,layout)
	if a==Vector2i.MAX or b==Vector2i.MAX: return result
	var raw: Array[Vector2] = []
	for id in grid.get_id_path(a,b): raw.append(Vector2(id)*16)
	if raw.is_empty(): return result
	raw.append(to)
	var previous := from
	for point in raw:
		if not clear_segment(previous,point,layout): return []
		previous=point
	# Collapse only collision-clear segments, preserving obstacle detours.
	previous=from
	while not raw.is_empty():
		var index := raw.size()-1
		while index>0 and not clear_segment(previous,raw[index],layout): index-=1
		result.append(raw[index]); previous=raw[index]
		for i in range(index+1): raw.pop_front()
	return result
func set_target(from: Vector2, to: Vector2, layout: Resource) -> bool:
	path=find_path(from,to,layout)
	stalled=0
	last_position=from
	return not path.is_empty()
func stop(actor: CharacterBody2D) -> void:
	path.clear(); actor.velocity=Vector2.ZERO
func advance(actor: CharacterBody2D, delta: float, speed: float) -> String:
	if path.is_empty(): actor.velocity=Vector2.ZERO; return "arrived"
	var motion := path[0]-actor.position
	actor.velocity=motion.normalized()*speed
	var before := actor.position
	actor.move_and_collide(motion.limit_length(speed*delta))
	if actor.position.distance_to(before)<0.05: stalled+=delta
	else: stalled=0
	if stalled>0.7: stop(actor); return "blocked"
	if actor.position.distance_to(path[0])<0.5:
		path.pop_front()
		if path.is_empty(): actor.velocity=Vector2.ZERO; return "arrived"
	return "moving"
