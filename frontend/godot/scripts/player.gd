extends CharacterBody2D

@export var speed: float = 180.0
var control_enabled := true

func set_control_enabled(enabled: bool) -> void:
	control_enabled=enabled
	velocity=Vector2.ZERO


func _physics_process(_delta: float) -> void:
	if not control_enabled:
		velocity=Vector2.ZERO
		return
	if get_viewport().gui_get_focus_owner() is LineEdit:
		velocity = Vector2.ZERO
		return
	var direction := Vector2.ZERO
	if Input.is_key_pressed(KEY_A):
		direction.x -= 1.0
	if Input.is_key_pressed(KEY_D):
		direction.x += 1.0
	if Input.is_key_pressed(KEY_W):
		direction.y -= 1.0
	if Input.is_key_pressed(KEY_S):
		direction.y += 1.0

	var movement_speed := speed
	if direction != Vector2.ZERO and Input.is_key_pressed(KEY_SHIFT):
		movement_speed *= 1.5
	velocity = direction.normalized() * movement_speed
	move_and_slide()
