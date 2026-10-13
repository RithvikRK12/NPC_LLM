extends Node2D
const Layout = preload("res://resources/village_layout.tres")
var layout := Layout
var ground: Sprite2D
var props: Array[Node2D] = []
var debug_geometry := false
var reduced_motion := false
const PATH = [Vector2(-850,70),Vector2(-170,70),Vector2(0,0),Vector2(210,32),Vector2(384,32),Vector2(576,64),Vector2(800,128),Vector2(960,192)]
func _ready() -> void:
	ground = Sprite2D.new()
	ground.texture = _terrain()
	ground.centered = false
	ground.position = Vector2(-1408,-1120)
	ground.scale = Vector2(2,2)
	ground.z_index = 1
	add_child(ground)
	# Props are direct siblings of actors so all share the same ground-Y sort.
	for entry in layout.objects():
		var prop := preload("res://scenes/world/PlacedProp.tscn").instantiate()
		prop.entry = entry
		prop.layout = layout
		prop.name = entry.id
		get_parent().add_child.call_deferred(prop)
		props.append(prop)
	z_index = -30
func _exit_tree() -> void:
	for prop in props:
		if is_instance_valid(prop): prop.queue_free()
func set_debug(enabled: bool) -> void:
	debug_geometry = enabled
	for prop in props:
		prop.debug_geometry = enabled
		prop.queue_redraw()
func set_reduced_motion(enabled: bool) -> void:
	reduced_motion = enabled
	for prop in props:
		prop.reduced_motion = enabled
		if prop.entry.get("smoke",false): prop.sprite.visible = not enabled
func _draw() -> void:
	pass # IslandWorld owns all exterior land and ocean.
func path_distance(at: Vector2) -> float:
	var result := INF
	for i in range(PATH.size()-1):result = minf(result,Geometry2D.get_closest_point_to_segment(at,PATH[i],PATH[i+1]).distance_to(at))
	# Join the shared southern approach across this locally owned terrain patch.
	for segment in [[Vector2(0,1120),Vector2(0,600)],[Vector2(0,600),Vector2(-112,300)],[Vector2(-112,300),Vector2(-112,128)]]:
		result=minf(result,Geometry2D.get_closest_point_to_segment(at,segment[0],segment[1]).distance_to(at))
	# A quiet southern clearing leads to the authoritative string pickup.
	for segment in [[Vector2.ZERO,Vector2(-112,128)],[Vector2(-112,128),Vector2(-70,288)]]:
		result = minf(result,Geometry2D.get_closest_point_to_segment(at,segment[0],segment[1]).distance_to(at)+12)
	# Clear cottage aprons connect to the market rather than dead-end behind stalls.
	for segment in [[Vector2(496,-48),Vector2(496,64)],[Vector2(720,-80),Vector2(720,112)],[Vector2(496,-48),Vector2(560,-48)]]:
		result=minf(result,Geometry2D.get_closest_point_to_segment(at,segment[0],segment[1]).distance_to(at)+16)
	return result
func _terrain() -> ImageTexture:
	var tiles := {}
	for kind in ["grass","shade","path","soil","edge","moss"]:
		tiles[kind]=[]
		for i in range(4):
			var image: Image = load("res://assets/world/%s-%s.svg" % [kind,i]).get_image()
			image.convert(Image.FORMAT_RGBA8)
			tiles[kind].append(image)
	var canvas := Image.create(1408,1120,false,Image.FORMAT_RGBA8)
	for y in range(0,1120,16):
		for x in range(0,1408,16):
			var world_y := float(y*2-1120)
			var forest_edge := -340.0 + sin(world_y/90.0)*42.0 + cos(world_y/140.0)*24.0
			var distance := float(x*2-1408)-forest_edge
			var kind := "shade" if distance< -24 else ("moss" if distance<24 else "grass")
			var variation := posmod(x/16*7+y/16*13,4)
			canvas.blit_rect(tiles[kind][variation],Rect2i(0,0,16,16),Vector2i(x,y))
	for y in range(496,1120,4):
		for x in range(256,1200,4):
			var at := Vector2(x*2-1408+4,y*2-1120+4)
			var distance := path_distance(at)
			if distance<52:
				var kind := "path" if distance<46 else "edge"
				var variation := posmod(x/16+y/16,4)
				canvas.blit_rect(tiles[kind][variation],Rect2i(x%16,y%16,4,4),Vector2i(x,y))
	# Cottage garden soil, away from the clear door aprons.
	for at in [Vector2i(900,450),Vector2i(1100,440)]:
		for y in range(at.y,at.y+24,16):
			for x in range(at.x,at.x+32,16):canvas.blit_rect(tiles.soil[0],Rect2i(0,0,16,16),Vector2i(x,y))
	return ImageTexture.create_from_image(canvas)
