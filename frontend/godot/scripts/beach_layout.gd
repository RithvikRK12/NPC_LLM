extends Resource
var _data: Dictionary = {}
func data() -> Dictionary:
	if _data.is_empty(): _data=JSON.parse_string(FileAccess.get_file_as_string("res://resources/shipwreck_beach.json"))
	return _data
