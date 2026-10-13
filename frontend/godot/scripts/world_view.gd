extends Node
# Simulation stays in world units; only presentation is quantized.
var world_viewport: SubViewport
var world: Node2D
var world_camera: Camera2D
var presentation: TextureRect
var enlargement := 2
var remainder := Vector2i.ZERO

func _ready() -> void:
	world_viewport = SubViewport.new()
	world_viewport.disable_3d = true
	world_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	world_viewport.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	world_viewport.snap_2d_transforms_to_pixel = true
	world_viewport.snap_2d_vertices_to_pixel = true
	add_child(world_viewport)
	world = Node2D.new()
	world.y_sort_enabled = true
	world.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	world_viewport.add_child(world)
	world_camera = Camera2D.new()
	world_camera.zoom = Vector2(0.5,0.5)
	world_camera.position_smoothing_enabled = false
	world_camera.process_callback = Camera2D.CAMERA2D_PROCESS_IDLE
	world.add_child(world_camera)
	presentation = TextureRect.new()
	presentation.mouse_filter = Control.MOUSE_FILTER_IGNORE
	presentation.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	presentation.texture = world_viewport.get_texture()
	presentation.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	add_child(presentation)
	get_viewport().size_changed.connect(_resize)
	_resize()

func _resize() -> void: resize_world(Vector2i(get_viewport().get_visible_rect().size))

func resize_world(window: Vector2i) -> void:
	enlargement = maxi(2, mini(window.x / 640, window.y / 360))
	world_viewport.size = Vector2i(window.x / enlargement,window.y / enlargement)
	remainder = window - world_viewport.size * enlargement
	presentation.position = Vector2(remainder / 2)
	presentation.size = Vector2(world_viewport.size * enlargement)

func follow(at: Vector2) -> void:
	world_camera.position = (at / 2.0).round() * 2.0
	world_camera.force_update_scroll()

func world_to_screen(at: Vector2) -> Vector2:
	return presentation.position + world_viewport.canvas_transform * at * enlargement
