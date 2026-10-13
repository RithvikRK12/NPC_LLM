extends SceneTree
func _initialize() -> void:
	var layout=load("res://resources/village_layout.tres")
	var beach=load("res://resources/shipwreck_beach.tres").data()
	var failures:=0
	for id in beach.markers:
		var at: Array=beach.markers[id]
		if not layout.is_walkable(Vector2(at[0],at[1])): print("FAIL marker ",id); failures+=1
	for y in range(3552,3793,2):
		if not layout.is_walkable(Vector2(0,y)): print("FAIL recovery sweep ",y); failures+=1
	print("PASS all beach markers and swept recovery route" if failures==0 else "FAIL beach")
	quit(1 if failures else 0)
