extends SceneTree
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var director=load("res://scenes/cutscenes/opening/opening_director.gd").new()
	var crash=load("res://scenes/cutscenes/opening/crash_fx.gd").new(); root.add_child(crash)
	var expected: Array[StringName]=[&"keel_contact",&"splinters",&"mast_break",&"deck_wash",&"player_fall"]
	director.cue.connect(func(id):
		if id in expected: crash.trigger(id))
	var failures:=0
	for fast in [false,true]:
		director.start(); crash.reset()
		director.advance_clock(18 if fast else 36,fast)
		if crash.fired!=expected: print("FAIL ordered crash events"); failures+=1
		for id in expected: crash.trigger(id)
		if crash.fired!=expected: print("FAIL repeat-safe bursts"); failures+=1
		crash.reset()
		if not crash.fired.is_empty(): failures+=1
	print("PASS ordered/repeat-safe crash effects at both rates" if not failures else "FAIL crash")
	director.free(); crash.queue_free(); await process_frame
	quit(1 if failures else 0)
