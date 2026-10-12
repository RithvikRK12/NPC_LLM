extends Node2D


func _draw() -> void:
	draw_rect(Rect2(-1400, -1100, 2800, 2200), Color("405d3c"))
	var rng := RandomNumberGenerator.new()
	rng.seed = 42
	for i in range(2200):
		var p := Vector2(rng.randf_range(-1300, 1300), rng.randf_range(-1000, 1000))
		draw_line(p, p + Vector2(2, -5), Color("526d45"), 1.0)
	# Worn footpaths link the forest, square and workshop.
	draw_polyline(PackedVector2Array([Vector2(-800, 70), Vector2(-170, 70), Vector2(0, 0), Vector2(210, 0), Vector2(750, 180)]), Color("827659"), 76.0, true)
	draw_polyline(PackedVector2Array([Vector2(-800, 70), Vector2(-170, 70), Vector2(0, 0), Vector2(210, 0), Vector2(750, 180)]), Color("a18e67"), 56.0, true)
	for i in range(100):
		var p := Vector2(rng.randf_range(-650, 650), rng.randf_range(-24, 24))
		draw_circle(p + Vector2(0, 45), 2, Color("b3a07a"))
	# Timber workshop with roof tiles, stone base, doorway and lit windows.
	draw_rect(Rect2(88, -222, 235, 148), Color(0, 0, 0, 0.2))
	draw_rect(Rect2(80, -230, 230, 144), Color("84745e"))
	draw_rect(Rect2(88, -222, 214, 123), Color("bd9a69"))
	for x in range(90, 305, 34):
		draw_line(Vector2(x, -220), Vector2(x, -100), Color("5d4432"), 7)
	draw_rect(Rect2(174, -170, 46, 74), Color("382e28"))
	for x in [108, 244]:
		draw_rect(Rect2(x, -181, 32, 36), Color("e6bd69"))
		draw_line(Vector2(x + 16, -181), Vector2(x + 16, -145), Color("604932"), 4)
	draw_colored_polygon(PackedVector2Array([Vector2(60, -214), Vector2(190, -307), Vector2(331, -214)]), Color("70493a"))
	for y in range(-280, -212, 16):
		var width := float(y + 307) * 1.42
		draw_line(Vector2(190 - width, y), Vector2(190 + width, y), Color("97644b"), 4)
	draw_rect(Rect2(259, -296, 24, 59), Color("72655a"))
	# Workbench, logs and anvil beside the craftsman.
	draw_rect(Rect2(250, -45, 62, 27), Color("624833"))
	draw_rect(Rect2(246, -55, 70, 23), Color("b18a56"))
	draw_colored_polygon(PackedVector2Array([Vector2(264, -71), Vector2(303, -71), Vector2(291, -62), Vector2(288, -51), Vector2(271, -51)]), Color("4e565b"))
	for i in range(5):
		draw_line(Vector2(330, -111 + i * 12), Vector2(382, -111 + i * 12), Color("65462f"), 11)
		draw_circle(Vector2(330, -111 + i * 12), 5, Color("c29861"))
	# Village well.
	draw_circle(Vector2(-10, 180), 39, Color(0, 0, 0, 0.18))
	draw_circle(Vector2(-15, 172), 33, Color("9a9b8d"))
	draw_circle(Vector2(-15, 172), 23, Color("344d54"))
	draw_line(Vector2(-47, 172), Vector2(-47, 110), Color("694c34"), 7)
	draw_line(Vector2(17, 172), Vector2(17, 110), Color("694c34"), 7)
	draw_colored_polygon(PackedVector2Array([Vector2(-60, 117), Vector2(-15, 88), Vector2(31, 117)]), Color("845841"))
	for i in range(25):
		var p := Vector2(rng.randf_range(-650, -290), rng.randf_range(-360, 360))
		_tree(p, rng.randf_range(0.8, 1.3))
	for i in range(10):
		_tree(Vector2(rng.randf_range(-200, 650), rng.randf_range(330, 470)), 1.0)
	for x in range(65, 400, 35):
		draw_line(Vector2(x, 208), Vector2(x + 35, 208), Color("8c7350"), 5)
		draw_line(Vector2(x, 221), Vector2(x + 35, 221), Color("8c7350"), 5)
		draw_line(Vector2(x, 199), Vector2(x, 235), Color("c1a477"), 7)


func _tree(p: Vector2, scale_factor: float) -> void:
	draw_circle(p + Vector2(8, 12), 35 * scale_factor, Color(0, 0, 0, 0.15))
	draw_line(p, p + Vector2(0, -43 * scale_factor), Color("664934"), 12 * scale_factor)
	draw_circle(p + Vector2(0, -50 * scale_factor), 34 * scale_factor, Color("274b35"))
	draw_circle(p + Vector2(-12, -61) * scale_factor, 25 * scale_factor, Color("376346"))
	draw_circle(p + Vector2(10, -69) * scale_factor, 21 * scale_factor, Color("4c7950"))
