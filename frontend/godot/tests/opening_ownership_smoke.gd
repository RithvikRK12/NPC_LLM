extends SceneTree
var failures:=0
func check(ok: bool,label: String) -> void:
	print("PASS " if ok else "FAIL ",label)
	if not ok: failures+=1
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var scene=load("res://scenes/Main.tscn").instantiate()
	scene.backend_url="http://127.0.0.1:1"
	root.add_child(scene)
	await process_frame
	var payload={"opening_capability":1,"opening_state":"pending","game_scope":"fake","player_inventory":["food","water"],"player_position":{"x":0,"y":0}}
	scene._world_completed(0,200,PackedStringArray(),JSON.stringify(payload).to_utf8_buffer())
	check(scene.get("cinematic")==true,"Pending snapshot takes cinematic ownership")
	if scene.get("opening")==null: scene.queue_free(); quit(1); return
	scene.opening.director.set_paused(true)
	var start: Vector2=scene.player.position
	for key in [KEY_W,KEY_E,KEY_F,KEY_I]:
		var event:=InputEventKey.new(); event.keycode=key; event.pressed=true
		Input.parse_input_event(event)
	for i in range(5): await process_frame; await physics_frame
	check(scene.player.position==start,"Held gameplay keys cannot move body")
	check(not scene.inventory_drawer.visible and not scene.quest_busy and not scene.travelling,"Gameplay input cannot open panels or mutate world")
	scene.bag_button.pressed.emit()
	scene.quest_panel.start_requested.emit()
	scene.give_button.pressed.emit()
	check(not scene.inventory_drawer.visible and not scene.quest_busy,"Clickable gameplay callbacks stay gated")
	check(not scene.position_busy,"Position autosaves suppressed")
	check(not scene.ui.get_child(0).visible,"HUD hidden")
	check(not scene.player.visible,"Voyage uses visual proxy")
	check(scene.world_view.world_camera.position.distance_to(scene.player.position)>1000,"Gameplay follow cannot overwrite cinematic camera")
	for key in [KEY_W,KEY_E,KEY_F,KEY_I]:
		var event:=InputEventKey.new(); event.keycode=key; event.pressed=false; Input.parse_input_event(event)
	# Actual reset path while the voyage is hiding its HUD; emulate the server reply.
	scene._restart_game(); scene.world_request.cancel_request()
	payload.game_scope="replacement"
	scene._world_completed(0,200,PackedStringArray(),JSON.stringify(payload).to_utf8_buffer())
	scene.opening.set_process(false); scene.opening.fake=true; scene.opening.director.checkpoint_ready=true
	scene.opening.director.advance_clock(60,false)
	await process_frame; await process_frame
	check(scene.bag_button.is_visible_in_tree(),"New Game during voyage preserves baseline HUD at replacement handoff")
	# The old run may already be durably complete when a subsequent reset fails.
	scene._start_opening(); scene.opening.set_process(false); scene.opening.fake=true; scene.opening.director.checkpoint_ready=true
	scene.opening.director.advance_clock(88,false)
	await process_frame; await process_frame
	scene._restart_game(); scene.world_request.cancel_request()
	payload.opening_state="complete"; payload.player_position={"x":0,"y":3600}
	scene._world_completed(0,200,PackedStringArray(),JSON.stringify(payload).to_utf8_buffer())
	await process_frame; await process_frame
	check(not scene.cinematic and scene.player.visible and scene.player.control_enabled and not scene.player.get_child(0).scripted_mode,"Failed reset reconnect restores completed-run gameplay ownership")
	check(scene.bag_button.is_visible_in_tree(),"Failed reset reconnect restores normal HUD")
	# An older server has no opening capability; it must never create a session.
	scene._world_completed(0,200,PackedStringArray(),JSON.stringify({"player_inventory":["water"],"player_position":{"x":10.125,"y":50.875}}).to_utf8_buffer())
	check(not scene.cinematic and scene.player.position==Vector2(10.125,50.875),"Older backend snapshot follows gameplay without opening requests")
	scene.queue_free()
	await process_frame; await process_frame
	quit(1 if failures else 0)
