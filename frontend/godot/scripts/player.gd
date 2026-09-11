extends CharacterBody2D

@export var speed: float = 180.0


func _physics_process(_delta: float) -> void:
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

	velocity = direction.normalized() * speed
	move_and_slide()