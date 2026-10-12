extends Node3D

var controller: Node
var runner: CharacterBody3D
var camera: Camera3D
var pickup: Node3D
var concrete: StandardMaterial3D
var steel: StandardMaterial3D
var cyan: StandardMaterial3D
var amber: StandardMaterial3D
var glass: StandardMaterial3D
var elapsed := 0.0
var camera_distance := 1.0
var patrols: Dictionary = {}
var shop_roofs: Dictionary = {}

func mat(color: String, metallic := 0.0, roughness := 0.7, glow := 0.0) -> StandardMaterial3D:
	var result := StandardMaterial3D.new()
	result.albedo_color = Color(color)
	result.metallic = metallic
	result.roughness = roughness
	if glow > 0:
		result.emission_enabled = true
		result.emission = Color(color)
		result.emission_energy_multiplier = glow
	return result

func box(at: Vector3, size: Vector3, material: Material, solid := false) -> MeshInstance3D:
	var mesh := MeshInstance3D.new()
	var shape := BoxMesh.new()
	shape.size = size
	mesh.mesh = shape
	mesh.material_override = material
	mesh.position = at
	add_child(mesh)
	if solid:
		var body := StaticBody3D.new()
		var collider := CollisionShape3D.new()
		var collision := BoxShape3D.new()
		collision.size = size
		collider.shape = collision
		body.add_child(collider)
		mesh.add_child(body)
	return mesh

func weathered(material: StandardMaterial3D, base: Color, scale_value: float) -> void:
	var noise := FastNoiseLite.new()
	noise.seed = 71
	noise.frequency = 0.065
	noise.fractal_octaves = 4
	var texture := NoiseTexture2D.new()
	texture.width = 256
	texture.height = 256
	texture.seamless = true
	texture.noise = noise
	var ramp := Gradient.new()
	ramp.set_color(0, base.darkened(0.18))
	ramp.set_color(1, base.lightened(0.06))
	texture.color_ramp = ramp
	material.albedo_color = Color.WHITE
	material.albedo_texture = texture
	material.uv1_triplanar = true
	material.uv1_world_triplanar = true
	material.uv1_scale = Vector3.ONE * scale_value
	var normal := NoiseTexture2D.new()
	normal.width = 256
	normal.height = 256
	normal.seamless = true
	normal.noise = noise
	normal.as_normal_map = true
	normal.bump_strength = 2.0
	material.normal_enabled = true
	material.normal_texture = normal
	material.normal_scale = 0.18

func pipe(at: Vector3, height: float, radius: float) -> void:
	var mesh := MeshInstance3D.new()
	var cylinder := CylinderMesh.new()
	cylinder.top_radius = radius
	cylinder.bottom_radius = radius
	cylinder.height = height
	mesh.mesh = cylinder
	mesh.position = at
	mesh.material_override = steel
	add_child(mesh)
	for y in [-height * 0.4, 0.0, height * 0.4]:
		var ring := MeshInstance3D.new()
		var torus := TorusMesh.new()
		torus.inner_radius = radius
		torus.outer_radius = radius + 0.07
		ring.mesh = torus
		ring.position = at + Vector3(0, y, 0)
		ring.material_override = concrete
		add_child(ring)

func street_details(x: float, z: float) -> void:
	# Service cabinets, vents and rooftop ductwork give the architecture readable scale.
	box(Vector3(x, 0.85, z), Vector3(1.2, 1.7, 0.65), steel, true)
	box(Vector3(x, 1.2, z + 0.34), Vector3(0.75, 0.4, 0.025), cyan)
	for i in 6:
		box(Vector3(x, 0.25 + i * 0.1, z + 0.34), Vector3(0.85, 0.035, 0.04), concrete)
	box(Vector3(x + 2, 0.28, z), Vector3(1.4, 0.56, 1), concrete, true)
	box(Vector3(x + 2, 0.58, z), Vector3(1.5, 0.05, 1.1), steel)

