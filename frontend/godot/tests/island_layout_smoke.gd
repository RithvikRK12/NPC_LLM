extends SceneTree
var failures := 0
func check(ok: bool, label: String) -> void:
	print("PASS " if ok else "FAIL ",label)
	if not ok: failures+=1
func _initialize() -> void:
	var script = load("res://scripts/island_layout.gd")
	if script==null: check(false,"Island layout exists"); quit(1); return
	var layout = script.new()
	check(layout.is_exterior_walkable(Vector2(0,3600)),"Handoff is on land")
	check(not layout.is_exterior_walkable(Vector2(0,3900)),"Open sea south of wreck")
	for edge in [-8192,8192]:
		for y in range(-6144,6145,32):
			if layout.is_exterior_walkable(Vector2(edge,y)): check(false,"East/west ocean margin")
	for edge in [-6144,6144]:
		for x in range(-8192,8193,32):
			if layout.is_exterior_walkable(Vector2(x,edge)): check(false,"North/south ocean margin")
	check(layout.recover_exterior_position(Vector2(40000,40000))==layout.recover_exterior_position(Vector2(40000,40000)),"Deterministic recovery")
	check(layout.recover_exterior_position(Vector2(30.125,50.875))==Vector2(30.125,50.875),"Valid float coordinates retained")
	var world_layout=load("res://resources/village_layout.tres")
	check(world_layout.recover_position(Vector2(10064.25,10032.125))==Vector2(10064.25,10032.125),"Interior floats retained")
	var clear := true
	var route: Array = layout.data().routes[0]
	for i in range(route.size()-1):
		var a := Vector2(route[i][0],route[i][1])
		var b := Vector2(route[i+1][0],route[i+1][1])
		var normal := (b-a).normalized().orthogonal()
		for step in range(int(a.distance_to(b)/4)+1):
			for offset in [-32,0,32]:
				if not world_layout.is_walkable(a.move_toward(b,step*4)+normal*offset): clear=false
	check(clear,"64-unit inland corridor connects wreck to village")
	var spawn: Array=layout.data().recovery_markers.beach
	var start:=Vector2i(floor(spawn[0]/32),floor(spawn[1]/32))
	var pending: Array[Vector2i]=[start]
	var connected: Dictionary={start:true}
	var index:=0
	while index<pending.size():
		var cell:=pending[index]; index+=1
		for direction in [Vector2i.UP,Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT]:
			var next: Vector2i=cell+direction
			if not connected.has(next) and layout.land_cell(next): connected[next]=true; pending.append(next)
	var land_count:=0
	for y in range(-192,192):
		for x in range(-256,256):
			if layout.land_cell(Vector2i(x,y)): land_count+=1
	check(connected.size()==land_count,"Every land cell and reserved region connects to the southern spawn (%s cells)" % land_count)
	check(layout.reserve_fraction()>=0.35,"At least 35% usable land reserved")
	print("Usable land area: ",layout.usable_area()," reserve: ",layout.reserve_fraction())
	quit(1 if failures else 0)
