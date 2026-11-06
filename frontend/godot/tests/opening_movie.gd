# Native Godot Movie Maker. This harness has fake persistence only.
extends SceneTree
func _initialize() -> void: call_deferred("run")
func run() -> void:
	root.size=Vector2i(960,540) if OS.get_cmdline_user_args().has("--small") else Vector2i(1280,720)
	var preview=load("res://scenes/cutscenes/opening/OpeningPreview.tscn").instantiate(); root.add_child(preview)
	preview.session.set_process(false)
	preview.set_process_unhandled_input(false)
	var fast:=OS.get_cmdline_user_args().has("--fast")
	var mixed:=OS.get_cmdline_user_args().has("--mixed")
	preview.session.reduced_motion=OS.get_cmdline_user_args().has("--reduced")
	preview.session.captions=true
	# Hide preview widgets while retaining a shot/time watermark in the recording.
	for child in preview.get_children():
		if child is CanvasLayer and child.layer==30:
			for control in child.get_child(0).get_children():
				if control!=preview.debug_label: control.hide()
	preview.director.start()
	var frames:=0
	var started:=Time.get_ticks_msec()
	var max_frame_us:=0
	while preview.director.running:
		await process_frame
		# Movie Maker is an offline timeline render, independent of desktop focus.
		# Native wall-clock and lifecycle tests cover actual focus/pause behavior.
		if not preview.director.focused: preview.director.set_focused(true)
		preview.director.set_paused(false)
		preview.director.advance_clock(0,false)
		var before:=Time.get_ticks_usec()
		preview.director.advance_clock(1.0/30,fast or (mixed and frames%120<60))
		max_frame_us=maxi(max_frame_us,Time.get_ticks_usec()-before)
		frames+=1
		if frames>3100: push_error("Movie clock stalled"); quit(1); return
	for i in range(30): await process_frame
	print("MOVIE frames=",frames," simulated seconds=",frames/30.0," generation ms=",Time.get_ticks_msec()-started," max sample us=",max_frame_us)
	preview.queue_free(); await process_frame; await process_frame
	quit()
