extends SceneTree

var failures := 0
class RecordingWorld extends "res://tests/fisherman_test_main.gd":
	var recorded_action := ""
	var recorded_payload: Dictionary = {}
	func _quest_call(action: String, payload: Dictionary = {}) -> void:
		recorded_action = action
		recorded_payload = payload
func check(ok: bool, label: String) -> void:
	if not ok:
		failures += 1
		push_error(label)

func _initialize() -> void:
	call_deferred("run_check")

func run_check() -> void:
	if not FileAccess.file_exists("res://scripts/forest_gift_pickups.gd"):
		check(false, "Forest gift pickup view must exist")
		quit(1)
		return
	var pickups = load("res://scripts/forest_gift_pickups.gd").new()
	root.add_child(pickups)
	pickups.sync({})
	check(pickups.nearby(Vector2(-880, 224)).is_empty(), "Honeycomb must be hidden before advice")
	var rules: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://resources/gatherer_recovery.json"))
	var layout = load("res://resources/village_layout.tres")
	for pickup in rules.pickups:
		var at := Vector2(float(pickup.position.x), float(pickup.position.y))
		check(layout.is_walkable(at), "Honeycomb must be on clear ground: " + str(pickup.id))
		check(layout.route_exists(Vector2(-560, 70), at), "Honeycomb must be reachable from the forest entrance: " + str(pickup.id))
	pickups.sync({"hint_unlocked": true, "pickups": rules.pickups})
	pickups.update_proximity(Vector2(-880, 224))
	check(pickups.markers["honeycomb-1"].get_child(0).visible, "Nearby pickup must show its key hint")
	check(not pickups.markers["honeycomb-2"].get_child(0).visible, "Distant key hints must not clutter the view")
	check(pickups.nearby(Vector2(-880, 224)).get("id") == "honeycomb-1", "F interaction must find the nearest honeycomb")
	check(pickups.nearby(Vector2.ZERO).is_empty(), "Distant honeycomb must not be collectible")
	pickups.sync({"hint_unlocked": true, "pickups": rules.pickups.slice(1)})
	check(pickups.nearby(Vector2(-880, 224)).is_empty(), "Collected honeycomb must disappear after authoritative refresh")
	check(pickups.nearby(Vector2(-1184, 352)).get("id") == "honeycomb-2", "Other forest gifts must remain collectible")
	pickups.sync({})
	check(pickups.nearby(Vector2(-1184, 352)).is_empty(), "Reset or completed recovery must hide pickups")
	var world := RecordingWorld.new()
	world.backend_url = "http://127.0.0.1:1"
	root.add_child(world)
	world.world_loaded = true
	world.game_scope = "test:gift-pickup"
	world.player.position = Vector2(-880, 224)
	world.forest_gifts.sync({"pickups": rules.pickups})
	var key := InputEventKey.new()
	key.keycode = KEY_F
	key.pressed = true
	world._unhandled_input(key)
	check(world.recorded_action == "pickup-honeycomb", "F must reach the real quest pickup action")
	check(world.recorded_payload.get("pickup_id") == "honeycomb-1", "F must send the selected pickup ID")
	check(world.recorded_payload.get("game_scope") == "test:gift-pickup", "F must scope the pickup to the current save")
	world.queue_free()
	print("Forest gift pickups: ", "PASS" if failures == 0 else "FAIL")
	pickups.queue_free()
	await process_frame
	quit(0 if failures == 0 else 1)
