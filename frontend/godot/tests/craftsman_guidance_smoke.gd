extends SceneTree
var failures := 0
func check(ok: bool, text: String) -> void:
	print("PASS " if ok else "FAIL ",text)
	if not ok: failures+=1
func capture(label: String) -> void:
	var directory := OS.get_environment("GUIDANCE_CAPTURE_DIR")
	if directory.is_empty() or DisplayServer.get_name()=="headless": return
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(directory.path_join(label+".png"))
func _initialize() -> void: call_deferred("run")
func snapshot(scope: String, revision: int, active: bool) -> Dictionary:
	return {"game_scope":scope,"state_revisions":{"resources":{"activity:ship_inspection":revision}},
		"craftsman_encounter":{"game_scope":scope,"revision":revision,"intro_seen":true,
			"wreck_reported":true,"offer_pending":not active,"outing_active":active,
			"inspection_complete":false,"mode":"departure_pending" if active else "workshop_routine"}}
func run() -> void:
	var main = load("res://tests/fisherman_test_main.gd").new()
	main.backend_url = "http://127.0.0.1:1"
	root.add_child(main)
	main.game_scope="guidance:test"
	main.world_loaded=true
	main.inventory_label.text=""
	main.fisherman.intro_seen=true
	main.craftsman_activity.intro_seen=true
	main.onboarding.state_path="/tmp/npc-guidance-unused.cfg"
	main.revisioned_state.reset(main.game_scope)
	main.craftsman_gateway.restore(snapshot(main.game_scope,0,false))
	main.craftsman_gateway.checkpoint_provider = Callable()
	var popup = main.get("craftsman_objective")
	check(popup!=null,"Craftsman guidance reuses an objective presenter")
	if popup==null:
		main.queue_free(); await process_frame; quit(1); return
	var chat = main.chat_windows[1]
	chat.game_scope=main.game_scope
	chat.open_chat()
	main._apply_chat_state(snapshot(main.game_scope,1,false))
	check(chat.visible and not popup.objective.visible,"Wreck report alone keeps chat open and does not prompt travel")
	main._apply_chat_state(snapshot("another:save",2,true))
	check(chat.visible and not popup.objective.visible,"Foreign scope cannot close chat or create guidance")
	var accepted := snapshot(main.game_scope,2,true)
	main._apply_chat_state(accepted)
	await process_frame
	check(not chat.visible,"Confirmed inspection acceptance closes chat automatically")
	check(popup.objective.visible and popup.animating,"Acceptance begins the objective animation")
	check(popup.objective_text.text=="Lead the Craftsman to the boat.","Objective names the next player action")
	check(popup.get_script()==main.onboarding.get_script(),"Arrival and Craftsman objectives share the same style and animation code")
	check(not popup.owns_input() and not main.ui_owns_input(),"Travel prompt does not block player movement")
	await capture("center")
	popup.advance(0.5)
	var elapsed: float=popup.elapsed
	chat.open_chat()
	main._apply_chat_state(accepted)
	check(chat.visible and is_equal_approx(popup.elapsed,elapsed),"Replayed acceptance neither closes later chat nor replays the popup")
	chat.close_chat()
	main._open_menu()
	elapsed=popup.elapsed
	for i in range(4): await process_frame
	check(is_equal_approx(popup.elapsed,elapsed),"Menu pauses the objective animation")
	main._resume_game()
	popup.advance(3.0)
	check(not popup.animating and popup.objective.position.distance_to(popup.DOCK)<1,"Objective docks using the arrival transition")
	await capture("docked")
	for dimensions in [Vector2i(960,540),Vector2i(1920,1080)]:
		root.size=dimensions; main._resize_ui()
		await process_frame
		check(Rect2(Vector2.ZERO,root.get_visible_rect().size).encloses(popup.objective.get_global_rect()),"Docked guidance fits "+str(dimensions))
	popup.reset_presentation()
	main._sync_craftsman_guidance(false)
	check(popup.objective.visible and not popup.animating,"Reloaded accepted outing restores docked guidance without replay")
	main._complete_craftsman_guidance()
	check(popup.completed and popup.completing,"Reaching the boat completes guidance with the existing checkmark animation")
	popup.advance(popup.COMPLETION_END)
	check(not popup.objective.visible,"Completed guidance fades away")
	main.queue_free(); await process_frame
	print("Craftsman guidance failures: ",failures)
	quit(1 if failures else 0)
