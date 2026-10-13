# Native wall-clock verification; no real persistence. Defaults to held Space 2×.
extends SceneTree
func _initialize() -> void: call_deferred("run")
func run() -> void:
	root.size=Vector2i(1280,720)
	var preview=load("res://scenes/cutscenes/opening/OpeningPreview.tscn").instantiate(); root.add_child(preview)
	for i in range(10): await process_frame
	preview.director.set_focused(true); preview.director.start()
	var fast:=not OS.get_cmdline_user_args().has("--normal")
	if fast: Input.action_press("cutscene_fast_forward")
	var start:=Time.get_ticks_msec()
	while preview.session.active:
		await process_frame
		if Time.get_ticks_msec()-start>100000: push_error("Realtime playback timed out"); quit(1); return
	var seconds: float=(Time.get_ticks_msec()-start)/1000.0
	Input.action_release("cutscene_fast_forward")
	var expected:=30.0 if fast else 60.0
	var ok: bool=absf(seconds-expected)<0.75 and preview.director.time==60 and Engine.time_scale==1
	print("PASS " if ok else "FAIL ","Native wall playback: ",seconds," s; expected ",expected," s; endpoint ",preview.player.position)
	preview.queue_free(); await process_frame; await process_frame
	quit(0 if ok else 1)
