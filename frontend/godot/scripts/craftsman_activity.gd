extends RefCounted
const DATA_PATH := "res://resources/craftsman_encounter.json"
var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(DATA_PATH))
var actor: CharacterBody2D
var player: CharacterBody2D
var layout: Resource
var portals: RefCounted
var router = preload("res://scripts/actor_router.gd").new()
var mode := "workshop_routine"
var outing_active := false
var inspection_complete := false
var intro_seen := false
var wait_reason := ""
var return_index := 0
var presentation := ""
var presentation_beat := 0
var idle_left := 6.0
var last_work := -1
var conversation_open := false
var overridden := false
var repath_left := 0.0
var separation_time := 0.0
var failures := 0
var hint := ""
var breadcrumbs: Array[Vector2] = []
var portal_target := Vector2.INF
var bow_busy := false
var space := "workshop"
var follow_moving := false
func configure(npc, leader, world_layout, actor_portals) -> void:
	actor=npc; player=leader; layout=world_layout; portals=actor_portals
func restore(state: Dictionary) -> void:
	var at: Dictionary=state.get("position",{"x":10064,"y":9968})
	actor.position=layout.recover_position(Vector2(at.x,at.y))
	space=layout.interior_at(actor.position)
	if space.is_empty(): space="exterior"
	apply_encounter(state)
	router.stop(actor)
	breadcrumbs.clear()
func apply_encounter(state: Dictionary) -> void:
	var next: String=state.get("mode",mode)
	if next!=mode: router.stop(actor); repath_left=0; failures=0
	mode=next
	outing_active=state.get("outing_active",outing_active)
	inspection_complete=state.get("inspection_complete",inspection_complete)
	intro_seen=state.get("intro_seen",intro_seen)
	wait_reason=state.get("wait_reason",wait_reason)
	return_index=int(state.get("return_index",return_index))
	presentation=state.get("presentation",presentation)
	presentation_beat=int(state.get("presentation_beat",presentation_beat))
func checkpoint() -> Dictionary:
	return {"position":{"x":actor.position.x,"y":actor.position.y},"navigation_space":space,
		"mode":mode,"wait_reason":wait_reason,"return_index":return_index,"presentation":presentation,"presentation_beat":presentation_beat}
func set_conversation_open(open: bool) -> void:
	if conversation_open and not open: idle_left=2; repath_left=0
	conversation_open=open
	if open: actor.velocity=Vector2.ZERO; actor.face(player.position)
func whereabouthint() -> String:
	if space=="workshop": return "Workshop"
	if mode=="waiting_for_player": return "Waiting outside" if wait_reason=="interior" else "Waiting on the path"
	return "Returning to workshop" if mode=="returning_to_workshop" else "On the way to the ship"
func advance(delta: float, paused: bool) -> void:
	actor.location_text=whereabouthint()
	if actor.label: actor.label.text="Craftsman\n"+actor.location_text
	if paused or conversation_open or overridden:
		actor.velocity=Vector2.ZERO; return
	if portal_target!=Vector2.INF:
		walk_to(portal_target,delta,180); return
	if mode=="workshop_routine": routine(delta)
	elif mode=="departure_pending":
		if not bow_busy: mode="following_player"; repath_left=0
	elif mode=="following_player" or (mode=="waiting_for_player" and wait_reason=="interior"):
		follow(delta)
	elif mode=="returning_to_workshop": return_home(delta)
	else: actor.velocity=Vector2.ZERO
func walk_to(target: Vector2, delta: float, speed: float) -> String:
	repath_left-=delta
	if actor.position.distance_to(target)<3: router.stop(actor); failures=0; return "arrived"
	if router.path.is_empty() and repath_left<=0:
		repath_left=0.4
		if not router.set_target(actor.position,target,layout):
			failures+=1; actor.velocity=Vector2.ZERO
			if failures>=4: hint="The Craftsman is blocked. Return to him to find another route."
			return "blocked"
	var result: String=router.advance(actor,delta,speed)
	if result=="blocked": failures+=1; repath_left=0
	return result
