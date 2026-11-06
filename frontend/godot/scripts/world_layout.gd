extends Resource
@export_file("*.json") var data_file: String
const BEACH = preload("res://resources/shipwreck_beach.tres")
const SCENERY = preload("res://resources/south_scenery.tres")
const ISLAND = preload("res://resources/island_layout.tres")
var _objects: Array = []
var _interiors: Dictionary = {}
const INTERIOR_FLOOR := Rect2(-320, -176, 640, 384)

func interiors() -> Dictionary:
	if _interiors.is_empty():
		_interiors = JSON.parse_string(FileAccess.get_file_as_string("res://resources/building_interiors.json"))
	return _interiors

func interior_origin(id: String) -> Vector2:
	var at: Array = interiors()[id].origin
	return Vector2(at[0], at[1])

func interior_at(at: Vector2) -> String:
	for id in interiors():
		if Rect2(interior_origin(id) - Vector2(512,384), Vector2(1024,768)).has_point(at):
			return id
	return ""

func interior_obstacles(id: String) -> Array[Rect2]:
	var origin := interior_origin(id)
	# Solid outer walls; the south doorway transfers before feet reach the wall.
	var result: Array[Rect2] = [Rect2(-352,-240,32,480), Rect2(320,-240,32,480), Rect2(-320,-240,640,64), Rect2(-320,208,640,32)]
	for prop in interiors()[id].furniture:
		var rect := local_footprint(prop)
		rect.position += anchor(prop)
		result.append(rect)
	for i in range(result.size()): result[i].position += origin
	return result

func doorway_at(at: Vector2) -> String:
	if not interior_at(at).is_empty(): return ""
	for entry in objects():
		if interiors().has(entry.id):
			var door := anchor(entry)
			if Rect2(door + Vector2(-24,8),Vector2(48,48)).has_point(at): return entry.id
	return ""

func exterior_spawn(id: String) -> Vector2:
	for entry in objects():
		if entry.id == id: return anchor(entry) + Vector2(0,44)
	return Vector2.ZERO

func objects() -> Array:
	if _objects.is_empty():
		_objects = JSON.parse_string(FileAccess.get_file_as_string(data_file))
		_objects.append_array(JSON.parse_string(FileAccess.get_file_as_string("res://resources/forest_layout.json")).scenery)
	return _objects

func anchor(entry: Dictionary) -> Vector2: return Vector2(entry.at[0],entry.at[1])
func local_footprint(entry: Dictionary) -> Rect2:
	var f: Array = entry.get("footprint",[0,0,0,0])
	return Rect2(f[0],f[1],f[2],f[3])
func footprint(id: String) -> Rect2:
	for entry in objects():
		if entry.id == id:
			var rect := local_footprint(entry)
			rect.position += anchor(entry)
			return rect
	return Rect2()
func is_walkable(at: Vector2) -> bool:
	var room := interior_at(at)
	if not room.is_empty():
		if not INTERIOR_FLOOR.grow_individual(-12,-8,-12,-8).has_point(at-interior_origin(room)): return false
		for rect in interior_obstacles(room):
			if rect.grow_individual(12,8,12,8).has_point(at): return false
		return true
	if not ISLAND.is_exterior_walkable(at) or SCENERY.blocked(at): return false
	var beach: Dictionary = BEACH.data()
	for solid in beach.solids:
		if Rect2(solid[0],solid[1],solid[2],solid[3]).grow_individual(12,8,12,8).has_point(at): return false
	for entry in objects():
		var f := local_footprint(entry)
		if f.size == Vector2.ZERO: continue
		f.position += anchor(entry) - Vector2(12,8)
		f.size += Vector2(24,16)
		if f.has_point(at): return false
	return true
func recover_position(at: Vector2) -> Vector2:
	if is_walkable(at): return at
	var room := interior_at(at)
	if not room.is_empty():
		var spawn: Array = interiors()[room].spawn
		return interior_origin(room) + Vector2(spawn[0],spawn[1])
	if not ISLAND.is_exterior_walkable(at): return ISLAND.recover_exterior_position(at)
	for radius in range(8,513,8):
		var best := Vector2.INF
		var distance := INF
		for offset in range(-radius,radius+1,8):
			for delta in [Vector2(offset,radius),Vector2(offset,-radius),Vector2(radius,offset),Vector2(-radius,offset)]:
				var candidate: Vector2 = at + delta
				if is_walkable(candidate) and delta.length_squared()<distance:
					best=candidate
					distance=delta.length_squared()
		if best!=Vector2.INF: return best
	return at
func route_exists(start: Vector2,goal: Vector2) -> bool:
	if not is_walkable(start) or not is_walkable(goal): return false
	var pending: Array[Vector2] = [start]
	var visited := {Vector2i.ZERO:true}
	var index := 0
	while index < pending.size() and index < 20000:
		var p := pending[index]
		index += 1
		if p.distance_to(goal)<=24 and is_walkable((p+goal)/2): return true
		for d in [Vector2(16,0),Vector2(-16,0),Vector2(0,16),Vector2(0,-16)]:
			var next: Vector2 = p+d
			var key := Vector2i((next-start)/16)
			if not visited.has(key) and is_walkable(next) and is_walkable(p+d/2):
				visited[key]=true
				pending.append(next)
	return false
