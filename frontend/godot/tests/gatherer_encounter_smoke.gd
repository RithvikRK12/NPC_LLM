extends SceneTree
class RecordingGateway extends "res://scripts/gatherer_gateway.gd":
	var refreshes := 0
	func _refresh() -> void:
		refreshes+=1; refreshing=true; busy=true; sent_scope=game_scope
var failures := 0
func check(value: bool, text: String):
	print("PASS " if value else "FAIL ",text)
	if not value: failures+=1
func _initialize(): call_deferred("run")
func reply(state: Dictionary) -> PackedByteArray:
	return JSON.stringify({"game_scope":"scope","gatherer_encounter":state}).to_utf8_buffer()
func run():
	var gateway=RecordingGateway.new(); root.add_child(gateway)
	gateway.game_scope="scope"; gateway.sent_scope="scope"
	gateway.state={"status":"intro_pending","revision":2}
	gateway.pending={"command":"victory","request_id":"same-victory","payload":{"attempt_id":"attempt"},"expected_revision":2}
	var original=gateway.pending.duplicate(true)
	gateway._completed(HTTPRequest.RESULT_CANT_CONNECT,0,PackedStringArray(),PackedByteArray())
	check(gateway.pending==original and not gateway.busy,"Lost outcome response preserves original payload and request ID")
	gateway._completed(HTTPRequest.RESULT_SUCCESS,200,PackedStringArray(),reply({"status":"saved_thanks_pending","revision":3}))
	check(gateway.pending.is_empty() and gateway.state.status=="saved_thanks_pending","Acknowledged outcome unlocks thanks")
	gateway.pending=original.duplicate(true)
	gateway._completed(HTTPRequest.RESULT_SUCCESS,409,PackedStringArray(),PackedByteArray())
	check(gateway.refreshes==1 and gateway.busy,"Revision conflict fetches authoritative state")
	gateway._completed(HTTPRequest.RESULT_SUCCESS,200,PackedStringArray(),reply({"status":"resolved_helped","revision":4}))
	check(gateway.pending.is_empty() and gateway.state.status=="resolved_helped","Conflict recovery adopts committed branch without another reward")
	gateway.restore({"game_scope":"new-scope","gatherer_encounter":{"status":"unseen","revision":0}})
	gateway.sent_scope="scope"
	gateway._completed(HTTPRequest.RESULT_SUCCESS,200,PackedStringArray(),reply({"status":"resolved_helped","revision":4}))
	check(gateway.game_scope=="new-scope" and gateway.state.status=="unseen","Old-scope callback cannot replace new game")
	gateway.free()
	quit(1 if failures else 0)
