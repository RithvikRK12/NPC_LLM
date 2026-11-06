extends Node
const T = preload("res://scenes/cutscenes/opening/opening_times.gd")
signal completed
var view: Node
var player: CharacterBody2D
var beach: Node2D
var fade: ColorRect
var director: Node
var stage: Node2D
var audio: Node
var presentation_layer: CanvasLayer
var hint: Label
var retry: Button
var backend_url := ""
var game_scope := ""
var fake := true
var busy := false
var checkpoint_error := ""
var request: HTTPRequest
var desired_position := Vector2.ZERO
var recovery_started := false
var recovery_failed := false
var active := true
var skipping := false
var forced_rate := false
var reduced_motion := false
var reduced_flashes := false
var captions := false
var last_caption := ""
func configure(world_view: Node, body: CharacterBody2D, shore: Node2D, overlay: ColorRect) -> void:
	view=world_view; player=body; beach=shore; fade=overlay
func _ready() -> void:
	director=preload("res://scenes/cutscenes/opening/opening_director.gd").new()
	add_child(director)
	stage=preload("res://scenes/cutscenes/opening/OpeningStage.tscn").instantiate()
	view.world.add_child(stage)
	audio=preload("res://scenes/cutscenes/opening/opening_audio.gd").new()
	if not fake: audio.ambience_owner=beach # Never reparent a playing stream at handoff.
	add_child(audio)
	var layer:=CanvasLayer.new(); layer.layer=25; add_child(layer)
	presentation_layer=layer
	hint=Label.new(); hint.position=Vector2(24,24); layer.add_child(hint)
	retry=Button.new(); retry.text="Retry checkpoint"; retry.position=Vector2(24,64); layer.add_child(retry)
	hint.add_theme_font_size_override("font_size",23)
	retry.add_theme_font_size_override("font_size",23)
	get_viewport().size_changed.connect(_resize_presentation)
	_resize_presentation()
	retry.hide(); retry.pressed.connect(_checkpoint)
	request=HTTPRequest.new(); request.timeout=8; add_child(request)
	request.request_completed.connect(_checkpoint_completed)
	director.checkpoint_ready=fake
	director.sampled.connect(_sample)
	director.cue.connect(_cue)
	director.completed.connect(_finish)
	player.set_control_enabled(false)
	player.velocity=Vector2.ZERO; player.hide(); player.set_physics_process(false)
	player.get_child(0).set_scripted_mode(true)
	var error:=validate_preparation()
	if not error.is_empty():
		active=false; stage.hide(); fade.show(); fade.color.a=1
		hint.text=error+" · Esc → Quit; restore the required beach data."
		return
	director.start()
func validate_preparation() -> String:
	for id in ["RecoveryStart","HullExit","ControlHandoff","SafeFallback","InlandRoute","SupplyApproach"]:
		if not beach.has_node(id): return "Missing beach marker: "+id
		if not preload("res://resources/village_layout.tres").is_walkable(beach.marker(id)): return "Blocked beach marker: "+id
	return ""
func _process(delta: float) -> void:
	if not active: return
	if skipping:
		audio.set_paused(director.paused or not director.focused or not director.checkpoint_ready)
		if director.checkpoint_ready and not director.paused and director.focused:
			_finish()
			return
		hint.text = "Saving arrival…" if busy else checkpoint_error
		hint.show()
		retry.visible = not busy and not checkpoint_error.is_empty()
		return
	director.advance_clock(delta,forced_rate or Input.is_action_pressed("cutscene_fast_forward"))
	if not active: return
	audio.set_paused(director.paused or not director.focused or director.waiting)
	var black: bool=director.time>=T.BLACKOUT and director.time<T.FADE_IN
	var binding: String=InputMap.action_get_events("cutscene_fast_forward")[0].as_text().replace(" (Physical)","")
	hint.text="Hold %s · 2×   L · Skip   Esc · Menu" % binding if director.time<12 else ("2×   L · Skip" if director.rate==2 else "L · Skip")
	if captions and not last_caption.is_empty(): hint.text+="\n"+last_caption
	if director.waiting: hint.text="Saving arrival…" if busy else checkpoint_error
	hint.visible=not black
	retry.visible=director.waiting and not busy and not checkpoint_error.is_empty()
func _sample(t: float) -> void:
	stage.reduced_motion=reduced_motion; stage.reduced_flashes=reduced_flashes
	stage.sample_at(t)
	audio.sample_mix(t)
	fade.visible=t>=T.FADE_OUT and t<T.FADE_IN_END
	fade.color.a=clampf((t-T.FADE_OUT)/1.5,0,1) if t<T.FADE_IN else 1-clampf((t-T.FADE_IN)/2,0,1)
	fade.mouse_filter=Control.MOUSE_FILTER_IGNORE
	if t<T.BLACKOUT:
		player.hide()
		stage.camera_rig.present(view)
	else:
		if not recovery_started:
			recovery_started=true
			player.position=beach.marker("RecoveryStart")
		player.show()
		desired_position=path_at(t)
		var pose: StringName=&"recover" if t<T.BRACE else (&"brace" if t<T.STAND else (&"stand" if t<T.CLIMB else (&"climb_out" if t<T.CHECKPOINT else (&"walk_up" if t<T.END else &"idle_up"))))
		player.get_child(0).play_scripted(pose,int((t-T.CHECKPOINT)*8) if t>=T.CHECKPOINT else 0)
		var align:=clampf((t-T.RECOVER)/10.8,0,1)
		view.follow((beach.marker("RecoveryStart")+Vector2(40,-32)).lerp(desired_position,align))
