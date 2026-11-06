extends Node2D
# Encounter-local simulation. The encounter calls advance only while unpaused.
signal health_changed(hearts: int)
signal defeated
signal boundary_reached

var player: CharacterBody2D
var boars: Array = []
var layout: Resource
var bounds := Rect2()
var hearts := 3
var enabled := false
var facing := Vector2.LEFT
var attack_owner: Node = null
var immunity := 0.0
var _attack_gap := 1.0
var _swing := -1.0
var _swing_direction := Vector2.LEFT
var _hit: Dictionary = {}
var _defeat_emitted := false
var _edge_notice := 0.0
var _walls: StaticBody2D
var _audio: AudioStreamPlayer
var _sounds: Dictionary = {}

func configure(actor: CharacterBody2D, enemies: Array, world_layout: Resource, arena: Rect2) -> void:
	player = actor; boars = enemies; layout = world_layout; bounds = arena
	z_index = 40
	_build_walls()
	_audio = AudioStreamPlayer.new()
	_audio.volume_db = -18
	add_child(_audio)
	for kind in ["slash", "hit", "warning"]: _sounds[kind] = _make_sound(kind)

func _build_walls() -> void:
	if is_instance_valid(_walls): _walls.queue_free()
	_walls = StaticBody2D.new()
	_walls.collision_layer = 0; _walls.collision_mask = 0
	add_child(_walls)
	for rect in [Rect2(bounds.position-Vector2(16,16),Vector2(bounds.size.x+32,16)), Rect2(Vector2(bounds.position.x-16,bounds.end.y),Vector2(bounds.size.x+32,16)), Rect2(bounds.position-Vector2(16,0),Vector2(16,bounds.size.y)), Rect2(Vector2(bounds.end.x,bounds.position.y),Vector2(16,bounds.size.y))]:
		var collider := CollisionShape2D.new()
		var shape := RectangleShape2D.new()
		shape.size = rect.size
		collider.shape = shape; collider.position = rect.get_center()
		_walls.add_child(collider)

func reset() -> void:
	stop()
	hearts = 3; immunity = 0; facing = Vector2.LEFT
	_defeat_emitted = false; _edge_notice = 0
	for boar in boars: boar.reset_at(boar.spawn_position)
	health_changed.emit(hearts)

func start() -> void:
	enabled = true; _attack_gap = 1.0; _swing = -1; _hit.clear()
	attack_owner = null
	if is_instance_valid(_walls): _walls.collision_layer = 1
	for boar in boars:
		boar.active = boar.health > 0
		if boar.active: boar.state = "approach"; boar.timer = 0

func stop() -> void:
	enabled = false; _swing = -1; _hit.clear(); attack_owner = null
	if is_instance_valid(_walls): _walls.collision_layer = 0
	for boar in boars: boar.active = false; boar.velocity = Vector2.ZERO
	if is_instance_valid(player): player.modulate = Color.WHITE
	if is_instance_valid(_audio): _audio.stop()
	queue_redraw()

func attack() -> bool:
	if not enabled or hearts <= 0 or _swing >= 0: return false
	_swing = 0; _swing_direction = facing.normalized(); _hit.clear()
	play_sound("slash")
	return true

func take_damage(direction: Vector2) -> void:
	if not enabled or immunity > 0 or hearts <= 0: return
	hearts -= 1; immunity = 1.0
	if direction.length_squared() > 0: player.move_and_collide(direction.normalized() * 14.0)
	play_sound("hit")
	health_changed.emit(hearts)
	if hearts == 0:
		stop()
		if not _defeat_emitted:
			_defeat_emitted = true
			defeated.emit()

func claim_attack(boar: Node) -> bool:
	if not enabled or attack_owner != null or _attack_gap > 0: return false
	attack_owner = boar
	return true

func release_attack(boar: Node) -> void:
	if attack_owner == boar:
		attack_owner = null; _attack_gap = 0.30

func advance(delta: float) -> void:
	if not enabled: return
	immunity = maxf(0, immunity-delta)
	_attack_gap = maxf(0, _attack_gap-delta)
	_edge_notice = maxf(0, _edge_notice-delta)
	if player.velocity.length_squared() > 1: facing = player.velocity.normalized()
	player.modulate = Color(1,0.60,0.55) if immunity > 0 and fmod(immunity,0.16) > 0.08 else Color.WHITE
	var interior := bounds.grow(-15)
	if not interior.has_point(player.position) and player.velocity.length_squared() > 1 and _edge_notice <= 0:
		_edge_notice = 2; boundary_reached.emit()
	# Incoming strikes resolve first. Defeat stops this step before outgoing hits,
	# so a simultaneous last-heart/last-boar event cannot award victory.
	for boar in boars:
		boar.advance(delta, attack_owner == null and _attack_gap <= 0)
		if not enabled: return
	if Input.is_action_just_pressed("melee_attack"): attack()
	if _swing >= 0:
		var previous := _swing
		_swing += delta
		if _swing >= 0.10 and previous < 0.22:
			for boar in boars:
				if boar.health <= 0 or _hit.has(boar.get_instance_id()): continue
				var offset: Vector2 = boar.position-player.position
				var reach := offset.dot(_swing_direction)
				var lateral := absf(offset.cross(_swing_direction))
				if reach >= -4 and reach <= 52 and lateral <= 24:
					_hit[boar.get_instance_id()] = true
					boar.take_hit(_swing_direction)
		if _swing >= 0.45: _swing = -1
	queue_redraw()

func _draw() -> void:
	if not enabled or not is_instance_valid(player): return
	var at := to_local(player.global_position) + Vector2(0,-8)
	# The small blade remains visible while equipped.
	var hand := at + facing * 13
	draw_line(hand, hand + facing * 9, Color("dce7df"), 3)
	draw_line(hand-facing*3, hand, Color("8c633d"), 4)
	if _swing >= 0.10 and _swing < 0.22:
		var angle := _swing_direction.angle()
		draw_arc(at, 36, angle-0.75, angle+0.75, 9, Color("fff0b4"), 4, false)
		draw_arc(at, 43, angle-0.50, angle+0.50, 7, Color(1,1,0.85,0.7), 2, false)

func play_sound(kind: String) -> void:
	if not is_instance_valid(_audio) or not _sounds.has(kind): return
	_audio.stream = _sounds[kind]; _audio.play()

func _make_sound(kind: String) -> AudioStreamWAV:
	var stream := AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS; stream.mix_rate = 22050
	var seconds := 0.15 if kind == "warning" else 0.07
	var data := PackedByteArray()
	var samples := int(seconds * 22050)
	data.resize(samples * 2)
	for i in range(samples):
		var t := float(i) / 22050
		var envelope := (1.0-float(i)/samples) * minf(1,t*300)
		var frequency := 105.0 if kind == "warning" else (420.0 if kind == "slash" else 170.0)
		var sample := sin(TAU*frequency*t + sin(t*91)*2) * envelope * 0.5
		data.encode_s16(i*2,int(sample*32767))
	stream.data = data
	return stream
