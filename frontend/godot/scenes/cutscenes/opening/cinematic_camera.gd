extends RefCounted
const T = preload("res://scenes/cutscenes/opening/opening_times.gd")
var base_position := Vector2.ZERO
var shake_offset := Vector2.ZERO
var reduced_motion := false
func sample_at(t: float) -> void:
	shake_offset=Vector2.ZERO
	if not reduced_motion and t>=T.CONTACT and t<T.SHAKE_END:
		var decay:=exp(-(t-T.CONTACT)*1.6)
		shake_offset=Vector2(sin(t*83),cos(t*71))*12*decay
func present(view: Node) -> void: view.follow(base_position+shake_offset)
