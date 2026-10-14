extends Node
# Durable story state lives in the gateway. This controller reconstructs only
# presentation and combat; it never attempts to undo an outcome locally.
const Router = preload("res://scripts/actor_router.gd")
var data: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://resources/gatherer_encounter.json"))
var lines: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://resources/gatherer_dialogue.json"))
var main: Node
var gateway: Node
var combat: Node2D
var boars: Array = []
var boar_routes: Array = [Router.new(),Router.new()]
var router = Router.new()
var phase := ""
var beat := 0
var elapsed := 0.0
var recovery_pending := false
var capability_delay := 0.0
var return_armed := true
var corpses := false
var route_goal := Vector2.ZERO
var route_next := ""
var route_retries := 0
var route_error := false
var resume_phase := ""
var panel: PanelContainer
var line: Label
var choices: VBoxContainer
var hud: PanelContainer
var hearts_label: Label
var hint_label: Label
var knife: Label
var was_paused := false
var anger: Label
func mark(id: String) -> Vector2:
	var a: Array=data.marks[id]; return Vector2(a[0],a[1])
func bounds(id: String) -> Rect2:
	var a: Array=data[id]; return Rect2(a[0],a[1],a[2],a[3])
func configure(owner_node: Node, actor_gateway: Node) -> void:
	main=owner_node; gateway=actor_gateway
	for i in range(2):
		var boar=load("res://scripts/boar.gd").new()
		main.world_view.world.add_child(boar); boars.append(boar); boar.hide()
	combat=load("res://scripts/player_combat.gd").new()
	main.world_view.world.add_child(combat)
	combat.configure(main.player,boars,main.village.layout,bounds("CombatBounds"))
	for boar in boars: boar.configure(main.player,combat,main.village.layout,bounds("CombatBounds"))
	panel=PanelContainer.new(); main.ui.add_child(panel)
	panel.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	panel.offset_left=24; panel.offset_right=-24; panel.offset_top=-205; panel.offset_bottom=-16
	var content=VBoxContainer.new(); panel.add_child(content)
	var title=Label.new(); title.text="GATHERER  •  A cry from the forest"; content.add_child(title)
	line=Label.new(); line.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART; content.add_child(line)
	choices=VBoxContainer.new(); content.add_child(choices); panel.hide()
	hud=PanelContainer.new(); main.ui.add_child(hud)
	hud.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	hud.offset_left=24; hud.offset_right=-24; hud.offset_top=-155; hud.offset_bottom=-16
	var box=VBoxContainer.new(); hud.add_child(box)
	hearts_label=Label.new(); hearts_label.add_theme_color_override("font_color",Color("ef9b82")); box.add_child(hearts_label)
	hint_label=Label.new(); hint_label.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART; box.add_child(hint_label)
	hud.hide()
	anger=Label.new(); anger.text="!"; anger.add_theme_font_size_override("font_size",32); anger.add_theme_color_override("font_color",Color("e87960")); main.ui.add_child(anger); anger.hide()
	knife=Label.new(); knife.text="✦  Borrowed knife"; knife.add_theme_color_override("font_color",Color("fff0ce")); main.ui.add_child(knife); knife.hide()
	for item in [panel,hud,knife,anger]: main.ui.move_child(item,main.menu_layer.get_index())
	gateway.updated.connect(_updated); gateway.failed.connect(_failed)
func owns_input() -> bool: return not phase.is_empty()
func allows_movement() -> bool: return phase=="combat" and not was_paused
func blocks_chat() -> bool: return gateway.state.get("status","unseen") not in ["resolved_helped","resolved_declined"]
func camera_target() -> Vector2:
	if phase=="route":
		if route_next=="retreated": return main.player.position+Vector2(-80,-20)
		return (main.player.position+mark("GathererMark")+mark("BoarThreatA"))/3.0+Vector2(0,24)
	return mark("GathererMark")+Vector2(0,8 if phase in ["combat","release"] else 40)
func status() -> String: return str(gateway.state.get("status","unseen"))
func eligible() -> bool:
	return main.world_loaded and not main.cinematic and not main.quitting and not main.travelling and not main.ui_owns_input() and not main._operations_pending() and main.village.layout.interior_at(main.player.position).is_empty()
func restore(world: Dictionary) -> void:
	dispose(); gateway.restore(world)
	recovery_pending=status() not in ["unseen","resolved_helped","resolved_declined"]
	return_armed=true
func dispose() -> void:
	phase=""; recovery_pending=false; corpses=false; was_paused=false
	if main==null: return
	router.stop(main.player); combat.stop(); combat.reset()
	main.player.get_child(0).set_scripted_mode(false)
	main.npc_nodes[2].modulate=Color.WHITE
	for boar in boars: boar.hide()
	panel.hide(); hud.hide(); knife.hide(); anger.hide()
func _capture() -> void:
	main._close_overlays(); main.onboarding.complete_objective(false)
	main.player.velocity=Vector2.ZERO; main.player.set_physics_process(false)
	main.npc_nodes[2].position=mark("GathererMark")
