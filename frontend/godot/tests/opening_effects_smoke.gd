extends SceneTree
var failures:=0
func check(ok: bool,label: String) -> void:
	print("PASS " if ok else "FAIL ",label)
	if not ok: failures+=1
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var preview=load("res://scenes/cutscenes/opening/OpeningPreview.tscn").instantiate(); root.add_child(preview)
	preview.session.set_process(false)
	var stage=preview.session.stage
	for t in [0.0,3.0,6.0,22.0,27.99]:
		stage.sample_at(t)
		check(stage.weather.coverage==1 and not stage.coast.visible and not stage.scenery.visible,"Opaque coast mask through %s" % t)
	stage.sample_at(29.5)
	check(stage.weather.coverage==0,"Coast fully uncovered at 29.5")
	var camera_y: float=stage.camera_rig.base_position.y
	check(camera_y-270<3840,"Shore inside minimum-height safe frame by 29.5")
	stage.sample_at(32.99); check(stage.ship.damage==0 and stage.ship.turn==1,"Failed turn before contact")
	for t in [33.0,34.2,35.4]:
		stage.sample_at(t); check(stage.ship.damage>0,"Damage staged at %s" % t)
	stage.reduced_motion=true; stage.sample_at(33.1)
	check(stage.camera_rig.shake_offset==Vector2.ZERO,"Reduced motion suppresses impact shake")
	stage.reset(); check(stage.crash.fired.is_empty() and stage.ship.damage==0,"Restart clears damage and crash effects")
	check(preview.session.audio.ambience.stream.loop_end>0 and preview.session.audio.wind.stream.loop_end>0,"Ambience loops cover the authored sample frames")
	preview.session.audio.sample_mix(41)
	check(preview.session.audio.silent and not preview.session.audio.ambience.playing,"Intentional blackout silence")
	preview.session.audio.sample_mix(42)
	check(preview.session.audio.ambience.playing,"Surf returns at 42")
	preview.session.audio.set_paused(true)
	check(preview.session.audio.ambience.stream_paused,"Pause freezes opening audio")
	preview.queue_free(); await process_frame; await process_frame
	quit(1 if failures else 0)
