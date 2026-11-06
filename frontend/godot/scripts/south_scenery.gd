extends Resource
# Stable world-space ownership: whole formations belong to the trunk's chunk.
const SIGN_POSITION := Vector2(150,940)
const ISLAND=preload("res://resources/island_layout.tres")
const BEACH=preload("res://resources/shipwreck_beach.tres")
var cache: Dictionary={}
func route_distance(at: Vector2) -> float:
	var best:=INF
	var route: Array=ISLAND.data().routes[0]
	for i in range(route.size()-1):
		var a:=Vector2(route[i][0],route[i][1]); var b:=Vector2(route[i+1][0],route[i+1][1])
		best=minf(best,at.distance_to(Geometry2D.get_closest_point_to_segment(at,a,b)))
	return best
func safe(at: Vector2, clearance: float) -> bool:
	if not ISLAND.is_exterior_walkable(at) or at.y<780 or absf(at.x)>2200: return false
	if route_distance(at)<clearance: return false
	for landmark in [Vector2(-250,2900),Vector2(-340,2830),Vector2(250,2250),Vector2(150,940)]:
		if at.distance_to(landmark)<200: return false
	for p in BEACH.data().markers.values():
		if at.distance_to(Vector2(p[0],p[1]))<(clearance+90 if clearance>=100 else 70): return false
	for solid in BEACH.data().solids:
		if Rect2(solid[0],solid[1],solid[2],solid[3]).grow(clearance).has_point(at): return false
	return true
func entry(id: String,kind: String,at: Vector2,variant: int) -> Dictionary:
	var footprint:=Vector2.ZERO
	if kind in ["palm","broadleaf"]: footprint=Vector2(22,18)
	elif kind=="outcrop": footprint=Vector2(72,36)
	elif kind=="fallen-tree": footprint=Vector2(116,28)
	elif kind=="trail-marker": footprint=Vector2(10,12)
	return {"id":id,"kind":kind,"at":at,"variant":variant,"footprint":footprint}
func entries_for_chunk(chunk: Vector2i) -> Array:
	if cache.has(chunk): return cache[chunk]
	var result: Array=[]
	var origin:=Vector2(chunk*1024)
	var coast_y: float=BEACH.data().coast_origin[1]
	for y in range(9):
		for x in range(9):
			var seed:=posmod((chunk.x*9+x)*73856093 ^ (chunk.y*9+y)*19349663,2147483647)
			var at: Vector2=(origin+Vector2(x*112+16+seed%71,y*112+16+(seed/71)%71)).snapped(Vector2(2,2))
			# Keep every generated trunk inside its owner chunk.
			if ISLAND.chunk_id_at(at)!=chunk: continue
			var distance:=route_distance(at)
			var beach: bool=at.y>coast_y-320
			var clearing: bool=at.distance_to(Vector2(0,1580))<330
			var kind: String
			if beach: kind=["shells","stones","shells","driftwood","stones","stones","shells"][seed%7]
			elif clearing: kind="flowers" if seed%3 else "shrub"
			elif seed%7<4: kind="palm" if at.y>coast_y-900 else "broadleaf"
			elif seed%7<6: kind="shrub"
			else: kind="flowers" if seed%2 else "stones"
			var clearance:=140.0 if kind in ["palm","broadleaf"] else 76.0
			if not safe(at,clearance): continue
			if distance>1500 and seed%2: continue
			result.append(entry("south_%s_%s_%s_%s" % [chunk.x,chunk.y,x,y],kind,at,seed%(4 if kind in ["palm","broadleaf"] else 3)))
	# Recognizable compositions rather than uniformly distributed props.
	for landmark in [["outcrop",Vector2(-250,2900)],["outcrop",Vector2(-340,2830)],["fallen-tree",Vector2(250,2250)],["flowers",Vector2(-210,1590)],["flowers",Vector2(220,1540)],["trail-marker",SIGN_POSITION]]:
		if ISLAND.chunk_id_at(landmark[1])==chunk: result.append(entry("landmark_%s_%s" % [landmark[0],landmark[1].y],landmark[0],landmark[1],0))
	cache[chunk]=result
	return result
func blocked(at: Vector2) -> bool:
	# Include diagonal owners: both a trunk footprint and the actor's foot box
	# can overlap a corner while their origins belong to different chunks.
	var chunk: Vector2i=ISLAND.chunk_id_at(at)
	for y in range(-1,2):
		for x in range(-1,2):
			for item in entries_for_chunk(chunk+Vector2i(x,y)):
				var size: Vector2=item.footprint
				if size!=Vector2.ZERO and Rect2(item.at-size/2,size).grow_individual(12,8,12,8).has_point(at): return true
	return false