func path_at(t: float) -> Vector2:
	if recovery_failed: return beach.marker("SafeFallback")
	if t<T.CLIMB: return beach.marker("RecoveryStart")
	if t<T.CHECKPOINT: return beach.marker("RecoveryStart").lerp(beach.marker("HullExit"),clampf((t-T.CLIMB)/3,0,1))
	return beach.marker("HullExit").lerp(beach.marker("ControlHandoff"),clampf((t-T.CHECKPOINT)/3,0,1))
func _physics_process(_delta: float) -> void:
	if not active or not recovery_started: return
	# Swept physics movement; input remains disabled. Bounded fallback prevents a trapped exit.
	var motion:=desired_position-player.position
	if motion.length()>0.001:
		var collision:=player.move_and_collide(motion)
		if collision:
			recovery_failed=true
			player.position=beach.marker("SafeFallback"); desired_position=player.position
func _cue(id: StringName) -> void:
	stage.crash.trigger(id)
	audio.trigger(id)
	if id==&"keel_contact": last_caption="[Hull strikes rock]"
	elif id==&"deck_wash": last_caption="[Water rushes over the deck]"
	elif id==&"blackout": last_caption=""
	elif id==&"checkpoint": _checkpoint()
func _checkpoint() -> void:
	if fake: director.checkpoint_ready=true; return
	if busy: return
	busy=true; checkpoint_error=""
	var error:=request.request(backend_url+"/world/opening/complete",PackedStringArray(["Content-Type: application/json"]),HTTPClient.METHOD_POST,JSON.stringify({"game_scope":game_scope,"opening_version":1}))
	if error!=OK: busy=false; checkpoint_error="Could not save arrival. Retry or Esc → Quit."
func _checkpoint_completed(result: int,code: int,_headers: PackedStringArray,body: PackedByteArray) -> void:
	busy=false
	if not active: return
	var data: Variant=JSON.parse_string(body.get_string_from_utf8())
	if result==HTTPRequest.RESULT_SUCCESS and code==200 and data is Dictionary and data.get("game_scope")==game_scope:
		director.checkpoint_ready=true; checkpoint_error=""
	else: checkpoint_error="Could not save arrival. Retry or Esc → Quit." if code!=409 else "Game changed. Esc → Quit and relaunch."
func skip() -> void:
	if not active or skipping: return
	skipping = true
	director.running = false
	director.time = T.END
	director.rate = 1
	director.waiting = not director.checkpoint_ready
	# Present the actual beach immediately without sampling intervening shots
	# or emitting their crash/audio cues. Keep control locked until saved.
	audio.reset()
	audio.sample_mix(T.END)
	stage.hide()
	fade.hide(); fade.color.a = 0
	recovery_started = true
	recovery_failed = false
	desired_position = beach.marker("ControlHandoff")
	player.position = desired_position
	player.velocity = Vector2.ZERO
	player.show()
	player.get_child(0).play_scripted(&"idle_up")
	view.follow(player.position)
	if not director.checkpoint_ready: _checkpoint()
	if director.checkpoint_ready and not director.paused and director.focused: _finish()

func _finish() -> void:
	if not active: return
	skipping = false
	director.running = false
	director.waiting = false
	audio.set_paused(false)
	player.position=beach.marker("ControlHandoff") if not recovery_failed and preload("res://resources/village_layout.tres").is_walkable(beach.marker("ControlHandoff")) else beach.marker("SafeFallback")
	player.velocity=Vector2.ZERO
	player.set_control_enabled(true)
	player.get_child(0).set_facing(&"up")
	player.get_child(0).set_scripted_mode(false)
	view.follow(player.position)
	fade.hide(); fade.color.a=0
	stage.hide(); hint.hide(); retry.hide()
	if not fake: stage.queue_free()
	audio.finish()
	active=false
	completed.emit()
func cancel() -> void:
	skipping=false
	active=false
	director.cancel(); audio.reset()
	if is_instance_valid(stage):
		stage.camera_rig.shake_offset=Vector2.ZERO
		stage.hide()
	hint.hide(); retry.hide(); fade.hide()
	player.velocity=Vector2.ZERO
func _notification(what: int) -> void:
	if director==null: return
	if what==NOTIFICATION_APPLICATION_FOCUS_OUT: director.set_focused(false)
	elif what==NOTIFICATION_APPLICATION_FOCUS_IN: director.set_focused(true)
func _exit_tree() -> void:
	if is_instance_valid(stage): stage.queue_free()

func _resize_presentation() -> void:
	presentation_layer.scale=Vector2.ONE*preload("res://scripts/ui_scaling.gd").factor(get_viewport().get_visible_rect().size)
