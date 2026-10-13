# Render the measured GFX-01 sample without loading or mutating any world.
extends SceneTree
func _initialize() -> void: call_deferred("run_sample")
func sprite(parent: Node2D, file: String, at: Vector2, pivot: Vector2, factor := 2.0) -> void:
	var s := Sprite2D.new()
	s.texture = load("res://assets/" + file + ".svg")
	s.centered = false
	s.offset = -pivot
	s.scale = Vector2.ONE * factor
	s.position = at
	s.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	parent.add_child(s)
func run_sample() -> void:
	root.size = Vector2i(1280, 720)
	var board := Node2D.new()
	root.add_child(board)
	for y in range(0,720,32):
		for x in range(0,1280,32):sprite(board,"world/" + ("path-0" if y>460 and y<590 else "grass-0"),Vector2(x,y),Vector2.ZERO)
	sprite(board,"world/workshop",Vector2(280,430),Vector2(64,115))
	sprite(board,"world/cottage-a",Vector2(560,430),Vector2(40,91))
	sprite(board,"world/tree-0",Vector2(740,430),Vector2(24,68))
	sprite(board,"world/produce-0",Vector2(900,430),Vector2(24,44))
	sprite(board,"world/bench",Vector2(400,494),Vector2(24,28))
	sprite(board,"characters/sample",Vector2(520,506),Vector2(12,30))
	sprite(board,"portraits/player",Vector2(1040,322),Vector2.ZERO)
	var caption := Label.new()
	caption.text = "GFX-01 • EXACT-GRID SCALE SAMPLE\n2 world units / source pixel • Original Willowbrook art\nWorkshop / cottage / tree / stall / bench / player / matching portrait\nBlue: foot origins • Red: ground footprints • Yellow: clear approach"
	caption.position = Vector2(32,24)
	caption.add_theme_font_size_override("font_size",22)
	board.add_child(caption)
	var overlay := Node2D.new()
	board.add_child(overlay)
	overlay.draw.connect(func():
		for at in [Vector2(280,430),Vector2(560,430),Vector2(740,430),Vector2(900,430),Vector2(400,494),Vector2(520,506)]:overlay.draw_rect(Rect2(at-Vector2(3,3),Vector2(6,6)),Color.CYAN)
		for r in [Rect2(165,305,230,125),Rect2(496,302,128,128),Rect2(732,414,16,16),Rect2(868,398,64,32),Rect2(366,478,68,16),Rect2(508,498,24,16)]:overlay.draw_rect(r,Color("f07a6a"),false,2)
		overlay.draw_rect(Rect2(528,434,64,64),Color("f6d97e"),false,2))
	for i in range(5):await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(ProjectSettings.globalize_path("res://../../docs/evidence/graphics-overhaul/exact-grid-sample.png"))
	quit()
