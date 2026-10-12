extends SceneTree

const FIXTURE := "res://../../backend/tests/fixtures/gateway/contract-codec-t01-valid.json"
const ACTIONS := ["idle", "speak", "face_target", "move_to", "approach_target", "retreat_from_target", "interact", "play_animation"]

func _initialize() -> void:
	var file := FileAccess.open(FIXTURE, FileAccess.READ)
	assert(file != null, "missing gateway fixture")
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	assert(parsed is Dictionary, "fixture must parse to dictionary")
	var payload: Dictionary = parsed["payload"]
	var command: Dictionary = payload["command"]
	assert(command["schema_version"] == 1, "unsupported schema version")
	assert(command["timeline_id"] == "timeline:main", "timeline mismatch")
	assert(ACTIONS.has(command["kind"]), "unknown command action")
	assert(command["target_id"] != null, "entity command requires target")
	assert(float(command["parameters"]["max_speed"]) >= 0.0, "max_speed must be finite and nonnegative")
	assert(float(command["parameters"]["arrival_distance"]) >= 0.0, "arrival_distance must be finite and nonnegative")
	assert(parsed["result"]["command"]["command_id"] == command["command_id"], "result must preserve command id")
	print("gateway.contract_codec Godot fixture smoke passed")
	quit(0)
