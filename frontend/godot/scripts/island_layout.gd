extends Resource
@export_file("*.json") var data_file := "res://resources/island_layout.json"
var _data: Dictionary = {}
var _mask: Dictionary = {}
func data() -> Dictionary:
	if _data.is_empty(): _data=JSON.parse_string(FileAccess.get_file_as_string(data_file))
	return _data
func polygon() -> PackedVector2Array:
	var result := PackedVector2Array()
	for at in data().outline: result.append(Vector2(at[0],at[1]))
	return result
func land_cell(cell: Vector2i) -> bool:
	if not _mask.has(cell): _mask[cell]=Geometry2D.is_point_in_polygon(Vector2(cell*32)+Vector2(16,16),polygon())
	return _mask[cell]
func is_exterior_walkable(at: Vector2) -> bool:
	for y in [at.y-8,at.y+7.999]:
		for x in [at.x-12,at.x+11.999]:
			if not land_cell(Vector2i(floor(x/32),floor(y/32))): return false
	return true
func recover_exterior_position(at: Vector2) -> Vector2:
	if is_exterior_walkable(at): return at
	var best := Vector2.ZERO
	var distance := INF
	var ids: Array = data().recovery_markers.keys()
	ids.sort()
	for id in ids:
		var p: Array = data().recovery_markers[id]
		var candidate := Vector2(p[0],p[1])
		var d := at.distance_squared_to(candidate)
		if d<distance and is_exterior_walkable(candidate): best=candidate; distance=d
	return best
func chunk_id_at(at: Vector2) -> Vector2i: return Vector2i(floor(at.x/1024),floor(at.y/1024))
func usable_area() -> float:
	# Coast cells are excluded from capacity, using a 64-unit inland clearance.
	var count := 0
	for y in range(-160,160):
		for x in range(-224,224):
			var cell := Vector2i(x,y)
			if land_cell(cell) and land_cell(cell+Vector2i(2,0)) and land_cell(cell-Vector2i(2,0)) and land_cell(cell+Vector2i(0,2)) and land_cell(cell-Vector2i(0,2)): count+=1
	return count*1024.0
func reserve_fraction() -> float:
	var committed := 0.0
	for region in data().regions:
		if region.status=="current": committed+=region.budget
	return 1.0-committed/usable_area()
