extends SceneTree
var failures := 0
func check(ok: bool, text: String) -> void:
	if not ok: failures+=1; push_error(text)
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var main = load("res://tests/fisherman_test_main.gd").new(); root.add_child(main)
	main.world_loaded=true; main.fisherman.intro_seen=true
	main.craftsman_activity.intro_seen=true
	main.player.position=Vector2(0,3504)
	var activity=main.craftsman_activity
	activity.outing_active=true; activity.mode="following_player"; activity.space="exterior"
	activity.actor.position=Vector2(0,3000)
	check(not main.craftsman_encounter.try_inspection(),"Player alone cannot trigger inspection")
	activity.actor.position=Vector2(64,3480)
	check(main.craftsman_encounter.try_inspection(),"Both actors near wreck trigger recognition")
	check(main.craftsman_encounter.phase=="inspection_recognition","Recognition precedes approach")
	main.craftsman_encounter.continue_scene()
	for i in range(180): await physics_frame
	check(main.craftsman_encounter.phase=="inspection_dialogue","Both physical approaches finish")
	check(main.player.position.distance_to(Vector2(-32,3632))<2,"Player reaches distinct mark")
	check(activity.actor.position.distance_to(Vector2(32,3632))<2,"Craftsman reaches distinct mark")
	check(main.village.layout.is_walkable(main.player.position) and main.village.layout.is_walkable(activity.actor.position),"Both actors remain outside hull collision")
	check(main.quest_panel.has_method("set_ship_state"),"Main quest has independent journal presentation")
	main.craftsman_encounter.cancel(); main.queue_free(); await process_frame
	print("Craftsman inspection: ",failures," failures"); quit(1 if failures else 0)
