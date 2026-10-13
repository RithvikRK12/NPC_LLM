extends StaticBody2D
var entry: Dictionary
var layout: Resource
var sprite: Sprite2D
var debug_geometry := false
var reduced_motion := false
var clock := 0.0
var last_phase := 0
func _ready() -> void:
	position = layout.anchor(entry)
	clock = float(hash(entry.id) % 100) / 10.0
	sprite = Sprite2D.new()
	sprite.texture = load("res://assets/world/%s.svg" % entry.art)
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	sprite.centered = false
	sprite.scale = Vector2(2,2)
	sprite.offset = -Vector2(entry.pivot[0],entry.pivot[1])
	add_child(sprite)
	var f: Rect2 = layout.local_footprint(entry)
	if f.size != Vector2.ZERO:
		var collision := CollisionShape2D.new()
		var shape := RectangleShape2D.new()
		shape.size = f.size
		collision.shape = shape
		collision.position = f.get_center()
		add_child(collision)
	if entry.get("smoke",false): sprite.z_index = 1
	set_process(entry.ambient)
func _process(delta: float) -> void:
	clock += delta
	var phase := 0 if reduced_motion else int(clock / 1.25) % 2
	if phase == last_phase: return
	last_phase = phase
	var art: String = entry.art
	if entry.get("smoke",false):
		sprite.position = Vector2(phase*2,-phase*4)
		sprite.visible = not reduced_motion
	else:
		sprite.texture = load("res://assets/world/%s.svg" % (art.left(art.length()-1) + str(phase)))
func _draw() -> void:
	if not debug_geometry: return
	draw_rect(Rect2(-Vector2(entry.pivot[0],entry.pivot[1])*2,sprite.texture.get_size()*2),Color("c7d68c"),false,1)
	draw_rect(layout.local_footprint(entry),Color("ed7364"),false,2)
	draw_circle(Vector2.ZERO,3,Color.CYAN)
	if entry.has("approach"):
		var at := Vector2(entry.approach[0],entry.approach[1])-position
		draw_rect(Rect2(at-Vector2(24,16),Vector2(48,32)),Color("f5db82"),false,2)
