extends Node2D

const RULES_PATH := "res://resources/gatherer_recovery.json"
var markers: Dictionary = {}
var available: Array = []

func _ready() -> void:
	var rules: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(RULES_PATH))
	for pickup in rules.pickups:
		var marker := Sprite2D.new()
		marker.z_index = 3
		marker.texture = preload("res://assets/items/pixel/honeycomb.svg")
		marker.position = Vector2(float(pickup.position.x), float(pickup.position.y))
		marker.scale = Vector2(2, 2)
		marker.offset = Vector2(0, -10)
		var label := Label.new()
		label.text = "Honeycomb • F"
		label.position = Vector2(-44, -38)
		label.scale = Vector2(0.5, 0.5)
		label.add_theme_color_override("font_color", Color("fff0ce"))
		label.add_theme_color_override("font_outline_color", Color("302419"))
		label.add_theme_constant_override("outline_size", 4)
		label.hide()
		marker.add_child(label)
		add_child(marker)
		markers[str(pickup.id)] = marker
		marker.hide()

func sync(recovery: Dictionary) -> void:
	available = recovery.get("pickups", []).duplicate(true)
	for id in markers:
		markers[id].visible = available.any(func(pickup): return str(pickup.id) == id)

func update_proximity(at: Vector2) -> void:
	for marker in markers.values():
		marker.get_child(0).visible = marker.visible and marker.position.distance_to(at) <= 96.0

func nearby(at: Vector2) -> Dictionary:
	var closest: Dictionary = {}
	var distance := 64.0
	for pickup in available:
		var target := Vector2(float(pickup.position.x), float(pickup.position.y))
		var candidate := at.distance_to(target)
		if candidate <= distance:
			closest = pickup
			distance = candidate
	return closest
