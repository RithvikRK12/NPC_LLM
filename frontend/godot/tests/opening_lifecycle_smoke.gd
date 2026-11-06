extends SceneTree
var failures:=0
func check(ok: bool,label: String) -> void:
	print("PASS " if ok else "FAIL ",label)
	if not ok: failures+=1
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var preview=load("res://scenes/cutscenes/opening/OpeningPreview.tscn").instantiate(); root.add_child(preview)
	preview.session.set_process(false)
	var session=preview.session
	var d=session.director
	d.advance_clock(20,true)
	session._notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	d.advance_clock(10,true)
	check(d.time==40 and d.rate==1,"Focus notification pauses acceleration")
	session._notification(Node.NOTIFICATION_APPLICATION_FOCUS_IN)
	d.advance_clock(1,true)
	check(d.time==41,"Focus return does not resume stale hold")
	d.set_paused(true); d.advance_clock(1,false); d.set_paused(false); d.advance_clock(1,true)
	check(d.time==43,"Release while paused enables a fresh press")
	for t in [33.0,33.3,34.2,35.0,35.4,39.0]:
		d.start(); d.advance_clock(t,false); session.cancel()
		check(not d.running and not preview.player.control_enabled,"Cancel at %s keeps actor locked" % t)
		preview.restart()
		check(d.time==0 and session.stage.ship.damage==0 and session.audio.fired.is_empty(),"Restart after %s resets effects and cues" % t)
	# Simulate delayed/lost acknowledgment. Story time stops but normal clock is untouched.
	d.start(); d.checkpoint_ready=false
	session.fake=false; session.backend_url="http://127.0.0.1:1"
	d.advance_clock(60,false)
	check(is_equal_approx(d.time,59.8) and d.waiting and not preview.player.control_enabled,"Readiness barrier retains control")
	session.request.cancel_request(); session.busy=false; session.checkpoint_error="Retry arrival"
	d.advance_clock(30,true)
	check(is_equal_approx(d.time,59.8),"Waiting timeout cannot be accelerated")
	for code in [KEY_W,KEY_SPACE]:
		var event:=InputEventKey.new(); event.physical_keycode=code; event.keycode=code; event.pressed=true; Input.parse_input_event(event)
	Input.flush_buffered_events()
	session.fake=true; session._checkpoint()
	d.advance_clock(.2,false)
	check(d.time==60 and not session.active and preview.player.control_enabled,"Retry acknowledgment releases final step exactly once")
	check(preview.player.position==preview.beach.marker("ControlHandoff"),"Held WASD lands at exact endpoint before next physics tick")
	for i in range(12): await physics_frame
	check(preview.player.position.y<3600 and preview.player.velocity.length()<=180.01,"Held WASD starts normal-speed movement only after handoff")
	for code in [KEY_W,KEY_SPACE]:
		var event:=InputEventKey.new(); event.physical_keycode=code; event.keycode=code; event.pressed=false; Input.parse_input_event(event)
	Input.flush_buffered_events()
	check(Engine.time_scale==1,"Lifecycle never changes global time scale")
	preview.queue_free(); await process_frame; await process_frame
	quit(1 if failures else 0)