func routine(delta: float) -> void:
	if space!="workshop": actor.velocity=Vector2.ZERO; return
	if bow_busy: router.stop(actor); return
	if not router.path.is_empty():
		var result: String=router.advance(actor,delta,75)
		if result!="moving": idle_left=randf_range(5,12); actor.face(actor.position+Vector2(0,-32))
		return
	idle_left-=delta
	if idle_left>0: actor.velocity=Vector2.ZERO; return
	var choices := [0,0,1,1,2,3]
	var selected: int=choices.pick_random()
	if selected==last_work: selected=(selected+1)%data.work_points.size()
	last_work=selected
	var at: Array=data.work_points[selected]
	var target: Vector2=layout.interior_origin("workshop")+Vector2(at[0],at[1])
	if not router.set_target(actor.position,target,layout): idle_left=5
func follow(delta: float) -> void:
	var player_room: String=layout.interior_at(player.position)
	var actor_room: String=layout.interior_at(actor.position)
	if not player_room.is_empty() and player_room!="workshop":
		if space=="exterior":
			mode="waiting_for_player"; wait_reason="interior"
			walk_to(layout.exterior_spawn(player_room)+Vector2(56,24),delta,180)
		return
	if wait_reason=="interior": mode="following_player"; wait_reason=""; repath_left=0
	if actor_room!=player_room:
		var entering := actor_room.is_empty()
		var target: Vector2=layout.exterior_spawn("workshop") if entering else layout.interior_origin("workshop")+Vector2(0,176)
		if walk_to(target,delta,180)=="arrived" and portals.traverse_actor(actor,"workshop",entering):
			space="workshop" if entering else "exterior"; router.stop(actor); breadcrumbs.clear()
		return
	if breadcrumbs.is_empty() or breadcrumbs.back().distance_to(player.position)>20:
		breadcrumbs.append(player.position)
		if breadcrumbs.size()>100: breadcrumbs.pop_front()
	var separation := actor.position.distance_to(player.position)
	separation_time=separation_time+delta if separation>240 else 0
	hint="The Craftsman is catching up" if separation_time>3 else ""
	if separation<=64 and router.clear_segment(actor.position,player.position,layout):
		follow_moving=false; router.stop(actor); actor.face(player.position); return
	if not follow_moving and separation<=96 and router.clear_segment(actor.position,player.position,layout): return
	follow_moving=true
	repath_left-=delta
	if repath_left<=0:
		repath_left=0.4
		var target := player.position
		# A reachable trail point leaves conversational space without cutting corners.
		for i in range(breadcrumbs.size()-1,-1,-1):
			if breadcrumbs[i].distance_to(player.position)>=72:
				target=breadcrumbs[i]; break
		if actor.position.distance_to(target)>1200:
			for point in breadcrumbs:
				if actor.position.distance_to(point)>80 and actor.position.distance_to(point)<600:
					target=point; break
		if not router.set_target(actor.position,target,layout): failures+=1
		else: failures=0
	if failures>=5:
		mode="waiting_for_player"; wait_reason="blocked"; router.stop(actor)
		hint="The Craftsman cannot find a clear route. Return and ask him to follow again."
		return
	var result: String=router.advance(actor,delta,210 if separation>160 else 180)
	if result=="blocked": failures+=1; repath_left=0
func return_home(delta: float) -> void:
	if space=="workshop":
		var target: Vector2=layout.interior_origin("workshop")+Vector2(64,-48)
		if walk_to(target,delta,180)=="arrived":
			mode="workshop_routine"; outing_active=false; idle_left=6; wait_reason=""
		return
	var route: Array=data.return_route
	# Start at the nearest appropriate inland landmark, never drag him back to the beach.
	if return_index==0:
		var best := INF
		for i in range(route.size()):
			var point := Vector2(route[i][0],route[i][1])
			var distance := actor.position.distance_to(point)
			if distance<best: best=distance; return_index=i
	if return_index<route.size():
		var target := Vector2(route[return_index][0],route[return_index][1])
		if walk_to(target,delta,180)=="arrived": return_index+=1
	else:
		if portals.traverse_actor(actor,"workshop",true): space="workshop"; router.stop(actor)
