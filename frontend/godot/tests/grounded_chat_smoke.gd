# Invoked only by run_godot_grounding.py with its runner-owned endpoint.
# Drives the real scene controls, HTTPRequest parser and display; no fake replies.
extends SceneTree

var endpoint := ""
var evidence_dir := ""
var failure_mode := false
var resume_mode := false
var behavior_mode := false
var checks: Array = []
var chats: Array = []
var last_response: Dictionary = {}
var npc_states: Dictionary = {}
var scene

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--verification-url="): endpoint = arg.trim_prefix("--verification-url=")
		if arg.begins_with("--evidence-dir="): evidence_dir = arg.trim_prefix("--evidence-dir=")
		if arg == "--failure-mode": failure_mode = true
		if arg == "--resume-mode": resume_mode = true
		if arg == "--behavior-mode": behavior_mode = true
	# Never default to the player's backend. The Python runner reserves this port.
	if not endpoint.begins_with("http://127.0.0.1:") or endpoint in ["http://127.0.0.1:8000", "http://127.0.0.1:8001"] or evidence_dir.is_empty():
		push_error("Use the disposable Python runner")
		quit(2)
		return
	call_deferred("run_check")

func record(ok: bool, label: String) -> void:
	checks.append({"passed": ok, "label": label})
	print("PASS " if ok else "FAIL ", label)
	write_report()

