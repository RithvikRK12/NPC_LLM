extends Node2D

var room_id: String
var layout: Resource
var props: Array[Node2D] = []
var floor_sprite: Sprite2D

func _ready() -> void:
	position = layout.interior_origin(room_id)
	var backdrop := Polygon2D.new()
	backdrop.polygon = PackedVector2Array([Vector2(-1024,-1024),Vector2(1024,-1024),Vector2(1024,1024),Vector2(-1024,1024)])
	backdrop.color = Color("171b20")
	backdrop.z_index = -25
	add_child(backdrop)
	floor_sprite = Sprite2D.new()
	floor_sprite.texture = load("res://assets/world/%s.svg" % layout.interiors()[room_id].floor_art)
	floor_sprite.centered = false
	floor_sprite.position = Vector2(-320,-240)
	floor_sprite.scale = Vector2(2,2)
	floor_sprite.z_index = -20
	add_child(floor_sprite)
	# Geometry comes from the same footprints used to recover saved positions.
	var walls := StaticBody2D.new()
	add_child(walls)
	var obstacles: Array[Rect2] = layout.interior_obstacles(room_id)
	for rect in obstacles.slice(0,4):
		var collider := CollisionShape2D.new()
		var shape := RectangleShape2D.new()
		shape.size = rect.size
		collider.shape = shape
		collider.position = rect.get_center()-position
		walls.add_child(collider)
	var index := 0
	for furniture in layout.interiors()[room_id].furniture:
		var prop := preload("res://scenes/world/PlacedProp.tscn").instantiate()
		var entry: Dictionary = furniture.duplicate(true)
		entry.id = room_id + "-furniture-" + str(index)
		entry.at = [position.x + furniture.at[0],position.y + furniture.at[1]]
		entry.ambient = false
		prop.entry = entry
		prop.layout = layout
		get_parent().add_child.call_deferred(prop)
		props.append(prop)
		index += 1

func _exit_tree() -> void:
	for prop in props:
		if is_instance_valid(prop): prop.queue_free()

func set_debug(enabled: bool) -> void:
	for prop in props:
		prop.debug_geometry = enabled
		prop.queue_redraw()
