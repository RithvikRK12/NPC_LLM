extends SceneTree
var failures := 0
func check(ok: bool, message: String):
	print("PASS " if ok else "FAIL ",message)
	if not ok: failures+=1
func _initialize(): call_deferred("run")
func run():
	var scene=load("res://tests/fisherman_test_main.gd").new(); root.add_child(scene)
	scene.gatherer_encounter.phase="choice"
	scene.bag_button.pressed.emit()
	check(not scene.inventory_drawer.visible,"Encounter blocks Bag button")
	for button in scene.ui.find_children("*","Button",true,false):
		if button.text=="Quests": button.pressed.emit()
	check(not scene.quest_panel.visible,"Encounter blocks Quests button")
	scene.quest_panel.hide(); scene.gatherer_encounter.phase="combat"
	check(scene.ui_owns_input() and scene.gatherer_encounter.allows_movement(),"Combat reserves interactions while allowing movement")
	scene.gatherer_encounter.phase="choice"
	check(not scene.gatherer_encounter.allows_movement(),"Cinematic disables manual movement")
	scene.gatherer_encounter.phase=""
	scene.world_loaded=true; scene.fisherman.intro_seen=true; scene.craftsman_activity.intro_seen=true
	scene.gatherer_gateway.restore({"game_scope":"legacy"})
	scene.player.position=scene.gatherer_encounter.mark("PlayerTalkMark")
	scene.gatherer_encounter.capability_delay=10 # Do not dispatch network traffic in this input unit check.
	scene.gatherer_encounter.advance(0.1)
	check(not scene.gatherer_encounter.owns_input(),"Missing backend encounter state leaves exploration available")
	scene.queue_free(); await process_frame
	quit(1 if failures else 0)
