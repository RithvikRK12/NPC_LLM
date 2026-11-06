extends Node2D
var scripted_mode := false
var identity := "player"
var sprite: AnimatedSprite2D
var facing := "down"
var last_animation := ""
var debug_geometry := false
func _ready() -> void: rebuild_frames()
func rebuild_frames() -> void:
	if sprite == null:
		sprite = AnimatedSprite2D.new()
		sprite.centered = false
		sprite.position = Vector2(-24,-60)
		sprite.scale = Vector2(2,2)
		sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		add_child(sprite)
	var frames := SpriteFrames.new()
	frames.remove_animation("default")
	var sheet: Texture2D = load("res://assets/characters/%s.svg" % identity)
	var directions := ["down","left","right","up"]
	for d in range(4):
		for moving in [false,true]:
			var animation: String = ("walk_" if moving else "idle_") + directions[d]
			frames.add_animation(animation)
			frames.set_animation_speed(animation,8)
			for f in (range(1,5) if moving else range(1)):
				var frame := AtlasTexture.new()
				frame.atlas = sheet
				frame.region = Rect2(f*24,d*32,24,32)
				frames.add_frame(animation,frame)
	if identity=="player":
		var recovery: Texture2D=load("res://assets/cutscene/opening/recovery.svg")
		var poses=["recover","brace","stand","climb_out","fall","look"]
		for i in range(poses.size()):
			frames.add_animation(poses[i])
			var frame:=AtlasTexture.new(); frame.atlas=recovery; frame.region=Rect2(i*24,0,24,32)
			frames.add_frame(poses[i],frame)
	sprite.sprite_frames = frames
	last_animation = ""
	sprite.play("idle_"+facing)
func _process(_delta: float) -> void:
	if scripted_mode: return
	var parent := get_parent()
	var velocity: Vector2 = parent.velocity if parent is CharacterBody2D else Vector2.ZERO
	var moving := velocity.length_squared()>1
	if moving:
		if absf(velocity.x)>absf(velocity.y): facing="left" if velocity.x<0 else "right"
		else: facing="up" if velocity.y<0 else "down"
	var animation := ("walk_" if moving else "idle_")+facing
	if animation != last_animation:
		sprite.play(animation)
		last_animation=animation
	# Snap only artwork relative to the unsnapped actor. Physics and saves retain floats.
	position = (parent.global_position/2.0).round()*2.0-parent.global_position
func _draw() -> void:
	if debug_geometry:
		draw_rect(Rect2(-12,-8,24,16),Color("ed7364"),false,2)
		draw_circle(Vector2.ZERO,3,Color.CYAN)

func set_scripted_mode(enabled: bool) -> void:
	scripted_mode=enabled
	if enabled and sprite: sprite.pause()
	if not enabled: last_animation=""; position=Vector2.ZERO
func play_scripted(animation: StringName, frame_index: int=0) -> void:
	if not sprite: return
	var selected: StringName=animation if sprite.sprite_frames.has_animation(animation) else &"idle_up"
	sprite.animation=selected
	sprite.frame=posmod(frame_index,sprite.sprite_frames.get_frame_count(selected))
	sprite.pause()
func set_facing(direction: StringName) -> void: facing=String(direction)
