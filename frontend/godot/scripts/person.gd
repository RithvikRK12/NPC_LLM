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
	draw_set_transform(Vector2(5, 9), 0, Vector2(1.28, 0.42))
	draw_circle(Vector2.ZERO, 22, Color(0, 0, 0, 0.34))
	draw_set_transform(Vector2.ZERO)
	draw_line(Vector2(-7, -4), Vector2(-8, 14 + stride), Color("05070d"), 9)
	draw_line(Vector2(7, -4), Vector2(8, 14 - stride), Color("05070d"), 9)
	draw_line(Vector2(-7, 11 + stride), Vector2(-12, 23 + stride), Color("172033"), 6)
	draw_line(Vector2(7, 11 - stride), Vector2(12, 23 - stride), Color("172033"), 6)
	draw_style_box(_coat_style(), Rect2(-16, -33, 32, 34))
	draw_colored_polygon(PackedVector2Array([Vector2(-13, -31), Vector2(0, -19), Vector2(13, -31), Vector2(9, -7), Vector2(-9, -7)]), coat.darkened(0.38))
	draw_line(Vector2(-12, -18), Vector2(12, -18), coat.lightened(0.70), 2.4)
	draw_line(Vector2(-10, -5), Vector2(10, -5), _ca("19f6ff", 0.86), 2.0)
	draw_line(Vector2(-19, -27), Vector2(-22, -5 - stride), coat.darkened(0.15), 8)
	draw_line(Vector2(19, -27), Vector2(22, -5 + stride), coat.darkened(0.15), 8)
	draw_circle(Vector2(-22, -3 - stride), 4.0, Color("101827"))
	draw_circle(Vector2(22, -3 + stride), 4.0, Color("101827"))
	if apron:
		draw_rect(Rect2(-11, -23, 22, 23), Color("12182b"))
		draw_line(Vector2(-8, -10), Vector2(8, -10), Color("ffeb6e"), 2)
		draw_circle(Vector2(0, -2), 3.0, Color("19f6ff"))
	draw_circle(Vector2(0, -41), 12, Color("c89a82"))
	draw_arc(Vector2(0, -43), 11, PI, TAU, 12, Color("080b14"), 8)
	draw_rect(Rect2(-10, -43, 20, 6), _ca("19f6ff", 0.78))
	draw_line(Vector2(9, -41), Vector2(15, -47), Color("ff3df2"), 2)
	draw_circle(Vector2(-4, -39), 1.7, Color("ff3df2"))
	draw_circle(Vector2(4, -39), 1.7, Color("19f6ff"))


func _coat_style() -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = coat
	style.border_color = coat.lightened(0.5)
	style.set_border_width_all(2)
	style.set_corner_radius_all(5)
	return style


func _ca(hex: String, alpha: float) -> Color:
	var color := Color(hex)
	color.a = alpha
	return color
