extends Node2D
const T = preload("res://scenes/cutscenes/opening/opening_times.gd")
var time := 0.0
var coverage := 1.0
var reduced_motion := false
var reduced_flashes := false
var center := Vector2.ZERO
var formations: Array[Texture2D] = []
func _ready() -> void:
	for i in range(7): formations.append(load("res://assets/cutscene/opening/fog-bank-%s.svg" % i))
func sample_at(t: float) -> void:
	time=t
	coverage=1.0-clampf((t-T.REVEAL)/(T.REVEALED-T.REVEAL),0,1)
	visible=t<T.BLACKOUT
	queue_redraw()
func reset() -> void: sample_at(0)
func _bank(at: Vector2, variant: int, depth: int) -> void:
	if formations.is_empty(): return
	var drift:=Vector2.ZERO if reduced_motion else Vector2(sin((time+30)*.065+variant)*16,cos((time+30)*.045+variant)*6)
	# Every source pixel is two world units, regardless of bank size or depth.
	var texture:=formations[posmod(variant,formations.size())]
	draw_texture_rect(texture,Rect2((at+drift).snapped(Vector2(2,2)),texture.get_size()*2),false,Color.WHITE.darkened(depth*.025))
func _draw() -> void:
	if coverage<=0: return
	var release:=1-coverage
	var withdraw:=release*2200
	# The far bank is opaque; its visible edge is buried under irregular silhouettes.
	# It extends beyond every supported viewport so lobe gaps cannot expose land.
	draw_rect(Rect2(center+Vector2(-20000,-20280-withdraw),Vector2(40000,20000)),Color("a2b6b8"))
	for row in range(-6,1):
		for column in range(-8,9):
			var seed:=posmod(column*73+row*37,101)
			var at:=center+Vector2(column*218+posmod(row*59,140)-100,row*115-310+seed%39-withdraw)
			at.x+=signf(column)*withdraw*.35
			_bank(at,seed,row%3)
	# Near banks frame the ship without washing out the readable deck.
	for side in [-1,1]:
		for row in range(-5,6):
			var seed:=posmod(row*43+side*19,97)
			var x:=130+seed%120+withdraw
			_bank(center+Vector2(x if side==1 else -x-384,row*108-60+seed%73),seed,2)
