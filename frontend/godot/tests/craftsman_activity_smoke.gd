extends SceneTree
func _initialize() -> void: call_deferred("run")
func run() -> void:
	if not ResourceLoader.exists("res://scripts/craftsman_activity.gd"):
		push_error("Workshop routine and follow controller are missing"); quit(1); return
	var main = load("res://tests/fisherman_test_main.gd").new()
	root.add_child(main)
	main.world_request.cancel_request(); main.world_busy=false; main.world_loaded=true
	main.fisherman.intro_seen=true
	var activity = main.craftsman_activity
	activity.intro_seen=true
	main.player.position=Vector2(10000,10128)
	activity.last_work=0 # Avoid a first destination only 16 units from the initial standing point.
	activity.idle_left=0
	var start: Vector2=activity.actor.position
	for i in range(120): await physics_frame
	if activity.actor.position.distance_to(start)<20:
		push_error("Craftsman did not physically walk between work points"); quit(1); return
	main.chat_windows[1].open_chat()
	start=activity.actor.position
	for i in range(30): await physics_frame
	if activity.actor.position!=start: push_error("Conversation failed to pause routine"); quit(1); return
	main.queue_free(); await process_frame
	print("Craftsman activity: 0 failures"); quit()
