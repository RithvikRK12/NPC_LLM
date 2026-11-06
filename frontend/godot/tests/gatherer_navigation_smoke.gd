extends SceneTree
var failures := 0
func check(value: bool, label: String):
	print('PASS ' if value else 'FAIL ',label)
	if not value: failures+=1
func _initialize():
	var path='res://resources/gatherer_encounter.json'
	check(FileAccess.file_exists(path),'Gatherer staging resource exists')
	if not FileAccess.file_exists(path): quit(1); return
	var data=JSON.parse_string(FileAccess.get_file_as_string(path))
	var layout=load('res://resources/village_layout.tres')
	var router=load('res://scripts/actor_router.gd').new()
	check(data.marks.GathererMark[0]<=-1600,'Gatherer clearing lies deep inside expanded forest')
	var forest=JSON.parse_string(FileAccess.get_file_as_string('res://resources/forest_layout.json'))
	check(forest.scenery.size()>=150,'Expanded forest has dense collision-backed scenery')
	for name in data.marks:
		var at=Vector2(data.marks[name][0],data.marks[name][1])
		check(router.point_clear(at,layout),name+' clears actor feet')
	var talk=Vector2(data.marks.PlayerTalkMark[0],data.marks.PlayerTalkMark[1])
	var region=Rect2(data.ForestEntryRegion[0],data.ForestEntryRegion[1],data.ForestEntryRegion[2],data.ForestEntryRegion[3])
	for entry in [Vector2(region.end.x-1,70),Vector2(-1800,region.position.y+1),Vector2(-1800,region.end.y-1),Vector2(region.position.x+1,70)]:
		entry=layout.recover_position(entry)
		check(not router.find_path(entry,talk,layout).is_empty(),'Routed forest approach '+str(entry))
	var retreat=data.marks.VillageReturnMark
	check(not router.find_path(talk,Vector2(retreat[0],retreat[1]),layout).is_empty(),'Refusal retreat route')
	var b=data.CombatBounds
	for y in range(b[1],b[1]+b[3]+1,8):
		for x in range(b[0],b[0]+b[2]+1,8):
			if not router.point_clear(Vector2(x,y),layout): check(false,'Arena obstruction '+str(Vector2(x,y)))
	print('Gatherer navigation failures: ',failures)
	quit(1 if failures else 0)