func write_report() -> void:
	var file := FileAccess.open(evidence_dir.path_join("resume.json" if resume_mode else "godot.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify({"engine": Engine.get_version_info(), "display": DisplayServer.get_name(), "checks": checks, "chats": chats}, "  "))

func wait_for(condition: Callable) -> bool:
	var deadline := Time.get_ticks_msec() + 170000
	while not condition.call():
		await process_frame
		if Time.get_ticks_msec() > deadline:
			record(false, "Operation timed out")
			quit(1)
			return false
	return true

func new_scene() -> void:
	scene = load("res://scenes/Main.tscn").instantiate()
	scene.backend_url = endpoint
	root.add_child(scene)
	scene.world_request.request_completed.connect(func(_result, _code, _headers, body):
		var data: Variant = JSON.parse_string(body.get_string_from_utf8())
		if data is Dictionary:
			for npc in data.get("npcs", []): npc_states[int(npc.id)] = npc.duplicate(true))
	for window in scene.chat_windows.values():
		window.world_changed.connect(func(response: Dictionary):
			last_response = response.duplicate(true)
			if response.has("npc"): npc_states[int(response.npc.id)] = response.npc.duplicate(true))

func ask(id: int, message: String, facts: Array = [], kind := "", safe := true) -> void:
	var window = scene.chat_windows[id]
	for other in scene.chat_windows.values(): other.close_chat()
	window.open_chat()
	var before_items: Array = scene.player_items.duplicate()
	var before_phase: String = scene.bow_state.phase
	var before_state: Dictionary = npc_states[id].duplicate(true)
	last_response = {}
	window.message_input.text = message
	var started := Time.get_ticks_msec()
	window.send_button.pressed.emit()
	if not await wait_for(func(): return not window.pending): return
	var response := last_response.duplicate(true)
	var output: Dictionary = response.get("validated_output", {})
	var answer: String = response.get("final_dialogue", "")
	chats.append({"npc_id": id, "message": message, "seconds": (Time.get_ticks_msec() - started) / 1000.0, "response": response, "displayed_text": window.conversation_text()})
	record(not response.is_empty() and not answer.is_empty() and window.conversation_text().contains(answer), "Displayed parsed response: " + message)
	record(not window.send_button.disabled and not window.clear_button.disabled, "Controls recovered: " + message)
	for fact in facts:
		record(fact in output.get("fact_ids", []) and not response.get("grounding_trace", {}).get("rejected", true), "Selected " + fact + ": " + message)
	if not kind.is_empty(): record(output.get("answer_kind") == kind, "Answer kind " + kind + ": " + message)
	if safe:
		var unchanged: bool = scene.player_items == before_items and scene.bow_state.phase == before_phase
		for field in ["trust", "fear", "aggression", "curiosity", "inventory", "pending_item"]:
			unchanged = unchanged and npc_states[id].get(field) == before_state.get(field)
		if failure_mode: unchanged = unchanged and npc_states[id].get("current_state") == before_state.get("current_state")
		record(unchanged, "Zero inventory/quest/NPC effects: " + message)
	var trace: Dictionary = response.get("decision_trace", {})
	var outcome: Dictionary = trace.get("outcome", {})
	var behavior: Dictionary = trace.get("behavior", {})
	var retrieval: Dictionary = trace.get("context", {}).get("memory_retrieval", {})
	record(trace.get("schema_version") == 1 and trace.get("recipient_id") == id and not str(trace.get("game_scope", "")).is_empty(), "Parsed scoped decision trace: " + message)
	record(not str(trace.get("decision_id", "")).is_empty() and trace.get("decision_id") == outcome.get("event_id") and outcome.get("conversation_id", 0) > 0, "Parsed durable outcome identity: " + message)
	var selection: String = behavior.get("selection", "")
	record(behavior.get("eligibility", {}).get(selection, {}).get("eligible", false) and behavior.get("scores", {}).has(selection), "Parsed eligible FSEC selection: " + message)
	record(retrieval.has("mode") and retrieval.get("selected_ids", []).size() <= retrieval.get("result_limit", -1), "Parsed bounded retrieval diagnostics: " + message)
	if failure_mode:
		record(trace.get("generation", {}).get("status") == "provider_or_decode_failure" and outcome.get("action") == null, "Parsed provider failure trace with no authorized action")
	write_report()

func snapshot(name: String) -> void:
	if DisplayServer.get_name() == "headless": return
	await process_frame
	await RenderingServer.frame_post_draw
	var error := root.get_texture().get_image().save_png(evidence_dir.path_join(name + ".png"))
	record(error == OK, "Saved rendered snapshot: " + name)

func run_check() -> void:
	new_scene()
	if not await wait_for(func(): return scene.world_loaded): return
	if resume_mode:
		record(scene.bow_state.phase == "completed" and scene.player_items.count("bow") == 1, "Backend and Godot restart preserve completed quest and one reward")
		record(scene.player.position == Vector2(10064, 10032), "Backend restart preserves saved interior position")
		record(scene.chat_windows[1].conversation_text().contains("Verified bow materials delivered"), "Backend restart preserves grounded history")
		for attempt in range(2):
			scene._quest_call("advance")
			if not await wait_for(func(): return not scene.quest_busy): return
			record(scene.player_items.count("bow") == 1, "Repeated advance does not duplicate completed reward")
		if not await wait_for(func(): return not scene._operations_pending()): return
		scene.restart_button.pressed.emit()
		record(scene.restart_dialog.visible, "Explicit restart asks for confirmation")
		scene.restart_dialog.hide()
		scene.restart_dialog.confirmed.emit()
		if not await wait_for(func(): return scene.world_loaded): return
		record(scene.bow_state.phase == "available" and scene.player_items == ["water", "food"] and scene.player.position == Vector2.ZERO, "Disposable restart resets phase, inventory and position")
		record(not scene.chat_windows[1].conversation_text().contains("Verified bow materials delivered"), "Disposable restart clears old dialogue")
		await snapshot("reset")
		finish_check()
		return
	record(scene.player_items == ["water", "food"] and scene.bow_state.phase == "available", "Fresh isolated world")
	if failure_mode:
		for id in [1, 2]:
			await ask(id, "Where is the Gatherer?")
			record(last_response.get("grounding_trace", {}).get("rejected", false), "Provider failure produces rejected zero-effect fallback")
			record(not last_response.get("memory_classification", {}).get("stored", true), "Provider failure stores no important memory")
		await snapshot("provider-failure")
		finish_check()
		return
	if behavior_mode:
		await ask(1, "Can I have rope?")
		record(last_response.get("behavior_trace", {}).get("selection") == "refuse", "Distrustful Craftsman refuses optional rope visibly")
		record(last_response.get("final_dialogue", "").contains("I'd rather keep my rope"), "Optional refusal text reaches real dialogue display")
		await snapshot("optional-refusal")
		await ask(2, "Can I have fruits?", [], "", false)
		record(last_response.get("behavior_trace", {}).get("selection") == "cooperate", "Helpful Gatherer selects cooperation")
		record(last_response.get("final_dialogue", "").contains("Glad to help."), "Cooperative expression reaches real dialogue display")
		await snapshot("optional-cooperation")
		await ask(2, "For my work in the village", [], "", false)
		record(scene.player_items.has("fruits"), "Cooperation uses authoritative transfer after purpose")
		await ask(2, "I give you fruits", [], "", false)
		record(not scene.player_items.has("fruits"), "Return optional fixture item through authoritative service")
	var cases: Array = JSON.parse_string(FileAccess.get_file_as_string("res://tests/grounding_scenarios.json"))
	for id in [1, 2]:
		for case in cases:
			await ask(id, case.message, case.get("facts", []), case.get("kind", ""))
			if case.message == "How do I get there?": await snapshot("route-npc-%s" % id)
	# Actual existing quest, transfers, pickup and timed reward through UI handlers.
	scene._quest_call("start")
	if not await wait_for(func(): return not scene.quest_busy): return
	await ask(1, "Can you make me a bow?", [], "", false)
	record(scene.bow_state.phase == "gather", "Craftsman request advances started quest")
	var gatherer = scene.chat_windows[2]
	gatherer.open_chat()
	gatherer.item_grid.select_item("wood")
	gatherer.take_button.pressed.emit()
	if not await wait_for(func(): return not gatherer.pending): return
	record(not scene.player_items.has("wood"), "Wood request waits for purpose")
	await ask(2, "To help the Craftsman make a bow", [], "", false)
	record(scene.player_items.has("wood"), "Confirmed transfer grants owned wood")
	for window in scene.chat_windows.values(): window.close_chat()
	scene.player.position = Vector2(-70, 240)
	var pickup := InputEventKey.new()
	pickup.keycode = KEY_F
	pickup.pressed = true
	scene._unhandled_input(pickup)
	if not await wait_for(func(): return not scene.quest_busy): return
	record(scene.player_items.has("string"), "F pickup grants real string")
	scene.player.position = Vector2(10064, 10032)
	scene._update_current_npc()
	scene.player_grid.select_item("wood")
	scene._give_selected_item()
	if not await wait_for(func(): return not scene.chat_windows[1].pending): return
	await ask(1, "What have I already delivered?", ["quest.bow.delivered"])
	record(last_response.get("final_dialogue", "").contains("wood") and not last_response.get("final_dialogue", "").contains("string"), "Partial delivery answer reflects wood only")
	await ask(1, "What materials do you need?", ["quest.bow.requirements"])
	record(last_response.get("final_dialogue", "").contains("Still needed: string."), "Only string outstanding after wood transfer")
	await snapshot("partial-delivery")
	if not await wait_for(func(): return not scene._operations_pending()): return
	scene._save_position()
	if not await wait_for(func(): return not scene.position_busy): return
	scene.queue_free()
	await process_frame
	await process_frame
	new_scene()
	if not await wait_for(func(): return scene.world_loaded): return
	record(scene.player.position == Vector2(10064, 10032) and scene.bow_state.phase == "gather" and scene.player_items.has("string") and not scene.player_items.has("wood"), "Scene relaunch resumes saved interior position, phase and transfers")
	record(scene.chat_windows[1].conversation_text().contains("Still needed: string."), "Scene relaunch restores grounded dialogue")
	await ask(1, "What have I already delivered?", ["quest.bow.delivered"])
	scene._update_current_npc()
	scene.player_grid.select_item("string")
	scene._give_selected_item()
	if not await wait_for(func(): return not scene.chat_windows[1].pending): return
	record(scene.bow_state.phase == "crafting" and not scene.player_items.has("bow"), "Second material starts timed crafting without instant reward")
	scene.quest_panel.show()
	await snapshot("crafting")
	if not await wait_for(func(): return scene.bow_state.phase == "completed"): return
	record(scene.player_items.count("bow") == 1, "Timed completion awards exactly one bow")
	await ask(1, "What have I already delivered?", ["quest.bow.delivered"])
	record(last_response.get("final_dialogue", "").contains("string, wood"), "Consumed materials remain verified delivery evidence")
	await ask(1, "What is actually in my bag?", ["player.inventory"])
	record(scene.player_items.count("bow") == 1, "Post-completion chat does not duplicate bow")
	scene.inventory_drawer.show()
	await snapshot("completed")
	finish_check()

func finish_check() -> void:
	write_report()
	var passed := true
	for result in checks:
		if not result.passed: passed = false
	quit(0 if passed else 1)
