extends Node
# Commands retain their complete wire payload until acknowledged. A timeout
# never manufactures a second reward request with a different identity.
signal updated(data: Dictionary, operation: String)
signal snapshot_received(data: Dictionary, operation: String)
signal failed(message: String)
var backend_url := "http://127.0.0.1:8000"
var game_scope := ""
var state: Dictionary = {}
var busy := false
var request: HTTPRequest
var pending: Dictionary = {}
var sent_scope := ""
var refreshing := false
var snapshot_filter: Callable
var activity_events = preload("res://scripts/revisioned_state.gd").new()
func _ready() -> void:
	request=HTTPRequest.new(); request.timeout=10; add_child(request)
	request.request_completed.connect(_completed)
func restore(data: Dictionary) -> void:
	request.cancel_request(); busy=false; pending={}; refreshing=false
	game_scope=str(data.get("game_scope",""))
	state=data.get("gatherer_encounter",{}).duplicate(true)
func send_command(command: String, payload: Dictionary={}) -> void:
	if busy: return
	if not pending.is_empty():
		failed.emit("An encounter save needs Retry before another choice can be made."); return
	if state.is_empty() or game_scope.is_empty():
		failed.emit("Gatherer encounter data is unavailable. Restart the backend and reload your save."); return
	pending={"game_scope":game_scope,"command":command,"request_id":game_scope+":gatherer:"+Crypto.new().generate_random_bytes(16).hex_encode(),"expected_revision":state.get("revision",0),"payload":payload.duplicate(true)}
	retry()
func retry() -> void:
	if busy: return
	if refreshing: _refresh(); return
	if pending.is_empty(): _refresh(); return
	busy=true; sent_scope=game_scope
	if request.request(backend_url+"/gatherer/command",PackedStringArray(["Content-Type: application/json"]),HTTPClient.METHOD_POST,JSON.stringify(pending))!=OK:
		busy=false; failed.emit("Could not save the encounter. Check your connection and Retry.")
func refresh() -> void:
	if not busy: _refresh()
func _refresh() -> void:
	busy=true; refreshing=true; sent_scope=game_scope
	if request.request(backend_url+"/world")!=OK:
		busy=false; failed.emit("Could not refresh the encounter. Retry to reconnect.")
func _completed(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	busy=false
	if sent_scope!=game_scope: return
	var data: Variant=JSON.parse_string(body.get_string_from_utf8()) if not body.is_empty() else null
	if code==409 and not refreshing:
		_refresh(); return
	if result!=HTTPRequest.RESULT_SUCCESS or code!=200 or not data is Dictionary:
		failed.emit("Could not save the encounter. Retry keeps your choice and cannot repeat its consequences."); return
	if data.get("game_scope","")!=game_scope:
		pending={}; refreshing=false
		failed.emit("This game was replaced. Reload the current game to continue."); return
	var operation: String="refresh" if refreshing else str(pending.get("command",""))
	var incoming: Dictionary=data.get("gatherer_encounter",{})
	if incoming.is_empty():
		failed.emit("The backend did not return the encounter. Reload after updating the backend."); return
	if int(incoming.get("revision",-1))<int(state.get("revision",0)):
		_refresh(); return
	if snapshot_filter.is_valid():
		data = snapshot_filter.call(data)
		incoming = data.get("gatherer_encounter", {})
		if incoming.is_empty(): return
	state=incoming.duplicate(true); pending={}; refreshing=false
	snapshot_received.emit(data, operation)
	if activity_events.consume_activity("encounter:gatherer", game_scope, state): updated.emit(data,operation)
