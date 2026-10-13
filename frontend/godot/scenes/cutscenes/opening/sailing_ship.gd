extends Node2D
const T = preload("res://scenes/cutscenes/opening/opening_times.gd")
var damage := 0
var time := 0.0
var show_proxy := true
var reduced_motion := false
var turn := 0
var proxy: Node2D
var textures: Array[Texture2D] = []
var mast_frames: Array[Texture2D] = []
func _ready() -> void:
	for d in range(4):
		for heading in range(2): textures.append(load("res://assets/cutscene/opening/ship-%s-%s.svg" % [d,heading]))
	for i in range(5): mast_frames.append(load("res://assets/cutscene/opening/mast-fall-%s.svg" % i))
	proxy=preload("res://scripts/person.gd").new()
	add_child(proxy)
	proxy.position=Vector2(30,34)
	proxy.visible=show_proxy
func sample_at(t: float) -> void:
	time=t
	damage=3 if t>=T.FALL else (2 if t>=T.MAST else (1 if t>=T.CONTACT else 0))
	turn=1 if t>=T.TURN and t<T.BLACKOUT else 0
	proxy.visible=show_proxy
	proxy.set_scripted_mode(true)
	proxy.play_scripted(&"fall" if t>=T.FALL else (&"brace" if t>=T.UNEASE else &"idle_up"))
	queue_redraw()
func _draw() -> void:
	if textures.size()==8:
		draw_texture_rect(textures[damage*2+turn],Rect2(-160,-164,320,384),false)
		if damage==2: draw_texture_rect(mast_frames[clampi(int((time-T.MAST)*5),0,4)],Rect2(-160,-164,320,384),false)
