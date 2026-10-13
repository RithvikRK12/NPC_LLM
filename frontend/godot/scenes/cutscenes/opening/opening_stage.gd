extends Node2D
const T = preload("res://scenes/cutscenes/opening/opening_times.gd")
var time := 0.0
var reduced_motion := false
var reduced_flashes := false
var ocean: Node2D
var coast: Node2D
var scenery: Node2D
var ship: Node2D
var weather: Node2D
var crash: Node2D
var shot: Node
var camera_rig = preload("res://scenes/cutscenes/opening/cinematic_camera.gd").new()
const BEACH = preload("res://resources/shipwreck_beach.tres")
var ship_at := Vector2.ZERO
func _ready() -> void:
	z_index=100
	ocean=preload("res://scenes/cutscenes/opening/ocean_backdrop.gd").new(); ocean.z_index=-20; add_child(ocean)
	coast=preload("res://scenes/cutscenes/opening/coast_reveal.gd").new(); coast.z_index=-10; add_child(coast)
	scenery=Node2D.new(); scenery.y_sort_enabled=true; add_child(scenery)
	var shared=preload("res://resources/south_scenery.tres")
	for y in range(2,5):
		for x in range(-3,3):
			for item in shared.entries_for_chunk(Vector2i(x,y)):
				var prop=preload("res://scripts/south_prop.gd").new(); prop.item=item; prop.solid=false; scenery.add_child(prop)
	ship=preload("res://scenes/cutscenes/opening/sailing_ship.gd").new()
	add_child(ship)
	crash=preload("res://scenes/cutscenes/opening/crash_fx.gd").new()
	add_child(crash)
	weather=preload("res://scenes/cutscenes/opening/weather_fx.gd").new()
	add_child(weather)
	shot=preload("res://scenes/cutscenes/opening/opening_shot.gd").new()
	add_child(shot)
func sample_at(t: float) -> void:
	time=t
	visible=t<T.BLACKOUT
	coast.visible=t>=T.REVEAL
	scenery.visible=t>=T.REVEAL
	var travel:=500*clampf((t-T.REVEAL)/2,0,1)+200*clampf((t-T.TURN)/3,0,1)
	ship_at=Vector2(-24*sin(clampf((t-T.TURN)/3,0,1)*PI),BEACH.data().coast_origin[1]+700-travel)
	var bob:=0.0 if reduced_motion else sin((t+30)*1.1)*2+sin((t+30)*0.73)*2
	ship.position=(ship_at/2).round()*2+Vector2(0,bob)
	ship.rotation=0.0 # Authored alternate heading preserves pixel clusters.
	ship.modulate=Color.WHITE * lerpf(0.82 if reduced_flashes else 0.65,1.0,clampf((t-T.REVEAL)/1.5,0,1))
	ship.modulate.a=1
	ship.sample_at(t)
	ocean.bend=clampf((t-T.TURN)/3,0,1)
	ocean.center=ship_at; ocean.reduced_flashes=reduced_flashes; ocean.sample_at(t)
	crash.position=ship_at
	crash.reduced_motion=reduced_motion
	crash.sample_at(t)
	weather.center=ship_at
	weather.reduced_motion=reduced_motion
	weather.reduced_flashes=reduced_flashes
	weather.sample_at(t)
	shot.sample_at(t)
	camera_rig.reduced_motion=reduced_motion
	camera_rig.base_position=ship_at+(Vector2(0,-100) if reduced_motion else shot.camera_offset)
	camera_rig.sample_at(t)
	queue_redraw()
func reset() -> void:
	crash.reset()
	shot.reset()
	sample_at(0)
