extends Node
var main: Node
var activity: RefCounted
var gateway: Node
var player_router = preload("res://scripts/actor_router.gd").new()
var npc_router = preload("res://scripts/actor_router.gd").new()
var lines: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://resources/craftsman_dialogue.json"))
var phase := ""
var beat := 0
var panel: PanelContainer
var line: Label
var continue_button: Button
var skip_button: Button
var route_time := 0.0
var retry_id := ""
var intro_retry := false
var ship_state: Dictionary = {}
var intro_attempted := false
var inspection_attempted := false
func configure(owner_node: Node, actor_activity: RefCounted, actor_gateway: Node) -> void:
	main=owner_node; activity=actor_activity; gateway=actor_gateway
	panel=PanelContainer.new(); main.ui.add_child(panel)
	panel.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	panel.offset_left=24; panel.offset_right=-24; panel.offset_top=-220; panel.offset_bottom=-16
	var content := VBoxContainer.new(); panel.add_child(content)
	var title := Label.new(); title.text="Craftsman"; content.add_child(title)
	line=Label.new(); line.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART; content.add_child(line)
	var row := HBoxContainer.new(); content.add_child(row)
	continue_button=Button.new(); continue_button.text="Continue"; row.add_child(continue_button)
	continue_button.pressed.connect(continue_scene)
	skip_button=Button.new(); skip_button.text="Skip"; row.add_child(skip_button); skip_button.pressed.connect(skip)
	panel.hide()
	main.ui.move_child(panel,main.menu_layer.get_index())
	gateway.updated.connect(_updated); gateway.failed.connect(_failed)
func owns_input() -> bool: return phase not in ["","outcome_retry","intro_retry"]
func is_ship_frame() -> bool:
	return phase.begins_with("inspection") or phase in ["outcome_pending","farewell"]
func camera_target() -> Vector2:
	return main.player.position.lerp(activity.actor.position,0.5)+Vector2(0,200 if is_ship_frame() else -16)
func eligible() -> bool:
	return main.world_loaded and not main.cinematic and not main.travelling and not main.menu_layer.visible and not main.quitting and not main.ui_owns_input()
func try_introduction() -> bool:
	if activity.intro_seen or intro_attempted or owns_input() or not eligible() or main.village.layout.interior_at(main.player.position)!="workshop" or activity.space!="workshop": return false
	intro_attempted=true
	main.onboarding.complete_objective()
	activity.overridden=true; activity.router.stop(activity.actor)
	var target := Vector2.INF
	for offset in [Vector2(0,72),Vector2(-72,0),Vector2(72,0),Vector2(0,-72)]:
		var at: Vector2=activity.actor.position+offset
		if player_router.set_target(main.player.position,at,main.village.layout): target=at; break
	if target==Vector2.INF:
		cancel(); main.recovery_notice="The Craftsman needs a clear approach. Move closer and press E."; return false
	phase="intro_approach"; beat=0; route_time=0
	main.player.set_physics_process(false)
	return true
func restore(data: Dictionary) -> void:
	cancel(); intro_attempted=false; inspection_attempted=false; retry_id=""; intro_retry=false
	ship_state=data.get("ship_repair",{})
	if activity.inspection_complete: return
	if activity.presentation in ["inspection_dialogue","outcome_pending"]:
		var p: Array=activity.data.InspectionPlayerMark; var n: Array=activity.data.InspectionCraftsmanMark
		if main.player.position.distance_to(Vector2(p[0],p[1]))>20 or activity.actor.position.distance_to(Vector2(n[0],n[1]))>20: return
		inspection_attempted=true; activity.overridden=true
		if activity.presentation=="outcome_pending":
			phase="outcome_retry"; present("The inspection is ready. Retry to save A Way Home."); continue_button.text="Retry"; skip_button.text="Close"
		else:
			phase="inspection_dialogue"; beat=clampi(activity.presentation_beat,1,3)
			present(ship_state.get("requirement_text","") if beat==3 else lines.inspection[beat].text)
func advance(delta: float) -> void:
	if main.menu_layer.visible or main.quitting: return
	if phase.is_empty():
		var at: Array=activity.data.InspectionArrival
		if main.player.position.distance_to(Vector2(at[0],at[1]))>210: inspection_attempted=false
		if main.village.layout.interior_at(main.player.position)!="workshop": intro_attempted=false
		if not try_introduction(): try_inspection()
		return
	if phase.ends_with("approach") or phase=="inspection_staging":
		route_time+=delta
		var a: String=player_router.advance(main.player,delta,180)
		var b := "arrived"
		if phase=="inspection_staging": b=npc_router.advance(activity.actor,delta,180)
		if a=="blocked" or b=="blocked" or route_time>15:
			cancel(); main.recovery_notice="The approach is blocked. Move to clear ground and try again."; return
		if a=="arrived" and b=="arrived":
			main.player.get_child(0).set_facing("up" if phase=="intro_approach" else "down")
			activity.actor.face(main.player.position)
			if phase=="intro_approach": phase="intro_dialogue"; present(lines.intro[0].text)
			else:
				phase="inspection_dialogue"; activity.presentation="inspection_dialogue"; beat=1; activity.presentation_beat=1
				activity.actor.face(Vector2(0,3800)); present(lines.inspection[beat].text)
