extends Node
signal updated(data: Dictionary, operation: String)
signal snapshot_received(data: Dictionary, operation: String)
signal failed(message: String)
var backend_url := "http://127.0.0.1:8000"
var game_scope := ""
var state: Dictionary = {}
var busy := false
var request: HTTPRequest
var operation := ""
var pending_command: Dictionary = {}
var sent_scope := ""
var checkpoint_provider: Callable
var last_checkpoint: Dictionary = {}
var sent_checkpoint: Dictionary = {}
var save_elapsed := 0.0
var retry_payload: Dictionary = {}
var snapshot_filter: Callable
var activity_events = preload("res://scripts/revisioned_state.gd").new()
func _ready() -> void:
	request=HTTPRequest.new(); request.timeout=10; add_child(request)
	request.request_completed.connect(_completed)
func restore(data: Dictionary) -> void:
	game_scope=data.get("game_scope","")
	state=data.get("craftsman_encounter",{})
	last_checkpoint={}; pending_command={}; retry_payload={}
func ingest(data: Dictionary) -> void:
	if data.get("game_scope",game_scope)!=game_scope: return
	if snapshot_filter.is_valid(): data = snapshot_filter.call(data)
	var incoming: Dictionary=data.get("craftsman_encounter",{})
	if int(incoming.get("revision",-1))>=int(state.get("revision",0)): state=incoming
func send_command(command: String, payload: Dictionary={}, request_id: String="") -> void:
	if game_scope.is_empty() or state.is_empty():
		failed.emit("The backend has not loaded the Craftsman encounter. Restart the backend, then reopen the game to continue. Your save will be kept.")
		return
	if not pending_command.is_empty(): return
	if not request_id.is_empty() and retry_payload.get("request_id", "") == request_id:
		if not busy: _send("command", retry_payload.duplicate(true))
		return
	if request_id.is_empty(): request_id=game_scope+":"+command+":"+str(Time.get_ticks_usec())
	pending_command={"command":command,"payload":payload,"request_id":request_id}
	if busy: return
	# Save physical staging before asking the server to commit its outcome.
	if command=="complete_inspection" and state.get("inspection_complete",false): _send_pending()
	elif checkpoint_provider.is_valid(): save_checkpoint(checkpoint_provider.call())
	else: _send_pending()
func _send_pending() -> void:
	if pending_command.is_empty(): return
	var body: Dictionary=pending_command.duplicate(true)
	pending_command={}
	body.merge({"game_scope":game_scope,"npc_id":1,"expected_revision":state.get("revision",0)})
	retry_payload=body
	_send("command",body)
func save_checkpoint(value: Dictionary) -> void:
	if busy or game_scope.is_empty() or state.is_empty(): return
	if value==last_checkpoint:
		_send_pending(); return
	sent_checkpoint=value.duplicate(true)
	_send("checkpoint",{"game_scope":game_scope,"expected_revision":state.get("revision",0),"checkpoint":value})
func tick(delta: float) -> void:
	save_elapsed+=delta
	if busy or not checkpoint_provider.is_valid(): return
	var current: Dictionary=checkpoint_provider.call()
	var boundary := false
	for key in ["mode","navigation_space","return_index","presentation","presentation_beat"]:
		if current.get(key)!=last_checkpoint.get(key): boundary=true
	if save_elapsed<1 and not boundary: return
	save_elapsed=0
	save_checkpoint(current)
func _send(kind: String, body: Dictionary) -> void:
	operation=kind; sent_scope=game_scope; busy=true
	var method := HTTPClient.METHOD_POST if kind=="command" else HTTPClient.METHOD_PUT
	if request.request(backend_url+"/craftsman/"+kind,PackedStringArray(["Content-Type: application/json"]),method,JSON.stringify(body))!=OK:
		busy=false; failed.emit("Could not save the Craftsman encounter. Try again.")
func _completed(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	busy=false
	if sent_scope!=game_scope: return
	var data: Variant=JSON.parse_string(body.get_string_from_utf8()) if not body.is_empty() else null
	if result!=HTTPRequest.RESULT_SUCCESS or code!=200 or not data is Dictionary:
		pending_command={}
		failed.emit("Could not save the Craftsman encounter. "+str(data.get("detail","Reconnect and retry.") if data is Dictionary else "Reconnect and retry."))
		if code==409:
			operation="refresh"; busy=true
			if request.request(backend_url+"/world")!=OK: busy=false
		return
	if data.get("game_scope",game_scope)!=game_scope: return
	var kind := operation
	if snapshot_filter.is_valid(): data = snapshot_filter.call(data)
	if int(data.get("craftsman_encounter", {}).get("revision", -1)) < int(state.get("revision", 0)): return
	ingest(data)
	if kind=="checkpoint":
		# Acknowledge exactly what was sent. JSON decodes integer fields as
		# floats; reconstructed dictionaries do not compare equal in Godot.
		last_checkpoint=sent_checkpoint.duplicate(true)
	snapshot_received.emit(data, kind)
	if kind == "checkpoint" or activity_events.consume_activity("activity:ship_inspection", game_scope, state): updated.emit(data,kind)
	if kind=="checkpoint" and not pending_command.is_empty():
		if checkpoint_provider.is_valid(): save_checkpoint(checkpoint_provider.call())
		else: _send_pending()
