extends Node
# Each shot owns one manually advanced, non-looping property animation.
var camera_offset := Vector2.ZERO
var animation_player: AnimationPlayer
var index := -1
var local_time := 0.0
const OFFSETS = [Vector2(-31.42857,-16),Vector2(-70,20),Vector2(0,-100),Vector2(0,-140),Vector2(0,-150),Vector2(0,-100),Vector2.ZERO,Vector2(40,-80),Vector2(0,-24),Vector2.ZERO,Vector2.ZERO]
const TIMING = preload("res://resources/cutscenes/opening_timing.tres")
func _ready() -> void:
	animation_player=AnimationPlayer.new()
	animation_player.callback_mode_process=AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	add_child(animation_player)
	var library:=AnimationLibrary.new()
	for i in range(TIMING.boundaries.size()-1):
		var anim:=Animation.new()
		anim.length=TIMING.boundaries[i+1]-TIMING.boundaries[i]
		var track:=anim.add_track(Animation.TYPE_VALUE)
		anim.track_set_path(track,NodePath(".:camera_offset"))
		anim.track_insert_key(track,0.0,OFFSETS[i])
		anim.track_insert_key(track,anim.length,OFFSETS[i+1])
		library.add_animation(StringName("S%02d" % (i+1)),anim)
	animation_player.add_animation_library(&"",library)
func sample_at(t: float) -> void:
	var i: int=TIMING.shot_at(t)
	if index!=i:
		index=i
		animation_player.play(StringName("S%02d" % (i+1)))
		animation_player.seek(0,true)
		local_time=0
	var next: float=t-TIMING.boundaries[i]
	if next>=local_time: animation_player.advance(next-local_time)
	else: animation_player.seek(next,true)
	local_time=next
func advance(delta: float) -> void: animation_player.advance(delta)
func reset() -> void:
	index=-1
	animation_player.stop()
	camera_offset=Vector2.ZERO
