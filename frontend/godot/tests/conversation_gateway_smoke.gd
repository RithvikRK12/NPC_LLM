extends SceneTree

const Gateway = preload("res://scripts/conversation_gateway.gd")

var passed := 0
var failed := 0

func _initialize() -> void:
	var gateway = Gateway.new()
	check(gateway.new_request_id() != gateway.new_request_id(), "each new submission gets a fresh ID")
	var payload := gateway.build_payload("same-id", "scope:1", 1, 2, "Hello")
	check(payload.request_id == "same-id")
	check(payload.schema_version == 1 and payload.game_scope == "scope:1")
	check(payload.conversation_epoch == 2 and payload.npc_id == 1)
	check(payload.player_message == "Hello")
	check(gateway.storage_path_for_npc(1) != gateway.storage_path_for_npc(2),
		"each NPC must have an isolated pending-turn storage record")
	var pending := {"status_url": "/chat/turns/t1", "phase": "queued", "turn": {"turn_id": "t1"}}
	check(gateway.is_pending_response(202, pending))
	check(not gateway.is_pending_response(200, {"final_dialogue": "done"}))
	check(gateway.is_current_response("scope:1", 2, "scope:1", 2))
	check(not gateway.is_current_response("old", 2, "scope:1", 2))
	check(not gateway.is_current_response("scope:1", 1, "scope:1", 2))
	# An empty startup scope arrives before /world has supplied the authoritative key.
	gateway.pending = true
	gateway.active_scope = "scope:1"
	gateway.active_epoch = 2
	gateway.restored_waiting_for_context = true
	gateway.invalidate("", 0)
	check(gateway.pending and gateway.restored_waiting_for_context and gateway.active_scope == "scope:1" and gateway.active_epoch == 2,
		"uninitialized world scope must preserve restored request identity")
	check(gateway.restored_key_matches("scope:1", 2), "matching world key may resume the persisted identity")
	check(not gateway.restored_key_matches("scope:old", 2), "stale world key must not resume the persisted identity")
	check(not gateway.restored_key_matches("scope:1", 1), "stale epoch must not resume the persisted identity")
	check(gateway.persistence_allows_dispatch(OK), "a successfully persisted request may be dispatched")
	check(not gateway.persistence_allows_dispatch(ERR_CANT_OPEN), "a request must not dispatch if identity persistence fails")
	check(gateway.clear_allows_publication(OK), "publication may follow a durable clear")
	check(not gateway.clear_allows_publication(ERR_CANT_OPEN), "publication must wait when durable clear fails")
	gateway.free()
	print("conversation_gateway_smoke: %d passed, %d failed" % [passed, failed])
	quit(1 if failed > 0 else 0)

func check(condition: bool, label: String = "") -> void:
	if condition:
		passed += 1
	else:
		failed += 1
		push_error("conversation_gateway_smoke: FAIL %s" % label)
