extends Node2D
const LAYOUT = preload("res://resources/island_layout.tres")
const SCENERY = preload("res://resources/south_scenery.tres")
var dressing_chunks: Dictionary = {}
var chunks: Dictionary = {}
var focus := Vector2.ZERO
var view_half_extent := Vector2(640,360)
var tiles: Array[Image] = []
var shade_tiles: Array[Image] = []
var sand_tiles: Array[Image] = []
var path_tiles: Array[Image] = []
var coast_body: StaticBody2D
func _ready() -> void:
	z_index=-50
	for i in range(4):
		var image: Image=load("res://assets/world/grass-%s.svg" % i).get_image()
		image.convert(Image.FORMAT_RGBA8)
		tiles.append(image)
		var shade: Image=load("res://assets/world/shade-%s.svg" % i).get_image(); shade.convert(Image.FORMAT_RGBA8); shade_tiles.append(shade)
	for i in range(4):
		var sand: Image=load("res://assets/cutscene/opening/sand-%s.svg" % i).get_image()
		sand.convert(Image.FORMAT_RGBA8)
		sand_tiles.append(sand)
		var path: Image=load("res://assets/world/path-%s.svg" % i).get_image()
		path.convert(Image.FORMAT_RGBA8); path_tiles.append(path)
	_build_coast()
	update_active_chunks(Vector2.ZERO)
func _build_coast() -> void:
	var segments := PackedVector2Array()
	for y in range(-160,160):
		for x in range(-224,224):
			var cell:=Vector2i(x,y)
			if not LAYOUT.land_cell(cell): continue
			var p:=Vector2(cell*32)
			for side in [[Vector2i(0,-1),Vector2.ZERO,Vector2(32,0)],[Vector2i(1,0),Vector2(32,0),Vector2(32,32)],[Vector2i(0,1),Vector2(32,32),Vector2(0,32)],[Vector2i(-1,0),Vector2(0,32),Vector2.ZERO]]:
				if not LAYOUT.land_cell(cell+side[0]): segments.append(p+side[1]); segments.append(p+side[2])
	coast_body=StaticBody2D.new()
	var collider:=CollisionShape2D.new()
	var shape:=ConcavePolygonShape2D.new()
	shape.segments=segments
	collider.shape=shape
	coast_body.add_child(collider)
	add_child(coast_body)
func prepare_region(_id: StringName) -> void:
	update_active_chunks(Vector2(LAYOUT.data().recovery_markers.beach[0],LAYOUT.data().recovery_markers.beach[1]))
func update_active_chunks(at: Vector2) -> void:
	focus=at
	if at.y>8000:
		visible=false
		for dressing in dressing_chunks.values(): dressing.hide()
		return
	visible=true
	for dressing in dressing_chunks.values(): dressing.show()
	var needed := {}
	# Visible terrain plus a full adjacent ring, even when the camera straddles a seam.
	var first: Vector2i=LAYOUT.chunk_id_at(at-view_half_extent)-Vector2i.ONE
	var last: Vector2i=LAYOUT.chunk_id_at(at+view_half_extent)+Vector2i.ONE
	for y in range(first.y,last.y+1):
		for x in range(first.x,last.x+1): needed[Vector2i(x,y)]=true
	# Village and active quest/NPC region remain pinned. Authoritative actors never unload.
	for center in [Vector2i.ZERO,Vector2i(-1,0)]:
		for y in range(-1,2):
			for x in range(-1,2): needed[center+Vector2i(x,y)]=true
	for id in needed:
		if not chunks.has(id): _load_chunk(id)
	for id in chunks.keys():
		if not needed.has(id):
			chunks[id].queue_free(); chunks.erase(id)
			var dressing: Node=dressing_chunks[id]
			dressing.get_parent().remove_child(dressing); dressing.queue_free(); dressing_chunks.erase(id)
	queue_redraw()
func _load_chunk(id: Vector2i) -> void:
	var image:=Image.create(512,512,false,Image.FORMAT_RGBA8)
	for y in range(32):
		for x in range(32):
			var cell:=id*32+Vector2i(x,y)
			if not LAYOUT.land_cell(cell): continue
			image.blit_rect((shade_tiles if cell.y*32>1900 and cell.y*32<2650 and abs(cell.x)<60 else tiles)[posmod(cell.x*7+cell.y*13,4)],Rect2i(0,0,16,16),Vector2i(x*16,y*16))
			var coast := false
			for d in [Vector2i.UP,Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT]:
				if not LAYOUT.land_cell(cell+d) or not LAYOUT.land_cell(cell+d*2): coast=true
			if coast or (cell.y>=109 and abs(cell.x)<26): image.blit_rect(sand_tiles[posmod(cell.x+cell.y,4)],Rect2i(0,0,16,16),Vector2i(x*16,y*16))
			var at:=Vector2(cell*32)+Vector2(16,16)
			for route in LAYOUT.data().routes:
				for i in range(route.size()-1):
					var a:=Vector2(route[i][0],route[i][1]); var b:=Vector2(route[i+1][0],route[i+1][1])
					if at.distance_to(Geometry2D.get_closest_point_to_segment(at,a,b))<48: image.blit_rect(path_tiles[posmod(cell.x+cell.y,4)],Rect2i(0,0,16,16),Vector2i(x*16,y*16))
	var sprite:=Sprite2D.new()
	sprite.centered=false
	sprite.texture=ImageTexture.create_from_image(image)
	sprite.scale=Vector2(2,2)
	sprite.position=Vector2(id*1024)
	add_child(sprite)
	chunks[id]=sprite
	var dressing:=Node2D.new(); dressing.y_sort_enabled=true
	# Siblings in the actor Y-sort hierarchy; terrain's -50 never reaches canopies.
	get_parent().add_child(dressing)
	dressing_chunks[id]=dressing
	for item in SCENERY.entries_for_chunk(id):
		var prop=preload("res://scripts/south_prop.gd").new(); prop.item=item; dressing.add_child(prop)
func _draw() -> void:
	draw_rect(Rect2(focus-Vector2(20000,20000),Vector2(40000,40000)),Color("2c7b82"))
	for y in range(int(focus.y/96)-12,int(focus.y/96)+13):
		for x in range(int(focus.x/128)-14,int(focus.x/128)+15):
			var p:=Vector2(x*128+posmod(y*31,80),y*96)
			draw_rect(Rect2(p,Vector2(24,2)),Color("568b94"))

func _exit_tree() -> void:
	for dressing in dressing_chunks.values():
		if is_instance_valid(dressing): dressing.queue_free()