func vehicle(at: Vector3, color: String) -> void:
	var paint := mat(color, 0.7, 0.25)
	box(at + Vector3(0, 0.55, 0), Vector3(2, 0.65, 4), paint, true)
	box(at + Vector3(0, 1.05, -0.2), Vector3(1.7, 0.55, 1.9), glass, true)
	box(at + Vector3(0, 1.35, -0.2), Vector3(1.8, 0.1, 2), paint)
	for side in [-1, 1]:
		box(at + Vector3(side * 0.7, 0.63, 2.02), Vector3(0.4, 0.12, 0.05), amber)
		box(at + Vector3(side * 1.02, 0.4, -1.15), Vector3(0.2, 0.65, 0.7), steel)
		box(at + Vector3(side * 1.02, 0.4, 1.15), Vector3(0.2, 0.65, 0.7), steel)
	box(at + Vector3(0, 0.24, 0), Vector3(1.8, 0.04, 3.5), cyan)

func light(at: Vector3, color: Color, energy := 2.0, radius := 8.0) -> void:
	var lamp := OmniLight3D.new()
	lamp.position = at
	lamp.light_color = color
	lamp.light_energy = energy
	lamp.omni_range = radius
	add_child(lamp)

func sign_text(caption: String, at: Vector3, color: Color, size := 48) -> Label3D:
	var label := Label3D.new()
	label.text = caption
	label.position = at
	label.font_size = size
	label.pixel_size = 0.012
	label.modulate = color
	label.outline_size = 5
	label.no_depth_test = false
	add_child(label)
	return label

func rail(a: Vector3, b: Vector3) -> void:
	var length := a.distance_to(b)
	var center := (a + b) / 2.0
	var along_x := absf(a.x - b.x) > absf(a.z - b.z)
	var size := Vector3(length, 1.1, 0.18) if along_x else Vector3(0.18, 1.1, length)
	# Continuous collider and mesh close every gap between support posts.
	box(center + Vector3(0, 0.55, 0), size, steel, true)
	box(center + Vector3(0, 1.12, 0), Vector3(size.x, 0.035, size.z), cyan)
	for i in range(int(length / 2.0) + 1):
		box(a.lerp(b, float(i) / maxf(1, floor(length / 2))) + Vector3(0, 0.65, 0), Vector3(0.25, 1.3, 0.25), concrete)

func shop(x: float, name_text: String, accent: StandardMaterial3D) -> void:
	var first_child := get_child_count()
	# Open south entrance: rear and side walls are solid; the interior is walkable.
	box(Vector3(x, -0.015, -4.5), Vector3(7, 0.04, 7), steel)
	box(Vector3(x, 2.1, -8), Vector3(7.4, 4.2, 0.35), concrete, true)
	for side in [-1, 1]:
		box(Vector3(x + side * 3.6, 2.1, -4.5), Vector3(0.35, 4.2, 7), concrete, true)
		box(Vector3(x + side * 2.7, 1.5, -1), Vector3(1.8, 3, 0.25), glass, true)
	var roof_material := steel.duplicate() as StandardMaterial3D
	var roof := box(Vector3(x, 4.35, -4.5), Vector3(7.6, 0.3, 7.6), roof_material)
	var fascia := box(Vector3(x, 3.6, -1), Vector3(7.5, 0.7, 0.6), roof_material)
	shop_roofs[1 if x > 0 else 2] = {"material": roof_material, "meshes": [roof, fascia]}
	var trim_material := accent.duplicate() as StandardMaterial3D
	box(Vector3(x, 3.19, -0.65), Vector3(7.2, 0.055, 0.055), trim_material)
	var sign_label := sign_text(name_text, Vector3(x, 3.6, -0.65), accent.albedo_color, 44)
	shop_roofs[1 if x > 0 else 2].trim_material = trim_material
	shop_roofs[1 if x > 0 else 2].sign_label = sign_label
	box(Vector3(x, 0.6, -6.7), Vector3(4.7, 1.2, 0.8), steel, true)
	for offset in [-1.5, 0.0, 1.5]:
		box(Vector3(x + offset, 1.65, -6.85), Vector3(0.9, 0.6, 0.12), accent)
	light(Vector3(x, 2.8, -4), accent.albedo_color, 2.5, 7)
	pipe(Vector3(x - 3.3, 2, -0.8), 4, 0.12)
	street_details(x + 4.5, -1.7)
	for side in [-1, 1]:
		box(Vector3(x + side * 2.8, 2, -7.65), Vector3(0.65, 2.7, 0.4), steel)
		for i in 8: box(Vector3(x + side * 2.8, 0.9 + i * 0.29, -7.4), Vector3(0.48, 0.035, 0.025), accent)
	# Expand around the entrance; mesh children carry their collision shapes with them.
	for index in range(first_child, get_child_count()):
		var child := get_child(index) as Node3D
		child.position.x = x + (child.position.x - x) * 1.5
		child.position.z = -1 + (child.position.z + 1) * 1.6
		child.scale *= Vector3(1.5, 1, 1.6)

