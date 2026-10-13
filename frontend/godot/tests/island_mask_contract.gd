extends SceneTree
func _initialize() -> void:
	var layout=load("res://resources/island_layout.tres")
	var mask:=PackedByteArray()
	for y in range(-192,192):
		for x in range(-256,256): mask.append(1 if layout.land_cell(Vector2i(x,y)) else 0)
	var file:=FileAccess.open("/tmp/island-godot-mask.bin",FileAccess.WRITE)
	file.store_buffer(mask); file.close()
	var hash:=HashingContext.new(); hash.start(HashingContext.HASH_SHA256); hash.update(mask)
	var digest:=hash.finish().hex_encode()
	var ok: bool=digest==layout.data().mask_sha256
	print("PASS " if ok else "FAIL ","All 196608 land cells match shared mask contract: ",digest)
	quit(0 if ok else 1)
