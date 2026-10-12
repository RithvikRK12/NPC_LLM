extends CharacterBody3D

var controller: Node
var avatar: Node3D
var synced := Vector2.ZERO
const SCALE := 0.025

func _ready() -> void:
	var collider := CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.radius = 0.28
	capsule.height = 1.8
	collider.shape = capsule
	collider.position.y = 0.9
	add_child(collider)
	avatar = preload("res://scripts/human_3d.gd").new()
	add_child(avatar)
	floor_snap_length = 0.3

func _physics_process(delta: float) -> void:
	# Preserve the existing API's Vector2 coordinates, including saved games and smoke fixtures.
	if controller.player.position != synced:
		position = Vector3(controller.player.position.x * SCALE, 0.05, controller.player.position.y * SCALE)
		synced = controller.player.position
	var direction := Vector3.ZERO
	var enabled: bool = controller.world_loaded and not controller.quitting and not controller.restart_dialog.visible and not controller.paused
	avatar.set_process(not controller.paused)
	if enabled and not get_viewport().gui_get_focus_owner() is LineEdit:
		direction = Vector3(float(Input.is_key_pressed(KEY_D)) - float(Input.is_key_pressed(KEY_A)), 0,
			float(Input.is_key_pressed(KEY_S)) - float(Input.is_key_pressed(KEY_W)))
	velocity.x = direction.normalized().x * 5.2
	velocity.z = direction.normalized().z * 5.2
	velocity.y -= 20.0 * delta
	move_and_slide()
	avatar.walking = direction.length_squared() > 0.0
	if avatar.walking:
		avatar.rotation.y = lerp_angle(avatar.rotation.y, atan2(-direction.x, -direction.z), delta * 12.0)
	if position.y < -4:
		position = Vector3(0, 0.1, 0)
	if enabled:
		synced = Vector2(position.x, position.z) / SCALE
		controller.player.position = synced
