extends SceneTree
func _initialize() -> void:
	var scenery=load("res://scripts/south_scenery.gd").new()
	# A trunk owned diagonally across a seam overlaps this actor's full foot box.
	# Set the authored chunk payload explicitly to exercise the corner geometry.
	scenery.cache[Vector2i(1,1)]=[scenery.entry("corner_trunk","palm",Vector2(1026,1026),0)]
	var ok: bool=scenery.blocked(Vector2(1020,1020))
	print("PASS " if ok else "FAIL ","Footprint validation includes diagonally owned seam obstacles")
	quit(0 if ok else 1)
