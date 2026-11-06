extends CharacterBody2D
var npc_id := 1
var display_name := "Craftsman"
var role_name := "craftsman"
var label: Label
var location_text := "Workshop"
var speed := 180.0
func _ready() -> void:
	motion_mode = MOTION_MODE_FLOATING
	collision_layer = 2
	collision_mask = 1
	var sense := Area2D.new()
	sense.name = "InteractionArea"
	sense.collision_layer = 0
	sense.collision_mask = 0
	var shape := CollisionShape2D.new()
	var circle := CircleShape2D.new()
	circle.radius = 96
	shape.shape = circle
	sense.add_child(shape)
	add_child.call_deferred(sense)
func apply_state(data: Dictionary) -> void:
	refresh_label(float(data.get("trust",0)),float(data.get("fear",0)),float(data.get("aggression",0)),float(data.get("curiosity",0)))
func refresh_label(trust: float=0, fear: float=0, aggression: float=0, curiosity: float=0) -> void:
	if label == null: return
	label.text = display_name+"\n"+location_text
	label.tooltip_text = "Trust %.2f | Fear %.2f | Aggression %.2f | Curiosity %.2f" % [trust,fear,aggression,curiosity]
func face(at: Vector2) -> void:
	var direction := at-position
	var facing := "left" if direction.x<0 else "right"
	if absf(direction.y)>absf(direction.x): facing="up" if direction.y<0 else "down"
	for child in get_children():
		if child.has_method("set_facing"): child.set_facing(facing)
