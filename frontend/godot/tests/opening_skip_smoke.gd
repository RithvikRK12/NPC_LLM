extends SceneTree
var failures := 0
func check(ok: bool, text: String) -> void:
	if not ok:
		failures += 1
		push_error(text)
func _initialize() -> void: call_deferred("run")
func frames() -> void:
	for i in range(4): await process_frame
func run() -> void:
	for t in [0.0,20.0,39.0,54.0]:
		var main = load("res://tests/fisherman_test_main.gd").new()
		root.add_child(main)
		main.onboarding.state_path = "/tmp/opening-skip-onboarding.cfg"
		DirAccess.remove_absolute(main.onboarding.state_path)
		var payload := {"opening_capability":1,"opening_state":"pending","game_scope":"skip-test","player_position":{"x":0,"y":0}}
		main._world_completed(0,200,PackedStringArray(),JSON.stringify(payload).to_utf8_buffer())
		var session = main.opening
		session.set_process(false)
		session.fake = true
		session.director.seek(t)
		var key := InputEventKey.new()
		key.keycode = KEY_L; key.pressed = true
		key.echo = true
		main._input(key)
		check(main.cinematic,"Key-repeat does not trigger a skip")
		key.echo = false
		main._open_menu()
		main._input(key)
		check(main.cinematic,"L does not bypass the open menu")
		main._resume_game()
		session.director.set_paused(false)
		main._input(key)
		# Skip should complete synchronously with an already available fake checkpoint.
		if main.cinematic:
			check(false,"L skips opening at %s" % t)
			main.queue_free(); await frames(); break
		check(main.player.position == main.beach.marker("ControlHandoff"),"Skip lands at beach handoff")
		check(not session.active and not session.stage.visible,"Skipped opening stops and hides stage")
		check(session.audio.fired.is_empty(),"Skip does not fire intervening crash cues")
		check(not main.travel_fade.visible and main.travel_fade.color.a == 0,"Skip removes blackout")
		check(main.player.velocity == Vector2.ZERO and not main.player.get_child(0).scripted_mode,"Skip restores idle player")
		check(main.onboarding.modal.visible,"Skip retains first-control popup")
		main.onboarding.dismiss()
		await frames()
		check(main.player.is_physics_processing(),"Dismissal enables normal gameplay")
		main._input(key)
		check(not main.cinematic,"L during gameplay does nothing")
		main.queue_free(); await frames()
	if failures:
		quit(1); return
	var main = load("res://tests/fisherman_test_main.gd").new()
	root.add_child(main)
	main.onboarding.state_path = "/tmp/opening-skip-onboarding.cfg"
	DirAccess.remove_absolute(main.onboarding.state_path)
	main._world_completed(0,200,PackedStringArray(),JSON.stringify({"opening_capability":1,"opening_state":"pending","game_scope":"skip-save","player_position":{"x":0,"y":0}}).to_utf8_buffer())
	var session = main.opening
	session.busy = true # Model an existing request awaiting acknowledgement.
	var key := InputEventKey.new(); key.keycode=KEY_L; key.pressed=true
	main._input(key)
	check(main.cinematic and not main.player.control_enabled,"Skip waits for arrival save")
	session._checkpoint_completed(0,500,PackedStringArray(),"{}".to_utf8_buffer())
	await frames()
	check(main.cinematic and session.retry.visible,"Save failure offers retry without releasing control")
	session.fake = true; session._checkpoint()
	await frames()
	check(not main.cinematic and main.player.position == main.beach.marker("ControlHandoff"),"Retry completes skipped handoff")
	main.queue_free(); await frames()
	DirAccess.remove_absolute("/tmp/opening-skip-onboarding.cfg")
	print("Opening skip checks: ",failures," failures")
	quit(1 if failures else 0)
