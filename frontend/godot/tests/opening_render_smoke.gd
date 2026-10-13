extends SceneTree
var failures:=0
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var preview=load("res://scenes/cutscenes/opening/OpeningPreview.tscn").instantiate()
	root.add_child(preview)
	await process_frame
	preview.session.set_process(false)
	for child in preview.get_children():
		if child is CanvasLayer and child.layer==30:
			for control in child.get_child(0).get_children():
				if control!=preview.debug_label: control.hide()
	var directory:=ProjectSettings.globalize_path("res://../../docs/evidence/starting-cutscene/second-pass/")
	for size in [Vector2i(960,540),Vector2i(1280,720),Vector2i(1920,1080),Vector2i(2560,720)]:
		root.size=size
		await process_frame
		for t in [0.0,4.0,14.0,27.9,28.5,29.5,33.5,35.5,44.0,49.0,55.0,60.0]:
			preview.session.recovery_started=false
			preview.director.seek(t)
			for i in range(4): await process_frame; await physics_frame
			await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png(directory+"frame-%s-%04d.png" % [size.x,int(t*10)])
			if t==27.9 and preview.session.stage.weather.coverage!=1: failures+=1
			if t==29.5 and preview.session.stage.weather.coverage!=0: failures+=1
			print("CAPTURE S%02d %.2f at %s" % [preview.director.shot+1,t,size])
	root.size=Vector2i(1280,720)
	for effect in ["Ocean","Ship","Fog","Coast","Crash"]:
		preview.effect_mode=effect
		var t: float=34.5 if effect=="Crash" else (29.5 if effect=="Coast" else (14.0 if effect=="Fog" else 15.0))
		preview._seek_preview(t)
		for i in range(4): await process_frame
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png(directory+"standalone-%s-%04d.png" % [effect,int(t*10)])
	preview.queue_free()
	await process_frame
	quit(1 if failures else 0)
