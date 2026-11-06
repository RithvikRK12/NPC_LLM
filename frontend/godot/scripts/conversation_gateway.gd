extends Node
## Versioned, idempotent chat transport. It has no presentation or gameplay authority.

signal turn_finalized(request_id: String, response: Dictionary)
signal turn_pending(request_id: String)
signal turn_failed(request_id: String, message: String, retryable: bool)
signal world_refresh_requested(data: Dictionary)

const STORAGE_PREFIX := "user://conversation_gateway_pending_npc_"
const POLL_SECONDS := 0.75
const CLEAR_RETRY_SECONDS := 2.0
const MAX_CLEAR_RETRIES := 5
var backend_url := "http://127.0.0.1:8000"
var npc_id := 0
var http: HTTPRequest
var poll_timer: Timer
var clear_retry_timer: Timer
var payload: Dictionary = {}
var active_request_id := ""
var active_scope := ""
var active_epoch := -1
var current_scope := ""
var current_epoch := 0
var status_url := ""
var pending := false
var mode := ""
var restored_waiting_for_context := false
var deferred_final_response: Dictionary = {}
var deferred_failure_detail := ""
var deferred_refresh_after_clear := false
var clear_retry_attempts := 0
var refresh_after_active_request := false

func _ready() -> void:
	http = HTTPRequest.new()
	http.timeout = 160
	add_child(http)
	http.request_completed.connect(_on_request_completed)
	poll_timer = Timer.new()
	poll_timer.wait_time = POLL_SECONDS
	poll_timer.timeout.connect(_poll_status)
	add_child(poll_timer)
	clear_retry_timer = Timer.new()
	clear_retry_timer.one_shot = true
	clear_retry_timer.wait_time = CLEAR_RETRY_SECONDS
	clear_retry_timer.timeout.connect(_retry_deferred_clear)
	add_child(clear_retry_timer)
	_restore_pending()

func new_request_id() -> String:
	return "godot:%s" % ResourceUID.create_id()

func storage_path_for_npc(id: int) -> String:
	return STORAGE_PREFIX + str(id) + ".cfg"

func build_payload(request_id: String, game_scope: String, npc_id: int, epoch: int, message: String) -> Dictionary:
	return {"schema_version": 1, "request_id": request_id, "game_scope": game_scope,
		"conversation_epoch": epoch, "npc_id": npc_id, "player_message": message}

func is_pending_response(code: int, response: Dictionary) -> bool:
	return code == 202 and response.has("status_url") and response.has("turn")

func is_current_response(response_scope: String, response_epoch: int, current_scope: String, current_epoch: int) -> bool:
	return response_scope == current_scope and response_epoch == current_epoch

func restored_key_matches(current_scope: String, current_epoch: int) -> bool:
	return not current_scope.is_empty() and is_current_response(active_scope, active_epoch, current_scope, current_epoch)

func persistence_allows_dispatch(save_error: int) -> bool:
	return save_error == OK

func clear_allows_publication(save_error: int) -> bool:
	return save_error == OK

func submit(game_scope: String, epoch: int, npc_id: int, message: String) -> String:
	if pending or game_scope.is_empty() or message.strip_edges().is_empty(): return ""
	active_request_id = new_request_id()
	payload = build_payload(active_request_id, game_scope, npc_id, epoch, message)
	active_scope = game_scope
	active_epoch = epoch
	status_url = ""
	pending = true
	if not persistence_allows_dispatch(_persist_pending()):
		_reset_pending_memory()
		return ""
	_send_submission()
	return active_request_id

## Delivery retry preserves the exact request identity and payload.
func retry() -> void:
	if not pending: return
	if not deferred_final_response.is_empty() or not deferred_failure_detail.is_empty():
		_attempt_deferred_clear()
		return
	if not status_url.is_empty(): _send_status_lookup()
	else: _send_submission()

func invalidate(current_scope: String, current_epoch: int) -> void:
	# Startup windows exist before /world completes. An empty scope is not a
	# confirmed key change and must not discard a persisted in-flight request.
	if current_scope.is_empty(): return
	self.current_scope = current_scope
	self.current_epoch = current_epoch
	if pending and not deferred_failure_detail.is_empty(): return
	if pending and not restored_key_matches(current_scope, current_epoch):
		poll_timer.stop()
		if is_instance_valid(http) and http.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED: http.cancel_request()
		_defer_failed_clear("Conversation changed. Refresh and send again if needed.", true)
		return
	if pending and restored_waiting_for_context:
		restored_waiting_for_context = false
		if not deferred_final_response.is_empty():
			_publish_final_response(deferred_final_response)
		else:
			call_deferred("retry")

func _send_submission() -> void:
	if not pending or http.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED: return
	mode = "submit"
	var err := http.request(backend_url + "/chat", ["Content-Type: application/json"], HTTPClient.METHOD_POST, JSON.stringify(payload))
	if err != OK: _delivery_lost()

func _send_status_lookup() -> void:
	if not pending or status_url.is_empty() or http.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED: return
	mode = "lookup"
	var err := http.request(backend_url + status_url, [], HTTPClient.METHOD_GET)
	if err != OK: _delivery_lost()

