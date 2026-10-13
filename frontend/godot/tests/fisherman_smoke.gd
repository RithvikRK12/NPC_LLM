extends SceneTree
var failures := 0
func check(ok: bool, message: String) -> void:
	if not ok:
		failures += 1
		push_error(message)
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var script = load("res://scripts/fisherman_encounter.gd")
	if script == null:
		check(false, "Fisherman encounter must exist")
		quit(1)
		return
	var encounter = script.new()
	encounter.state_path = "/tmp/fisherman-smoke.cfg"
	if FileAccess.file_exists(encounter.state_path): DirAccess.remove_absolute(encounter.state_path)
	root.add_child(encounter)
	var ui := Control.new()
	root.add_child(ui)
	ui.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	encounter.build_ui(ui)
	encounter.set_scope("test-run")
	check(not encounter.try_introduction(encounter.position + Vector2(321,0)), "Outside 10 meters must not trigger")
	check(encounter.try_introduction(encounter.position + Vector2(320,0)), "10 meters must trigger introduction")
	check(encounter.introducing and not encounter.panel.visible, "Introduction precedes dialogue")
	encounter.advance_intro(2.0)
	check(encounter.panel.visible and encounter.current_id == "F00", "Introduction opens F00")
	var endings := {}
	var opening: String = encounter.line.text
	for a in range(2):
		for b in range(2):
			for c in range(2):
				for choice in [a,b,c]:
					check(encounter.choices.get_child_count() == 2, "Exactly two choices at every branch")
					encounter.choose(choice)
				check(encounter.current_id.begins_with("E"), "Exactly three selections reach final reply")
				endings[encounter.current_id] = true
				check(encounter.choices.get_child_count() == 1 and encounter.choices.get_child(0).text == "Continue", "Final waits for Continue")
				encounter.continue_dialogue()
				check(not encounter.panel.visible and not encounter.owns_input(), "Continue closes final reply and releases input")
				encounter.open_dialogue()
				check(encounter.current_id == "F00" and encounter.line.text == opening, "New interaction repeats exact opening")
	check(endings.size() == 8, "All eight final replies reachable")
	encounter.choose(0)
	encounter.close_dialogue()
	check(not encounter.owns_input(), "Close releases player")
	check(not encounter.try_introduction(encounter.position), "Introduction never replays")
	encounter.open_dialogue()
	check(encounter.current_id == "F00", "Reopen starts at F00")
	encounter.set_scope("test-run")
	check(encounter.intro_seen, "Presentation flag survives reload")
	encounter.set_scope("new-run")
	check(not encounter.intro_seen, "New run resets presentation flag")
	check(ui.find_children("*", "LineEdit", true, false).is_empty(), "No free-form input")
	var scenery = load("res://resources/south_scenery.tres")
	check(scenery.blocked(Vector2(250,2250)), "Trunk remains solid")
	check(not scenery.blocked(Vector2(250,2290)), "Feet and approach remain clear")
	if OS.get_environment("FISHERMAN_RENDER") == "1":
		encounter.open_dialogue()
		await process_frame
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/fisherman-panel.png")
	encounter.queue_free(); ui.queue_free()
	await process_frame
	DirAccess.remove_absolute("/tmp/fisherman-smoke.cfg")
	print("Fisherman checks: ", failures, " failures")
	quit(1 if failures else 0)