func _actors(dead: bool=false) -> void:
	combat.reset(); main.player.get_child(0).set_scripted_mode(false)
	for i in range(2):
		boars[i].reset_at(mark("BoarSpawnA" if i==0 else "BoarSpawnB"))
		boars[i].show()
		if dead: boars[i].set_dead()
	corpses=dead
	main.npc_nodes[2].position=mark("GathererMark")
	main.npc_nodes[2].get_child(0).set_facing("left")
func advance(delta: float) -> void:
	if not main.world_loaded: return
	var paused: bool=main.menu_layer.visible or main.restart_dialog.visible or main.quitting
	if paused:
		was_paused=true; main.player.velocity=Vector2.ZERO; return
	if was_paused:
		was_paused=false
		if phase=="combat": phase="release"; elapsed=0
	if phase.is_empty():
		var inside: bool=bounds("ForestEntryRegion").has_point(main.player.position)
		if not inside:
			return_armed=true
			if corpses:
				for boar in boars: boar.hide()
				corpses=false
		if not eligible(): return
		if gateway.state.is_empty():
			if inside:
				main.recovery_notice="Gatherer encounter: reconnecting to backend • You can keep exploring."
				capability_delay-=delta
				if capability_delay<=0:
					capability_delay=3.0; gateway.refresh()
			return
		if recovery_pending:
			recovery_pending=false; _capture(); _recover(); return
		if inside and status()=="unseen":
			_capture(); _command("begin_intro"); return
		if inside and status()=="declined_return_pending" and return_armed:
			_capture(); _command("begin_confrontation"); return
		return
	anger.visible=phase=="confrontation"
	anger.position=main.world_view.world_to_screen(mark("GathererMark")-Vector2(0,82))/main.ui.scale-Vector2(8,12)
	elapsed+=delta
	if phase=="checkpoint_fade":
		main.travel_fade.show(); main.travel_fade.color.a=minf(1,elapsed/0.18)
		if elapsed>=0.2:
			main.player.position=mark("IntroCheckpoint")
			main.travel_fade.hide(); main.travel_fade.color.a=0
			_intro()
	elif phase=="route":
		var result: String=router.advance(main.player,delta,110 if route_next=="threat" else 180)
		if result=="blocked" or elapsed>18:
			if route_retries<1:
				route_retries+=1; elapsed=0
				if router.set_target(main.player.position,route_goal,main.village.layout): return
			route_error=true; _failed("The path is blocked. Retry the walk from here, or quit to menu.")
		elif result=="arrived": _arrived()
	elif phase=="threat":
		for i in range(2): boar_routes[i].advance(boars[i],delta,30)
		if elapsed>=4.2:
			for boar in boars: boar.state="cinematic_threat"; boar.queue_redraw()
			main.npc_nodes[2].get_child(0).set_facing("right")
			main.player.get_child(0).set_facing("left")
			phase="choice"; _present(lines.request,[[lines.help,help],[lines.decline,decline]])
	elif phase=="handoff":
		knife.position=main.world_view.world_to_screen(mark("GathererMark").lerp(main.player.position,clampf(elapsed/0.65,0,1))-Vector2(0,64))/main.ui.scale
		if elapsed>=0.8:
			knife.hide(); phase="tutorial"; _present(lines.handoff+"\n\n"+lines.tutorial,[["Continue",continue_scene]])
	elif phase=="release":
		if Input.is_key_pressed(KEY_ENTER) or Input.is_key_pressed(KEY_SPACE) or Input.is_key_pressed(KEY_J) or Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT): elapsed=0; return
		if elapsed>0.12:
			phase="combat"
			if not combat.enabled: combat.start()
	elif phase=="combat":
		combat.advance(delta)
		hearts_label.text="♥".repeat(combat.hearts)+"♡".repeat(3-combat.hearts)+"   •   Borrowed gathering knife"
		# Defeat takes precedence even when the last boar dies this step.
		if combat.hearts<=0:
			combat.stop(); hud.hide(); phase="defeat"; main.player.set_physics_process(false)
			main.player.get_child(0).set_scripted_mode(true); main.player.get_child(0).play_scripted("fall")
			_present(lines.defeat,[["Retry encounter",retry_encounter],["Quit to menu",quit_to_menu]])
		elif boars.all(func(b): return b.health<=0):
			combat.stop(); corpses=true; _command("victory",{"attempt_id":gateway.state.attempt_id})
func _intro() -> void:
	_actors(); hud.hide(); knife.hide()
	_route(mark("PlayerTalkMark"),"threat")
func _recover() -> void:
	match status():
		"intro_pending": _command("restart_attempt",{"attempt_id":gateway.state.attempt_id})
		"saved_thanks_pending": _actors(true); _route(mark("PlayerTalkMark"),"thanks")
		"declined_retreat_pending": _actors(); _route(mark("VillageReturnMark"),"retreated")
		"declined_return_pending":
			phase=""
			if bounds("ForestEntryRegion").has_point(main.player.position): _command("begin_confrontation")
		"declined_confrontation_pending": _actors(true); _route(mark("PlayerTalkMark"),"confrontation")
		_: _finish()