func _poll_status() -> void:
	if pending:
		if status_url.is_empty(): _send_submission()
		else: _send_status_lookup()

func _on_request_completed(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if mode == "world":
		if result == HTTPRequest.RESULT_SUCCESS and code == 200:
			var world: Variant = JSON.parse_string(body.get_string_from_utf8())
			if world is Dictionary: world_refresh_requested.emit(world)
		return
	if refresh_after_active_request:
		refresh_after_active_request = false
		call_deferred("_refresh_world")
	if not pending: return
	if result != HTTPRequest.RESULT_SUCCESS:
		_delivery_lost()
		return
	var parsed: Variant = JSON.parse_string(body.get_string_from_utf8())
	var response: Dictionary = parsed if parsed is Dictionary else {}
	if code == 409 or code == 404:
		poll_timer.stop()
		_defer_failed_clear("Conversation is stale or unavailable. World state was refreshed.", true)
		return
	if is_pending_response(code, response):
		status_url = str(response.status_url)
		if not persistence_allows_dispatch(_persist_pending()):
			# Keep the in-memory identity and continue read-only polling. The
			# original payload was persisted before POST, so recovery can safely
			# redeliver that same ID if the previous status URL write did not stick.
			push_warning("Could not persist conversation status URL; retaining the same request identity for recovery.")
		turn_pending.emit(active_request_id)
		poll_timer.start()
		return
	if code == 200 and not response.is_empty() and response.has("final_dialogue"):
		poll_timer.stop()
		# Do not publish a reply from a conversation that changed while in flight.
		if current_scope.is_empty():
			deferred_final_response = response
			restored_waiting_for_context = true
			return
		var current := is_current_response(active_scope, active_epoch, current_scope, current_epoch)
		if current: _publish_final_response(response)
		else:
			_defer_failed_clear("Conversation changed. World state was refreshed.", true)
		return
	_delivery_lost()

func _delivery_lost() -> void:
	if not pending: return
	# Defer retries to avoid a recursive loop when HTTPRequest rejects synchronously.
	poll_timer.start()

func _refresh_world() -> void:
	if http.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
		refresh_after_active_request = true
		return
	mode = "world"
	if http.request(backend_url + "/world") != OK:
		world_refresh_requested.emit({})

func _persist_pending() -> int:
	var config := ConfigFile.new()
	config.set_value("pending", "payload", payload)
	config.set_value("pending", "status_url", status_url)
	return config.save(storage_path_for_npc(npc_id))

func _restore_pending() -> void:
	var config := ConfigFile.new()
	if config.load(storage_path_for_npc(npc_id)) != OK: return
	var saved: Variant = config.get_value("pending", "payload", {})
	if not saved is Dictionary or saved.is_empty(): return
	payload = saved
	active_request_id = str(payload.get("request_id", ""))
	active_scope = str(payload.get("game_scope", ""))
	active_epoch = int(payload.get("conversation_epoch", -1))
	status_url = str(config.get_value("pending", "status_url", ""))
	if active_request_id.is_empty(): return
	pending = true
	# Wait for chat_window to receive the authoritative /world conversation key.
	restored_waiting_for_context = true

func _publish_final_response(response: Dictionary) -> void:
	deferred_final_response = response.duplicate(true)
	deferred_failure_detail = ""
	deferred_refresh_after_clear = false
	clear_retry_attempts = 0
	_attempt_deferred_clear()

func _defer_failed_clear(detail: String, refresh_world: bool) -> void:
	deferred_final_response.clear()
	deferred_failure_detail = detail
	deferred_refresh_after_clear = refresh_world
	clear_retry_attempts = 0
	_attempt_deferred_clear()

func _attempt_deferred_clear() -> void:
	clear_retry_timer.stop()
	var final_copy := deferred_final_response.duplicate(true)
	var failure_copy := deferred_failure_detail
	var refresh_after := deferred_refresh_after_clear
	var old_id := active_request_id
	if _clear_pending():
		if not final_copy.is_empty():
			turn_finalized.emit(old_id, final_copy)
		elif not failure_copy.is_empty():
			if refresh_after: _refresh_world()
			turn_failed.emit(old_id, failure_copy, false)
		return
	clear_retry_attempts += 1
	push_warning("Could not durably clear conversation request; retaining its identity and outcome.")
	if clear_retry_attempts < MAX_CLEAR_RETRIES:
		clear_retry_timer.start(CLEAR_RETRY_SECONDS)
	else:
		push_warning("Conversation clear retry limit reached; the turn remains pending until retry or restart.")

func _retry_deferred_clear() -> void:
	if not deferred_final_response.is_empty() or not deferred_failure_detail.is_empty():
		_attempt_deferred_clear()

func _clear_pending() -> bool:
	var config := ConfigFile.new()
	if not clear_allows_publication(config.save(storage_path_for_npc(npc_id))): return false
	_reset_pending_memory()
	return true

func _reset_pending_memory() -> void:
	clear_retry_timer.stop()
	pending = false
	payload.clear()
	active_request_id = ""
	active_scope = ""
	active_epoch = -1
	status_url = ""
	restored_waiting_for_context = false
	deferred_final_response.clear()
	deferred_failure_detail = ""
	deferred_refresh_after_clear = false
	clear_retry_attempts = 0
