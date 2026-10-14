extends SceneTree
var failures := 0
func check(ok: bool, text: String) -> void:
	if not ok: failures+=1; push_error(text)
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var gateway=load("res://scripts/craftsman_gateway.gd").new()
	root.add_child(gateway)
	var errors: Array[String]=[]
	gateway.failed.connect(func(message: String): errors.append(message))
	gateway.send_command("intro_complete")
	check(errors.size()==1,"Missing run scope reports failure instead of silently dropping the command")
	gateway.queue_free()
	var main=load("res://tests/fisherman_test_main.gd").new(); root.add_child(main)
	main.world_loaded=true; main.fisherman.intro_seen=true; main.craftsman_activity.intro_seen=true
	main.player.position=Vector2(10000,10128)
	main.craftsman_encounter.phase="intro_dialogue"; main.craftsman_encounter.beat=1
	main.craftsman_encounter.present(main.craftsman_encounter.lines.intro[1].text)
	main.craftsman_encounter.continue_button.pressed.emit()
	check(main.craftsman_encounter.phase=="intro_retry","Actual Continue button exposes recovery when the backend did not initialize the encounter")
	check(not main.craftsman_encounter.continue_button.disabled,"Retry remains enabled")
	check(not main.craftsman_encounter.owns_input(),"Missing backend capability restores player control")
	main.craftsman_encounter.skip_button.pressed.emit()
	check(main.craftsman_encounter.phase.is_empty(),"Actual Close/Skip button exits failed introduction safely")
	main.craftsman_gateway.restore({"game_scope":"legacy"})
	main.craftsman_encounter.phase="intro_dialogue"; main.craftsman_encounter.beat=1
	main.craftsman_encounter.skip_button.pressed.emit()
	check(main.craftsman_encounter.phase=="intro_retry","Legacy world without encounter capability produces an actionable retry")
	check(main.craftsman_encounter.line.text.to_lower().contains("restart"),"Legacy backend failure explains how to recover")
	main.craftsman_encounter.cancel(); main.queue_free(); await process_frame
	print("Craftsman backend compatibility: ",failures," failures"); quit(1 if failures else 0)
