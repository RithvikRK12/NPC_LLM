extends Node2D
const T = preload("res://scenes/cutscenes/opening/opening_times.gd")
var time:=0.0
var reduced_motion:=false
var reduced_flashes:=false
var center:=Vector2.ZERO
var sailing:=true
var bend:=0.0
func sample_at(t: float) -> void: time=t; queue_redraw()
func reset() -> void: sample_at(0)
func _draw() -> void:
	var daylight:=clampf((time-T.REVEAL)/1.5,0,1)
	var dark:=Color("344f60") if not reduced_flashes else Color("3c6470")
	draw_rect(Rect2(center-Vector2(20000,20000),Vector2(40000,40000)),dark.lerp(Color("2c7b82"),daylight))
	for y in range(int(center.y/64)-14,int(center.y/64)+15):
		for x in range(-18,19):
			var drift:=fmod((time+30)*28,64)
			var p:=Vector2(x*112+posmod(y*23,100),y*64+drift).snapped(Vector2(2,2))
			draw_rect(Rect2(p,Vector2(22,2)),Color("6e9ba3"))
			draw_rect(Rect2(p+Vector2(6,4),Vector2(12,2)),Color("426b7a"))
	if sailing:
		for i in range(12):
			var y: float=center.y+140+i*18+fmod((time+30)*35,18)
			var spread: float=50+i*5
			draw_rect(Rect2(center.x-spread+bend*i*4,y,16,4),Color("9abdb9"))
			draw_rect(Rect2(center.x+spread-16+bend*i*4,y,16,4),Color("9abdb9"))