func tower(x: float, z: float, width: float, height: float, depth: float) -> void:
	box(Vector3(x, height / 2, z), Vector3(width, height, depth), concrete, true)
	box(Vector3(x, height + 0.2, z), Vector3(width + 0.3, 0.4, depth + 0.3), steel)
	for level in range(2, int(height), 3):
		box(Vector3(x, level, z + depth / 2 + 0.015), Vector3(width - 0.6, 0.8, 0.03), glass)
		for column in range(int(width)):
			if (column + level + int(x)) % 3 != 0:
				box(Vector3(x - width / 2 + column + 0.5, level, z + depth / 2 + 0.04), Vector3(0.55, 0.55, 0.04), amber if column % 3 == 0 else cyan)
	for side in [-1, 1]:
		box(Vector3(x + side * width * 0.4, height / 2, z + depth / 2 + 0.07), Vector3(0.13, height, 0.14), steel)
	pipe(Vector3(x - width * 0.3, height / 2, z + depth / 2 + 0.23), height, 0.17)
	box(Vector3(x, height + 0.8, z), Vector3(2.8, 1.2, 2), steel)
	for i in 5: box(Vector3(x - 1 + i * 0.5, height + 1.44, z), Vector3(0.2, 0.08, 1.8), concrete)
	box(Vector3(x, 1.3, z + depth / 2 + 0.03), Vector3(1.8, 2.6, 0.12), steel)

