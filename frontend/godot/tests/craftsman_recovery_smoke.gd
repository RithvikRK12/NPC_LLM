extends SceneTree
class RecordingGateway extends "res://scripts/craftsman_gateway.gd":
	var dispatched: Dictionary = {}
	func _send(kind: String, body: Dictionary) -> void:
		operation=kind; sent_scope=game_scope; busy=true; dispatched={"kind":kind,"body":body}
var failures := 0
func check(ok: bool, text: String) -> void:
	if not ok: failures+=1; push_error(text)
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var gateway=RecordingGateway.new(); root.add_child(gateway)
	gateway.game_scope="recovery"; gateway.state={"revision":1}
	var final_checkpoint := {"mode":"following_player","navigation_space":"exterior","position":{"x":32,"y":3632},"wait_reason":"","return_index":0,"presentation":"outcome_pending","presentation_beat":4}
	gateway.checkpoint_provider=func(): return final_checkpoint
	gateway.busy=true; gateway.operation="checkpoint"; gateway.sent_scope="recovery"
	gateway.send_command("complete_inspection",{"staged":true},"outcome")
	var old: Dictionary=final_checkpoint.duplicate(true); old.position={"x":32,"y":3504}; old.presentation="inspection_staging"
	old.revision=2; old.game_scope="recovery"
	gateway._completed(HTTPRequest.RESULT_SUCCESS,200,PackedStringArray(),JSON.stringify({"game_scope":"recovery","craftsman_encounter":old}).to_utf8_buffer())
	check(gateway.dispatched.get("kind")=="checkpoint","Queued outcome flushes the latest staging checkpoint first")
	var staged: Dictionary=final_checkpoint.duplicate(true); staged.revision=3; staged.game_scope="recovery"
	gateway._completed(HTTPRequest.RESULT_SUCCESS,200,PackedStringArray(),JSON.stringify({"game_scope":"recovery","craftsman_encounter":staged}).to_utf8_buffer())
	check(gateway.dispatched.get("kind")=="command","Acknowledged staging sends the queued command exactly once")
	gateway.queue_free()
	var main=load("res://tests/fisherman_test_main.gd").new(); root.add_child(main)
	main.world_loaded=true; main.fisherman.intro_seen=true; main.craftsman_activity.intro_seen=true
	main.player.position=Vector2(10000,10176)
	main.craftsman_activity.outing_active=true; main.craftsman_activity.mode="waiting_for_player"; main.craftsman_activity.wait_reason="requested"
	var npc_at: Vector2=main.npc_nodes[1].position
	main._travel_to(main.village.layout.exterior_spawn("workshop"),"down")
	while main.travelling: await process_frame
	check(main.npc_nodes[1].position==npc_at and main.craftsman_activity.space=="workshop","Leaving workshop preserves explicit wait command")
	var encounter=main.craftsman_encounter
	main.player.position=Vector2(-32,3632); main.npc_nodes[1].position=Vector2(32,3632)
	main.craftsman_activity.space="exterior"; encounter.phase="outcome_pending"
	encounter._failed("Simulated lost response")
	check(not encounter.owns_input(),"Failed activation restores player control while Retry is available")
	main.craftsman_activity.presentation="outcome_pending"
	encounter.restore({"ship_repair":{}})
	check(encounter.phase=="outcome_retry","Reload at uncommitted outcome offers retry without replaying the walk")
	var committed: Dictionary=main.craftsman_activity.checkpoint()
	committed.merge({"inspection_complete":true,"outing_active":false,"mode":"returning_to_workshop"},true)
	encounter._updated({"craftsman_encounter":committed},"refresh")
	check(main.craftsman_activity.overridden,"Recovered farewell reacquires NPC presentation ownership")
	npc_at=main.npc_nodes[1].position
	for i in range(20): await physics_frame
	check(main.npc_nodes[1].position==npc_at,"NPC stays beside the ship until recovered farewell closes")
	encounter.cancel(); main.queue_free(); await process_frame
	print("Craftsman recovery: ",failures," failures"); quit(1 if failures else 0)
