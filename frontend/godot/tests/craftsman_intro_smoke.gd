extends SceneTree
var failures := 0
func check(ok: bool, text: String) -> void:
	if not ok: failures+=1; push_error(text)
func _initialize() -> void: call_deferred("run")
func run() -> void:
	check(ResourceLoader.exists("res://scripts/craftsman_encounter.gd"),"Workshop encounter controller exists")
	if failures: quit(1); return
	var main = load("res://tests/fisherman_test_main.gd").new()
	root.add_child(main)
	main.world_request.cancel_request(); main.world_busy=false; main.world_loaded=true
	main.fisherman.intro_seen=true
	main.onboarding.visible=false
	main.player.position=Vector2(10000,10128)
	main.craftsman_activity.intro_seen=false
	check(main.craftsman_encounter.try_introduction(),"First workshop entry acquires approach")
	check(main.onboarding.completed,"Meeting the Craftsman satisfies finding someone for help")
	check(main.craftsman_encounter.owns_input(),"Introduction owns input")
	var start: Vector2=main.player.position
	for i in range(180): await physics_frame
	check(main.player.position.distance_to(start)>30,"Player actually walks toward Craftsman")
	check(main.craftsman_encounter.phase=="intro_dialogue","Approach reaches introduction")
	main.craftsman_encounter.cancel()
	check(not main.craftsman_encounter.owns_input(),"Cancellation restores control")
	check(not main.craftsman_activity.intro_seen,"Interrupted introduction remains pending")
	main.craftsman_activity.intro_seen=true
	check(not main.craftsman_encounter.try_introduction(),"Seen introduction does not replay")
	main.queue_free(); await process_frame
	print("Craftsman introduction: ",failures," failures"); quit(1 if failures else 0)
