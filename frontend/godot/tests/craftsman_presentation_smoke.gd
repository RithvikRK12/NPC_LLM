extends SceneTree
var failures := 0
func check(ok: bool, message: String) -> void:
	if not ok: failures+=1; push_error(message)
func _initialize() -> void: call_deferred("run")
func run() -> void:
	root.size=Vector2i(1280,720)
	var main=load("res://tests/fisherman_test_main.gd").new(); root.add_child(main)
	main.world_loaded=true; main.fisherman.intro_seen=true; main.craftsman_activity.intro_seen=true
	main.player.position=Vector2(-32,3632); main.npc_nodes[1].position=Vector2(32,3632)
	main.craftsman_activity.overridden=true; main.craftsman_encounter.phase="inspection_dialogue"
	main.craftsman_encounter.present("Inspection")
	await process_frame; await process_frame
	check(main.world_view.world_to_screen(Vector2(0,3944)).y<main.craftsman_encounter.panel.position.y*main.ui.scale.y,"Inspection frames the hull above the dialogue panel")
	main.craftsman_encounter.cancel()
	var materials: Array=[]
	for item in ["Sound timber plank","Coil of rope","Bundle of sailcloth","Pot of pitch"]:
		materials.append({"name":item,"required":12.0,"contributed":0.0})
	main.quest_panel.set_ship_state({"phase":"gathering_materials","materials":materials,"objective":"Gather the materials and bring them to the Craftsman's workshop.","availability_note":"Material gathering and ship repair will be added in a later update."},{"mode":"returning_to_workshop"})
	for size in [Vector2i(960,540),Vector2i(1280,720)]:
		root.size=size; main.quest_panel.show()
		await process_frame; await process_frame
		check(main.quest_panel.get_global_rect().end.y<=main.ui.size.y,"Journal fits viewport height at "+str(size))
	check(not main.quest_panel.ship_objective.text.contains("0.0 /"),"Material counts display as whole quantities")
	main.queue_free(); await process_frame
	print("Craftsman presentation: ",failures," failures"); quit(1 if failures else 0)