func _route(goal: Vector2, next: String) -> void:
	route_goal=goal; route_next=next; elapsed=0; route_retries=0; route_error=false
	phase="route"; panel.hide(); main.player.set_physics_process(false)
	if not router.set_target(main.player.position,goal,main.village.layout):
		route_error=true; _failed("A clear route could not be found. Retry the walk, or quit to menu.")
func _arrived() -> void:
	phase=route_next; elapsed=0
	main.player.get_child(0).set_facing("left")
	match phase:
		"threat":
			combat.play_sound("warning")
			for i in range(2): boar_routes[i].set_target(boars[i].position,mark("BoarThreatA" if i==0 else "BoarThreatB"),main.village.layout)
		"handoff": knife.show()
		"thanks", "confrontation":
			beat=0; main.npc_nodes[2].get_child(0).set_facing("right")
			if phase=="confrontation": main.npc_nodes[2].modulate=Color("e6b3a2"); anger.show()
			_present(lines[phase][0],[["Continue",continue_scene]])
		"retreated": _command("complete_retreat")
func _present(text: String, options: Array) -> void:
	line.text=text
	for child in choices.get_children(): choices.remove_child(child); child.queue_free()
	for option in options:
		var button=Button.new(); button.text=option[0]; button.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
		button.pressed.connect(option[1]); choices.add_child(button)
	panel.show()
	if not main.menu_layer.visible and choices.get_child_count()>0: choices.get_child(0).grab_focus()
func help() -> void:
	if phase!="choice" or main.menu_layer.visible: return
	_command("accept",{"attempt_id":gateway.state.attempt_id})
func decline() -> void:
	if phase!="choice" or main.menu_layer.visible: return
	_command("decline")
func continue_scene() -> void:
	if main.menu_layer.visible: return
	if phase=="tutorial":
		panel.hide(); hud.show(); hearts_label.text="♥♥♥   •   Borrowed gathering knife"
		hint_label.text="WASD Move • J Attack • Step aside at the amber warning\nHelp the Gatherer defeat both boars"
		phase="release"; elapsed=0
	elif phase=="refusal": _route(mark("VillageReturnMark"),"retreated")
	elif phase in ["thanks","confrontation"]:
		beat+=1
		if beat<lines[phase].size(): _present(lines[phase][beat],[["Continue",continue_scene]])
		else: _command("finish_presentation")
func retry_encounter() -> void:
	if phase!="defeat" or main.menu_layer.visible: return
	_command("restart_attempt",{"attempt_id":gateway.state.attempt_id})
func quit_to_menu() -> void:
	main._open_menu()
func _command(command: String, payload: Dictionary={}) -> void:
	phase="saving"; panel.hide(); hud.hide(); main.player.velocity=Vector2.ZERO; main.player.set_physics_process(false)
	gateway.send_command(command,payload)
func _updated(world: Dictionary, operation: String) -> void:
	if world.get("npc",{}).get("role","")=="gatherer": main.npc_nodes[2].apply_state(world.npc)
	for npc in world.get("npcs",[]):
		if int(npc.get("id",0))==2: main.npc_nodes[2].apply_state(npc)
	if operation=="refresh":
		if main.recovery_notice.begins_with("Gatherer encounter"): main.recovery_notice=""
		if phase.is_empty():
			recovery_pending=status() not in ["unseen","resolved_helped","resolved_declined"]
			return
		combat.stop(); hud.hide(); _recover(); return
	match operation:
		"begin_intro": _intro()
		"restart_attempt": phase="checkpoint_fade"; elapsed=0; panel.hide(); hud.hide(); combat.reset()
		"accept": _route(mark("CombatStartMark"),"handoff")
		"victory": hud.hide(); _route(mark("PlayerTalkMark"),"thanks")
		"decline": phase="refusal"; _present(lines.refusal,[["Continue",continue_scene]])
		"complete_retreat":
			for boar in boars: boar.set_dead(); boar.hide()
			return_armed=true; _finish()
		"begin_confrontation": _actors(true); _route(mark("PlayerTalkMark"),"confrontation")
		"finish_presentation": _finish()
func _failed(message: String) -> void:
	if phase.is_empty() and gateway.state.is_empty():
		main.recovery_notice="Gatherer encounter: reconnecting to backend • You can keep exploring."
		return
	resume_phase=phase; phase="error"; hud.hide(); combat.stop(); main.player.set_physics_process(false)
	_present(message,[["Retry",retry_save_or_route],["Quit to menu",quit_to_menu]])
func retry_save_or_route() -> void:
	if phase!="error" or main.menu_layer.visible: return
	if route_error: _route(route_goal,route_next)
	else:
		phase="saving"; panel.hide(); gateway.retry()
func _finish() -> void:
	phase=""; panel.hide(); hud.hide(); knife.hide(); anger.hide(); combat.stop()
	main.player.get_child(0).set_scripted_mode(false)
	main.npc_nodes[2].modulate=Color.WHITE
	main.player.set_control_enabled(true)
