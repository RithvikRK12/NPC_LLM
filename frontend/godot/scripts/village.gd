extends Node2D

const MAP_RECT := Rect2(-836, -470, 1672, 940)
const PLAZA_TEXTURE := preload("res://assets/backgrounds/cyberpunk_plaza.png")


func _ca(hex: String, alpha: float) -> Color:
	var color := Color(hex)
	color.a = alpha
	return color


func _draw() -> void:
	draw_rect(Rect2(-1600, -1000, 3200, 2000), Color("04060c"))
	_draw_expanded_edges()
	draw_texture_rect(PLAZA_TEXTURE, MAP_RECT, false)
	_draw_depth_structures()
	_draw_cinematic_grade()
	_draw_walkable_language()
	_draw_interaction_lighting()


func _draw_expanded_edges() -> void:
	for x in range(-1500, 1501, 96):
		draw_line(Vector2(x, MAP_RECT.position.y - 280), Vector2(x + 280, MAP_RECT.position.y), _ca("112846", 0.34), 2)
	for y in range(-700, 760, 92):
		draw_line(Vector2(MAP_RECT.position.x - 420, y), Vector2(MAP_RECT.position.x, y - 140), _ca("0a1728", 0.62), 3)
		draw_line(Vector2(MAP_RECT.end.x, y + 80), Vector2(MAP_RECT.end.x + 460, y - 70), _ca("07111f", 0.70), 3)
	draw_rect(Rect2(MAP_RECT.position.x - 520, -438, 520, 900), _ca("060913", 0.58))
	draw_rect(Rect2(MAP_RECT.end.x, -438, 540, 900), _ca("050812", 0.62))
	for i in range(8):
		var left := Rect2(MAP_RECT.position.x - 490 + i * 42, -374 + i * 88, 28, 74)
		var right := Rect2(MAP_RECT.end.x + 80 + i * 45, -340 + i * 82, 30, 86)
		draw_rect(left, _ca("19f6ff", 0.12 + float(i % 3) * 0.03))
		draw_rect(right, _ca("ff3df2", 0.10 + float(i % 2) * 0.04))


func _draw_cinematic_grade() -> void:
	draw_rect(MAP_RECT, _ca("050713", 0.18))
	draw_rect(Rect2(MAP_RECT.position, Vector2(MAP_RECT.size.x, 160)), _ca("000000", 0.20))
	draw_rect(Rect2(MAP_RECT.position + Vector2(0, MAP_RECT.size.y - 170), Vector2(MAP_RECT.size.x, 170)), _ca("000000", 0.28))
	for radius in [460.0, 360.0, 270.0]:
		draw_circle(Vector2(360, -120), radius, _ca("ffb84a", 0.018))
	for radius in [420.0, 320.0, 220.0]:
		draw_circle(Vector2(-430, -140), radius, _ca("ff3df2", 0.022))
	for radius in [360.0, 250.0, 150.0]:
		draw_circle(Vector2(-70, 240), radius, _ca("19f6ff", 0.020))


func _draw_depth_structures() -> void:
	# Dark foreground architecture gives the painted map physical depth and hides map edges.
	draw_colored_polygon(PackedVector2Array([
		Vector2(-836, 470), Vector2(-836, 270), Vector2(-640, 315),
		Vector2(-610, 470)
	]), _ca("03050a", 0.78))
	draw_colored_polygon(PackedVector2Array([
		Vector2(520, 470), Vector2(836, 470), Vector2(836, 184),
		Vector2(650, 244)
	]), _ca("03050a", 0.76))
	draw_line(Vector2(-790, 312), Vector2(-612, 356), _ca("19f6ff", 0.42), 3)
	draw_line(Vector2(640, 255), Vector2(812, 198), _ca("ffb84a", 0.38), 3)
	draw_rect(Rect2(-835, -470, 1670, 940), _ca("000000", 0.10), false, 2)


func _draw_walkable_language() -> void:
	var route := PackedVector2Array([
		Vector2(-465, -95),
		Vector2(-230, -42),
		Vector2(0, 0),
		Vector2(205, -48),
		Vector2(400, -118)
	])
	draw_polyline(route, _ca("000000", 0.34), 74.0, true)
	draw_polyline(route, _ca("19f6ff", 0.20), 42.0, true)
	draw_polyline(route, _ca("ff3df2", 0.16), 16.0, true)
	for i in range(15):
		var t := float(i) / 14.0
		var p := _sample_route(route, t)
		draw_circle(p, 4.0, _ca("dffcff", 0.45))
	var branch := PackedVector2Array([Vector2(-40, 18), Vector2(-48, 112), Vector2(-70, 240)])
	draw_polyline(branch, _ca("19f6ff", 0.24), 26.0, true)
	draw_polyline(branch, _ca("f5ff6b", 0.22), 8.0, true)


func _draw_interaction_lighting() -> void:
	_marker(Vector2(360, -120), "TECHSMITH", Color("ffb84a"), Color("19f6ff"))
	_marker(Vector2(-430, -140), "DATA BROKER", Color("ff3df2"), Color("ffeb6e"))
	_marker(Vector2(-70, 240), "FIBER CABLE", Color("19f6ff"), Color("f5ff6b"))


func _marker(center: Vector2, label: String, glow: Color, accent: Color) -> void:
	draw_circle(center, 62, Color(glow, 0.10))
	draw_circle(center, 36, Color(glow, 0.16))
	draw_arc(center, 28, 0, TAU, 48, Color(accent, 0.78), 2.5)
	draw_arc(center, 36, -PI * 0.20, PI * 0.80, 32, Color(glow, 0.85), 3.0)
	draw_line(center + Vector2(-28, 0), center + Vector2(-15, 0), Color(accent, 0.80), 2)
	draw_line(center + Vector2(15, 0), center + Vector2(28, 0), Color(accent, 0.80), 2)
	draw_line(center + Vector2(0, -28), center + Vector2(0, -15), Color(accent, 0.80), 2)
	draw_line(center + Vector2(0, 15), center + Vector2(0, 28), Color(accent, 0.80), 2)


func _sample_route(route: PackedVector2Array, t: float) -> Vector2:
	var segment_count := route.size() - 1
	var scaled := clampf(t, 0.0, 1.0) * float(segment_count)
	var index := mini(int(floor(scaled)), segment_count - 1)
	var local_t := scaled - float(index)
	return route[index].lerp(route[index + 1], local_t)
