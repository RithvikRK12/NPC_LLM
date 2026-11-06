extends Node2D
const T = preload("res://scenes/cutscenes/opening/opening_times.gd")
var time := 0.0
var fired: Array[StringName] = []
var reduced_motion := false
func trigger(id: StringName) -> void:
	if not fired.has(id): fired.append(id)
func reset() -> void:
	fired.clear()
	time=0
	queue_redraw()
func sample_at(t: float) -> void:
	time=t
	queue_redraw()
func _draw() -> void:
	if time<T.CONTACT or time>=T.BLACKOUT: return
	var elapsed:=time-T.CONTACT
	for i in range(8 if reduced_motion else 32):
		var p:=Vector2(posmod(i*37,200)-100,-120)+Vector2(posmod(i*29,120)-60,-40-posmod(i*17,80))*minf(elapsed,2)
		p.y+=32*elapsed*elapsed
		if elapsed<2.5: draw_rect(Rect2((p/2).round()*2,Vector2(4+posmod(i,3)*2,8)),Color("c1a674") if i%3 else Color("a8d4cf"))
	if time>=T.WASH and time<T.WASH_END:
		for y in range(0,100,12): draw_rect(Rect2(-80,y-(time-T.WASH)*100,160,6),Color(0.65,0.83,0.81,0.65))
