extends Node2D
var item: Dictionary
var solid := true
func _ready() -> void:
	name=item.id
	position=item.at
	var sprite:=Sprite2D.new()
	sprite.texture=load("res://assets/cutscene/opening/%s-%s.svg" % [item.kind,item.variant])
	sprite.scale=Vector2(2,2)
	sprite.position=Vector2(0,-sprite.texture.get_height()+12)
	if item.kind in ["stones","shells","flowers","driftwood"]: sprite.z_index=-2
	add_child(sprite)
	var size: Vector2=item.footprint
	if solid and size!=Vector2.ZERO:
		var body:=StaticBody2D.new(); var collider:=CollisionShape2D.new(); var shape:=RectangleShape2D.new()
		shape.size=size; collider.shape=shape; body.add_child(collider); add_child(body)
