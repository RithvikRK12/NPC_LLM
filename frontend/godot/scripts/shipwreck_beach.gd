extends Node2D
const DATA = preload("res://resources/shipwreck_beach.tres")
var salvage_available := true
var debug_geometry := false
var ambience: AudioStreamPlayer
func marker(id: String) -> Vector2:
	var at: Array=DATA.data().markers[id]
	return Vector2(at[0],at[1])
func _ready() -> void:
	ambience=AudioStreamPlayer.new(); ambience.volume_db=-17
	if ResourceLoader.exists("res://assets/cutscene/opening/surf.wav"):
		ambience.stream=load("res://assets/cutscene/opening/surf.wav")
		if ambience.stream is AudioStreamWAV:
			ambience.stream.loop_begin=0
			ambience.stream.loop_end=int(ambience.stream.get_length()*ambience.stream.mix_rate)
			ambience.stream.loop_mode=AudioStreamWAV.LOOP_FORWARD
	add_child(ambience)
	for id in DATA.data().markers:
		var m:=Marker2D.new()
		m.name=id
		m.position=marker(id)
		add_child(m)
	for solid in DATA.data().solids:
		var body:=StaticBody2D.new()
		var collider:=CollisionShape2D.new()
		var shape:=RectangleShape2D.new()
		shape.size=Vector2(solid[2],solid[3])
		collider.shape=shape
		body.position=Vector2(solid[0],solid[1])+shape.size/2
		body.add_child(collider)
		add_child(body)
	var coast=preload("res://scenes/cutscenes/opening/coast_reveal.gd").new()
	coast.z_index=-40
	add_child(coast)
	var ship=preload("res://scenes/cutscenes/opening/sailing_ship.gd").new()
	ship.position=Vector2(DATA.data().coast_origin[0],DATA.data().coast_origin[1])
	ship.damage=3
	ship.show_proxy=false
	add_child(ship)
func _draw() -> void:
	for i in range(16):
		var at:=Vector2(-400+posmod(i*137,800),3560+posmod(i*71,240))
		if absf(at.x)<64: continue
		draw_rect(Rect2(at,Vector2(20,6)),Color("72503e"))
		draw_rect(Rect2(at+Vector2(4,0),Vector2(12,2)),Color("b38c58"))
	if salvage_available:
		var at:=marker("SupplyApproach")
		draw_rect(Rect2(at-Vector2(20,24),Vector2(40,24)),Color("765740"))
		draw_rect(Rect2(at-Vector2(16,20),Vector2(32,4)),Color("d4bd87"))
		draw_rect(Rect2(at-Vector2(16,10),Vector2(32,4)),Color("d4bd87"))
	if debug_geometry:
		for id in DATA.data().markers: draw_circle(marker(id),6,Color.YELLOW)

func set_ambience(enabled: bool) -> void:
	if enabled and ambience.stream and not ambience.playing: ambience.play()
	elif not enabled and ambience.playing: ambience.stop()
func adopt_ambience(voice: AudioStreamPlayer) -> void:
	if voice==null: return
	ambience.stop(); ambience.queue_free()
	ambience=voice
	if voice.get_parent()!=self: voice.reparent(self)
	# Real openings attach this voice to the beach before playback starts.
func _exit_tree() -> void:
	if is_instance_valid(ambience): ambience.stop(); ambience.stream=null