func _ready() -> void:
	concrete = mat("424c52", 0.15, 0.84)
	weathered(concrete, Color("545957"), 0.3)
	steel = mat("28343b", 0.75, 0.32)
	cyan = mat("46bfb9", 0.3, 0.3, 2.0)
	amber = mat("e1b477", 0.2, 0.4, 1.6)
	glass = mat("19383e", 0.7, 0.16)
	var world := WorldEnvironment.new()
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color("141e29")
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color("8aacc2")
	environment.ambient_light_energy = 0.4
	environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	environment.fog_enabled = true
	environment.fog_light_color = Color("374852")
	environment.fog_density = 0.006
	environment.glow_enabled = true
	world.environment = environment
	add_child(world)
	var moon := DirectionalLight3D.new()
	moon.rotation_degrees = Vector3(-48, -28, 0)
	moon.light_color = Color("adbdce")
	moon.light_energy = 0.85
	moon.shadow_enabled = true
	moon.directional_shadow_max_distance = 90
	add_child(moon)
	var ground := mat("39444a", 0.35, 0.32)
	weathered(ground, Color("414747"), 0.65)
	# Two banks separated by a genuine void; only the bridges have floor colliders.
	box(Vector3(0, -0.3, -17), Vector3(112, 0.6, 56), ground, true)
	box(Vector3(0, -0.3, 37), Vector3(112, 0.6, 34), ground, true)
	box(Vector3(0, -2.2, 15.5), Vector3(112, 0.15, 9), glass)
	for x in [-24.0, 0.0, 24.0]:
		box(Vector3(x, -0.16, 15.5), Vector3(5, 0.32, 9), steel, true)
		for side in [-1, 1]: rail(Vector3(x + side * 2.5, 0, 11), Vector3(x + side * 2.5, 0, 20))
		for z in range(12, 20): box(Vector3(x, 0.015, z), Vector3(4.7, 0.03, 0.08), concrete)
	for z in [11.0, 20.0]:
		for ends in [Vector2(-56, -26.5), Vector2(-21.5, -2.5), Vector2(2.5, 21.5), Vector2(26.5, 56)]:
			rail(Vector3(ends.x, 0, z), Vector3(ends.y, 0, z))
	for x in [-56.0, 56.0]: rail(Vector3(x, 0, -45), Vector3(x, 0, 54))
	for z in [-45.0, 54.0]: rail(Vector3(-56, 0, z), Vector3(56, 0, z))
	# Pavement joints, curbs and illuminated road markers are actual geometry.
	for x in range(-54, 56, 3):
		box(Vector3(x, 0.005, -16), Vector3(0.025, 0.01, 54), steel)
	for z in range(-42, 11, 3):
		box(Vector3(0, 0.006, z), Vector3(110, 0.012, 0.025), steel)
	for x in range(-50, 54, 4):
		box(Vector3(x, 0.018, 3), Vector3(1.7, 0.03, 0.08), amber)
		box(Vector3(x, 0.018, 8), Vector3(1.7, 0.03, 0.08), cyan)
	shop(9, "TECHSMITH", amber)
	shop(-10.75, "DATA EXCHANGE", cyan)
	for x in [-43.0, -30.0, -16.0, 0.0, 16.0, 31.0, 45.0]:
		tower(x, -21, 9, 12 + fmod(absf(x) * 2, 18), 10)
		tower(x, -39, 10, 23 + fmod(absf(x), 16), 9)
		tower(x, 43, 9, 9 + fmod(absf(x), 9), 10)
	for x in [-43.0, -29.0, 29.0, 43.0]: tower(x, -4, 8, 8, 9)
	vehicle(Vector3(-20, 0, 5), "653d43")
	vehicle(Vector3(19, 0, 5), "737f76")
	vehicle(Vector3(35, 0, 28), "aa915c")
	sign_text("TRANSIT / 03", Vector3(0, 5, -15.8), Color("dfa883"), 72)
	for x in range(-48, 53, 12):
		for z in [9.0, 23.0]:
			box(Vector3(x, 2.2, z), Vector3(0.15, 4.4, 0.15), steel, true)
			box(Vector3(x, 4.4, z), Vector3(1.8, 0.1, 0.35), amber)
			light(Vector3(x, 3.8, z), Color("e4c59a"), 2.0, 9)
	# Utility cabinet and visible cable spool at the authoritative pickup location.
	box(Vector3(-3.5, 0.7, 6), Vector3(1, 1.4, 0.65), steel, true)
	box(Vector3(-3.5, 1.0, 6.34), Vector3(0.6, 0.35, 0.035), cyan)
	pickup = Node3D.new()
	pickup.position = Vector3(-1.75, 0.45, 6)
	add_child(pickup)
	var spool := MeshInstance3D.new()
	var torus := TorusMesh.new()
	torus.inner_radius = 0.15
	torus.outer_radius = 0.32
	spool.mesh = torus
	spool.material_override = cyan
	pickup.add_child(spool)
	for spec in [[9.0, -3.0, Color("e1b477")], [-10.75, -3.5, Color("46bfb9")]]:
		var person := preload("res://scripts/human_3d.gd").new()
		person.accent = spec[2]
		person.position = Vector3(spec[0], 0, spec[1])
		person.rotation.y = PI
		add_child(person)
		var body := AnimatableBody3D.new()
		body.sync_to_physics = false
		var shape := CollisionShape3D.new()
		var capsule := CapsuleShape3D.new()
		capsule.radius = 0.3
		capsule.height = 1.8
		shape.shape = capsule
		shape.position.y = 0.9
		body.add_child(shape)
		person.add_child(body)
		var id := 1 if float(spec[0]) > 0 else 2
		patrols[id] = {"person": person, "center": float(spec[0]), "waypoint": 0, "visiting": false,
			"home": person.position,
			"route": [Vector3(spec[0] + 2.4, 0, -4.5), Vector3(spec[0] + 2.4, 0, -8.2),
				Vector3(spec[0] - 2.4, 0, -8.2), Vector3(spec[0] - 2.4, 0, -4.5)]}
	runner = preload("res://scripts/runner_3d.gd").new()
	runner.controller = controller
	add_child(runner)
	camera = Camera3D.new()
	camera.fov = 48
	camera.far = 180
	add_child(camera)
	camera.make_current()
	camera.position = Vector3(0, 15, 20)
	camera.look_at(Vector3(0, 0, -2))

