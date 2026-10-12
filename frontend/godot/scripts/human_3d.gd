extends Node3D

var accent := Color("45dbd2")
var walking := false
var clock := 0.0
var limbs: Array[Node3D] = []

func material(color: Color, metal := 0.0, emission := false) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.metallic = metal
	mat.roughness = 0.48
	mat.emission_enabled = emission
	mat.emission = color
	mat.emission_energy_multiplier = 2.0
	return mat

func part(parent: Node3D, at: Vector3, size: Vector3, mat: Material, rounded := false) -> void:
	var node := MeshInstance3D.new()
	if rounded:
		var mesh := CapsuleMesh.new()
		mesh.radius = 0.5
		mesh.height = 2.0
		node.mesh = mesh
		node.scale = size * Vector3(1, 0.5, 1)
	else:
		var mesh := BoxMesh.new()
		mesh.size = size
		node.mesh = mesh
	node.material_override = mat
	node.position = at
	parent.add_child(node)

func _ready() -> void:
	var suit := material(Color("242d33"), 0.35)
	var armor := material(Color("47535c"), 0.65)
	var skin := material(Color("ad806b"))
	var glow := material(accent, 0.3, true)
	part(self, Vector3(0, 1.22, 0), Vector3(0.48, 0.65, 0.28), suit, true)
	part(self, Vector3(0, 1.32, -0.14), Vector3(0.38, 0.27, 0.07), armor)
	part(self, Vector3(0, 1.4, -0.19), Vector3(0.27, 0.035, 0.025), glow)
	part(self, Vector3(0, 1.75, 0), Vector3(0.26, 0.36, 0.27), skin, true)
	part(self, Vector3(0, 1.85, 0.015), Vector3(0.29, 0.23, 0.29), suit, true)
	part(self, Vector3(0, 1.77, -0.139), Vector3(0.24, 0.065, 0.035), glow)
	part(self, Vector3(0, 1.25, 0.2), Vector3(0.32, 0.43, 0.17), armor)
	for side in [-1.0, 1.0]:
		var leg := Node3D.new()
		leg.position = Vector3(side * 0.14, 0.95, 0)
		add_child(leg)
		limbs.append(leg)
		part(leg, Vector3(0, -0.39, 0), Vector3(0.19, 0.79, 0.21), suit, true)
		part(leg, Vector3(0, -0.45, -0.1), Vector3(0.18, 0.19, 0.1), armor)
		part(leg, Vector3(0, -0.84, -0.06), Vector3(0.23, 0.18, 0.36), suit)
		var arm := Node3D.new()
		arm.position = Vector3(side * 0.32, 1.46, 0)
		add_child(arm)
		limbs.append(arm)
		part(arm, Vector3(0, -0.27, 0), Vector3(0.17, 0.63, 0.18), suit, true)
		part(arm, Vector3(0, -0.1, 0), Vector3(0.23, 0.21, 0.25), armor, true)
		part(arm, Vector3(0, -0.56, 0), Vector3(0.14, 0.18, 0.14), skin, true)
		part(arm, Vector3(0, -0.38, -0.1), Vector3(0.14, 0.08, 0.03), glow)

func _process(delta: float) -> void:
	clock += delta
	for i in limbs.size():
		var swing := sin(clock * 9.0) * 0.48 if walking else sin(clock * 1.7) * 0.025
		limbs[i].rotation.x = swing * (1.0 if i == 0 or i == 3 else -1.0)
