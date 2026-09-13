extends SceneTree

const FIXTURE_ROOT := "res://../../contracts/fixtures/v1"
const VALID_NAMES := ["valid-calm-speak.json", "valid-cautious-move.json", "valid-refusal-speak.json", "valid-urgent-retreat.json"]
const INVALID_NAMES := ["invalid-incompatible-version.json", "invalid-unknown-action.json", "invalid-numeric-overflow.json"]

func _initialize() -> void:
	for name in VALID_NAMES:
		_assert_valid(name)
	for name in INVALID_NAMES:
		_assert_invalid(name)
	print("C03 Godot fixture reader: %d valid and %d invalid fixtures passed" % [VALID_NAMES.size(), INVALID_NAMES.size()])
	quit(0)

func _read(name: String) -> Variant:
	var file := FileAccess.open(FIXTURE_ROOT + "/" + name, FileAccess.READ)
	assert(file != null, "missing fixture " + name)
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	assert(parsed is Dictionary, "fixture must be an object: " + name)
	return parsed

func _assert_valid(name: String) -> void:
	var fixture: Dictionary = _read(name)
	var envelope: Dictionary = fixture["envelope"]
	var revisions: Dictionary = fixture["revisions"]
	var command: Dictionary = fixture["command"]
	assert(envelope["schema_version"] == 1, "unsupported version in " + name)
	assert(envelope["npc_id"] == revisions["npc_id"], "NPC scope mismatch in " + name)
	assert(int(revisions["approved_npc_state_revision"]) <= 9007199254740991, "unsafe revision in " + name)
	assert(command["approval_id"] == envelope["causation_id"], "approval lineage mismatch in " + name)
	assert(command["issued_at"] == envelope["created_at"], "issuance mismatch in " + name)
	assert(command["controller_revision"] == _controller_revision(revisions, envelope["npc_id"]), "controller mismatch in " + name)

func _controller_revision(revisions: Dictionary, npc_id: String) -> int:
	for entry: Dictionary in revisions["controller"]:
		if entry["scope_id"] == npc_id:
			return int(entry["revision"])
	return -1

func _assert_invalid(name: String) -> void:
	var fixture: Dictionary = _read(name)
	var envelope: Dictionary = fixture["envelope"]
	var command: Dictionary = fixture["command"]
	if name == "invalid-incompatible-version.json":
		assert(envelope["schema_version"] != 1, "invalid version unexpectedly accepted")
	elif name == "invalid-numeric-overflow.json":
		assert(float(command["parameters"]["max_speed"]) < 0.0, "invalid numeric fixture missing")
	else:
		assert(command["kind"] not in ["speak", "face_target", "move_to", "approach_target", "retreat_from_target", "interact", "play_animation", "idle"], "invalid command unexpectedly accepted")
