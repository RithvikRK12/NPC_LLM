extends SceneTree
var failed := false

func _initialize() -> void:
	call_deferred("run_check")

func require(condition: bool, message: String) -> void:
	if not condition:
		failed = true
		push_error(message)

func run_check() -> void:
	var scene = load("res://scenes/Main.tscn").instantiate()
	scene.backend_url = "http://127.0.0.1:65534"
	root.add_child(scene)
	await physics_frame
	await physics_frame
	var actor: CharacterBody3D = scene.district.runner
	actor.set_physics_process(false)
	scene.set_process(false)
	scene.district.set_physics_process(false)
	var at := Transform3D.IDENTITY
	at.origin = Vector3(10, 0.05, 9)
	require(actor.test_move(at, Vector3(0, 0, 4)), "Canal bank must block entry into the gap")
	at.origin = Vector3(0, 0.05, 10)
	require(not actor.test_move(at, Vector3(0, 0, 11)), "Central bridge must remain traversable")
	at.origin = Vector3(0, 0.05, 15)
	require(actor.test_move(at, Vector3(4, 0, 0)), "Bridge side railing must block falling")
	at.origin = Vector3(9, 0.05, 1)
	require(not actor.test_move(at, Vector3(0, 0, -3)), "Workshop doorway must remain open")
	at.origin = Vector3(9, 0.05, -4)
	require(actor.test_move(at, Vector3(7, 0, 0)), "Expanded workshop walls must be solid")
	var space: PhysicsDirectSpaceState3D = scene.district.get_world_3d().direct_space_state
	var gap := PhysicsRayQueryParameters3D.create(Vector3(10, 2, 15), Vector3(10, -1, 15))
	require(space.intersect_ray(gap).is_empty(), "Canal gap must have no invisible walkable floor")
	var bridge := PhysicsRayQueryParameters3D.create(Vector3(0, 2, 15), Vector3(0, -1, 15))
	require(not space.intersect_ray(bridge).is_empty(), "Bridge must have a solid deck")
	var seam := PhysicsRayQueryParameters3D.create(Vector3(0, 2, 11.5), Vector3(0, -1, 11.5))
	var first: Dictionary = space.intersect_ray(seam)
	seam.exclude = [first.rid]
	require(space.intersect_ray(seam).is_empty(), "Bridge approach must not overlap another floor")
	scene.world_loaded = true
	for id in [1, 2]:
		var patrol: Dictionary = scene.district.patrols[id]
		scene.player.position = Vector2.ZERO
		var before: Vector3 = patrol.person.position
		scene.district._physics_process(0.5)
		require(patrol.person.position != before, "NPC must patrol an empty shop")
		scene.player.position = Vector2(patrol.center, -4) / 0.025
		scene.district._update_roofs(0.1)
		var roof_material: StandardMaterial3D = scene.district.shop_roofs[id].material
		require(roof_material.albedo_color.a < 1.0 and roof_material.albedo_color.a > 0.04, "Roof must fade gradually on entry")
		scene.district._update_roofs(0.5)
		require(is_equal_approx(roof_material.albedo_color.a, 0.04), "Occupied shop roof must become transparent")
		require(scene.district.shop_roofs[3 - id].material.albedo_color.a == 1.0, "Other shop roof must remain opaque")
		before = patrol.person.position
		scene.district._physics_process(0.5)
		require(patrol.person.position == before and not patrol.person.walking, "NPC must stop on store entry")
		scene.chat_windows[id].close_chat()
		scene.district._physics_process(0.5)
		require(patrol.person.position == before, "NPC must stay stopped after chat closes until store exit")
		scene._update_current_npc()
		require(scene.current_npc.npc_id == id, "Store interaction must track its roaming NPC")
		scene.player.position = Vector2.ZERO
		scene.district._update_roofs(0.5)
		require(roof_material.albedo_color.a == 1.0, "Roof must return to full opacity on exit")
		scene.district._physics_process(0.5)
		require(patrol.person.position != before, "NPC must resume on store exit")
	scene._set_paused(true)
	var stopped: Vector3 = scene.district.patrols[1].person.position
	scene.district._physics_process(0.5)
	require(scene.district.patrols[1].person.position == stopped, "Pause must freeze patrols")
	scene.position_busy = true
	scene._process(0)
	require(not scene.restart_button.disabled, "Autosave must not flicker the restart button")
	scene._restart_game()
	require(scene.restart_queued, "Restart must queue behind an in-flight save")
	scene.restart_queued = false
	scene.position_busy = false
	scene._set_paused(false)
	if DisplayServer.get_name() != "headless":
		for i in 10: await process_frame
		await RenderingServer.frame_post_draw
		var screenshot := root.get_texture().get_image()
		screenshot.save_png("/tmp/neon-district-3d.png")
		var colors := {}
		for x in range(0, screenshot.get_width(), 32):
			for y in range(0, screenshot.get_height(), 32): colors[screenshot.get_pixel(x, y).to_html()] = true
		require(colors.size() > 30, "Rendered viewport must not be blank")
		actor.position = Vector3(0, 0.05, 24)
		scene.district.camera.position = actor.position + Vector3(0, 15, 20)
		for i in 10: await process_frame
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/neon-district-bridges.png")
		scene._set_paused(true)
		await process_frame
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/neon-district-pause.png")
		scene._set_paused(false)
		for id in [1, 2]:
			scene.player.position = Vector2(scene.district.patrols[id].center, -4) / 0.025
			actor.position = Vector3(scene.district.patrols[id].center, 0, -4)
			scene.district.camera.position = actor.position + Vector3(0, 15, 20)
			scene.district._update_roofs(0.5)
			for i in 10: await process_frame
			await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png("/tmp/neon-shop-roof-%s.png" % id)
	if not failed: print("PASS: bridges, shops, patrols, pause, queued restart and roof fade/restore")
	quit(1 if failed else 0)