func present(text: String) -> void:
	line.text=text; panel.show(); continue_button.text="Continue"; continue_button.disabled=false
	skip_button.text="Skip"; skip_button.show(); continue_button.grab_focus()
func continue_scene() -> void:
	if phase in ["intro_pending","outcome_pending"]: return
	if phase=="intro_dialogue":
		beat+=1
		if beat<lines.intro.size(): present(lines.intro[beat].text)
		else: commit_intro()
	elif phase=="inspection_recognition": stage_inspection()
	elif phase=="inspection_dialogue":
		beat+=1; activity.presentation_beat=beat
		if beat<lines.inspection.size(): present(ship_state.get("requirement_text","") if beat==3 else lines.inspection[beat].text)
		else: retry_outcome()
	elif phase=="outcome_retry": retry_outcome()
	elif phase=="intro_retry": commit_intro()
	elif phase=="farewell": cancel()
func commit_intro() -> void:
	phase="intro_pending"; intro_retry=true; continue_button.disabled=true
	if retry_id.is_empty(): retry_id=gateway.game_scope+":intro"
	gateway.send_command("intro_complete",{"player_position":{"x":main.player.position.x,"y":main.player.position.y}},retry_id)
func try_inspection() -> bool:
	if inspection_attempted or owns_input() or not eligible() or not activity.outing_active or activity.inspection_complete or activity.space!="exterior" or not main.village.layout.interior_at(main.player.position).is_empty(): return false
	var at: Array=activity.data.InspectionArrival
	var arrival := Vector2(at[0],at[1])
	if main.player.position.distance_to(arrival)>176 or activity.actor.position.distance_to(arrival)>176: return false
	var p: Array=activity.data.InspectionPlayerMark; var n: Array=activity.data.InspectionCraftsmanMark
	if not player_router.set_target(main.player.position,Vector2(p[0],p[1]),main.village.layout) or not npc_router.set_target(activity.actor.position,Vector2(n[0],n[1]),main.village.layout): return false
	inspection_attempted=true
	activity.overridden=true; activity.router.stop(activity.actor)
	phase="inspection_recognition"; beat=0; route_time=0
	main.player.set_physics_process(false); present(lines.inspection[0].text)
	return true
func stage_inspection() -> void:
	phase="inspection_staging"; activity.presentation="inspection_staging"; panel.hide(); route_time=0
func retry_outcome() -> void:
	phase="outcome_pending"; activity.presentation="outcome_pending"; continue_button.disabled=true
	if retry_id.is_empty(): retry_id=gateway.game_scope+":inspection"
	gateway.send_command("complete_inspection",{"staged":true,"player_position":{"x":main.player.position.x,"y":main.player.position.y}},retry_id)
func skip() -> void:
	if phase in ["intro_pending","outcome_pending"]: return
	if phase in ["outcome_retry","intro_retry"]: cancel()
	elif phase.begins_with("intro"): commit_intro()
	elif phase=="inspection_dialogue" or phase=="outcome_retry": retry_outcome()
	elif phase.begins_with("inspection"): cancel()
	elif phase=="farewell": cancel()
func cancel() -> void:
	player_router.stop(main.player) if main!=null else null
	if activity!=null:
		npc_router.stop(activity.actor); activity.overridden=false; activity.idle_left=2
	phase=""
	if panel: panel.hide()
func _updated(data: Dictionary, operation: String) -> void:
	ship_state=data.get("ship_repair",ship_state)
	if operation not in ["command","refresh"]: return
	if phase in ["intro_pending","intro_retry"] and data.craftsman_encounter.get("intro_seen",false):
		intro_retry=false; retry_id=""; cancel(); main.current_npc=activity.actor; main._open_dialogue()
	elif phase in ["outcome_pending","outcome_retry"] and data.craftsman_encounter.get("inspection_complete",false):
		activity.presentation=""; activity.apply_encounter(data.craftsman_encounter)
		activity.overridden=true
		phase="farewell"; present(lines.farewell); skip_button.text="Close"
		main.recovery_notice="A Way Home — Gather the ship-repair materials."
func _failed(message: String) -> void:
	if phase in ["outcome_pending","intro_pending"]:
		var outcome := phase=="outcome_pending"
		cancel()
		# Restore free movement; a visible Retry preserves the accepted outcome beat.
		phase="outcome_retry" if outcome else "intro_retry"
		activity.overridden=true
		present(message); continue_button.text="Retry"; skip_button.text="Close"
	else: main.recovery_notice=message
