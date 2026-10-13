extends SceneTree
func _initialize() -> void:
	var village=load("res://scripts/village.gd").new()
	var ok: bool=village.path_distance(Vector2(0,940))<46 and village.path_distance(Vector2(0,600))<46 and village.path_distance(Vector2(-112,300))<46
	print("PASS " if ok else "FAIL ","Southern route remains visually connected through village-owned terrain")
	village.free(); quit(0 if ok else 1)