func _process(delta: float) -> void:
	_update_roofs(delta)
	elapsed += delta
	pickup.visible = controller.string_pickup.visible
	pickup.rotation.y += delta
	pickup.position.y = 0.45 + sin(elapsed * 2.5) * 0.1
	var target := runner.position + Vector3(0, 1, -1)
	camera.position = camera.position.lerp(runner.position + Vector3(0, 15, 20) * camera_distance, 1 - exp(-delta * 6))
	camera.look_at(target)

func _update_roofs(delta: float) -> void:
	var occupied := shop_for_position(controller.player.position * 0.025)
	for id in shop_roofs:
		var material: StandardMaterial3D = shop_roofs[id].material
		var target := 0.04 if occupied == id else 1.0
		var opacity := move_toward(material.albedo_color.a, target, delta * 2.5)
		material.albedo_color.a = opacity
		material.transparency = BaseMaterial3D.TRANSPARENCY_DISABLED if opacity >= 1.0 else BaseMaterial3D.TRANSPARENCY_ALPHA
		var trim_material: StandardMaterial3D = shop_roofs[id].trim_material
		trim_material.albedo_color.a = opacity
		trim_material.transparency = material.transparency
		shop_roofs[id].sign_label.modulate.a = opacity
		shop_roofs[id].sign_label.outline_modulate.a = opacity
		# A faded roof must not leave an opaque shadow over the shopkeeper.
		for mesh in shop_roofs[id].meshes:
			mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if opacity >= 1.0 else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF

func _unhandled_input(event: InputEvent) -> void:
	if controller.paused: return
	if event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP: camera_distance = maxf(0.55, camera_distance - 0.1)
		if event.button_index == MOUSE_BUTTON_WHEEL_DOWN: camera_distance = minf(1.35, camera_distance + 0.1)

func shop_for_position(at: Vector2) -> int:
	for id in patrols:
		if absf(at.x - patrols[id].center) < 5.2 and at.y < -0.8 and at.y > -12.0:
			return id
	return 0

func reset_patrols() -> void:
	for id in patrols:
		var patrol: Dictionary = patrols[id]
		patrol.person.position = patrol.home
		patrol.waypoint = 0
		patrol.visiting = false
		controller.npc_nodes[id].position = Vector2(patrol.home.x, patrol.home.z) / 0.025

func _physics_process(delta: float) -> void:
	var visitor := shop_for_position(controller.player.position * 0.025)
	for id in patrols:
		var patrol: Dictionary = patrols[id]
		var person: Node3D = patrol.person
		var visiting: bool = visitor == id
		if patrol.visiting and not visiting:
			controller.chat_windows[id].close_chat()
		patrol.visiting = visiting
		var frozen: bool = visiting or controller.paused or not controller.world_loaded or controller.quitting or controller.restart_dialog.visible
		person.set_process(not controller.paused)
		person.walking = not frozen
		if not frozen:
			var target: Vector3 = patrol.route[patrol.waypoint]
			var direction := target - person.position
			person.position = person.position.move_toward(target, delta * 0.85)
			person.rotation.y = lerp_angle(person.rotation.y, atan2(-direction.x, -direction.z), minf(delta * 5, 1))
			if person.position.distance_to(target) < 0.05:
				patrol.waypoint = (int(patrol.waypoint) + 1) % patrol.route.size()
		controller.npc_nodes[id].position = Vector2(person.position.x, person.position.z) / 0.025
