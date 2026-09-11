extends Node2D

var coat := Color("3e7d91")
var apron := false
var phase := 0.0


func _process(delta: float) -> void:
	phase += delta * 8.0
	queue_redraw()


func _draw() -> void:
	var moving: bool = get_parent() is CharacterBody2D and get_parent().velocity.length() > 1
	var stride := sin(phase) * 4.0 if moving else 0.0
	draw_set_transform(Vector2(3, 7), 0, Vector2(1, 0.42))
	draw_circle(Vector2.ZERO, 18, Color(0, 0, 0, 0.25))
	draw_set_transform(Vector2.ZERO)
	draw_line(Vector2(-6, -5), Vector2(-6, 9 + stride), Color("34383b"), 8)
	draw_line(Vector2(6, -5), Vector2(6, 9 - stride), Color("34383b"), 8)
	draw_style_box(_coat_style(), Rect2(-13, -31, 26, 29))
	draw_line(Vector2(-16, -25), Vector2(-16, -7 - stride), coat.darkened(0.12), 7)
	draw_line(Vector2(16, -25), Vector2(16, -7 + stride), coat.darkened(0.12), 7)
	if apron:
		draw_rect(Rect2(-9, -22, 18, 20), Color("73543a"))
	draw_circle(Vector2(0, -38), 11, Color("d2a67e"))
	draw_arc(Vector2(0, -40), 10, PI, TAU, 12, Color("48382c"), 7)
	draw_circle(Vector2(-4, -37), 1.2, Color("332b29"))
	draw_circle(Vector2(4, -37), 1.2, Color("332b29"))


func _coat_style() -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = coat
	style.set_corner_radius_all(7)
	return style
