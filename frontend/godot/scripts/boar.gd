extends CharacterBody2D
signal died
const ART_SCALE := 1.8
const ATTACK_REACH := 58.0
const ATTACK_HALF_WIDTH := 26.0
const Router = preload("res://scripts/actor_router.gd")
var player: CharacterBody2D
var combat: Node
var layout: Resource
var bounds := Rect2()
var health := 3
var state := "staging"
var active := false
var facing := Vector2.RIGHT
var spawn_position := Vector2.ZERO
var timer := 0.0
var _flash := 0.0
var _stalled := 0.0
var _router = Router.new()
var _shape: CollisionShape2D

func configure(actor: CharacterBody2D, controller: Node, world_layout: Resource, arena: Rect2) -> void:
	player = actor; combat = controller; layout = world_layout; bounds = arena
	collision_layer = 0; collision_mask = 1
	z_index = 3
	_shape = CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = Vector2(36,20); _shape.shape = shape
	add_child(_shape)

func reset_at(at: Vector2) -> void:
	if is_instance_valid(combat): combat.release_attack(self)
	position = at; spawn_position = at; health = 3; state = "approach"
	active = false; timer = 0; _flash = 0; _stalled = 0
	velocity = Vector2.ZERO; _router.path.clear()
	collision_mask = 1; facing = Vector2.RIGHT
	queue_redraw()

func set_dead() -> void:
	health = 0; state = "dead"; active = false; velocity = Vector2.ZERO
	collision_layer = 0; collision_mask = 0
	_router.path.clear()
	if is_instance_valid(combat): combat.release_attack(self)
	queue_redraw()

func take_hit(direction: Vector2) -> void:
	if health <= 0: return
	health -= 1; _flash = 0.14
	combat.release_attack(self)
	combat.play_sound("hit")
	if health <= 0:
		set_dead(); died.emit(); return
	state = "stagger"; timer = 0.22
	move_and_collide(direction.normalized()*12)
	queue_redraw()

func advance(delta: float, can_attack: bool) -> void:
	if not active or health <= 0: return
	_flash = maxf(0,_flash-delta)
	timer = maxf(0,timer-delta)
	match state:
		"approach":
			var difference := player.position-position
			if difference.length_squared() > 1: facing = difference.normalized()
			if difference.length() <= 45:
				velocity = Vector2.ZERO
				if can_attack and combat.claim_attack(self):
					state = "windup"; timer = 0.70
					combat.play_sound("warning")
			else:
				_approach(delta, difference)
		"windup":
			if timer <= 0:
				state = "strike"; timer = 0.10
				var offset := player.position-position
				if offset.dot(facing) >= -4 and offset.dot(facing) <= ATTACK_REACH and absf(offset.cross(facing)) <= ATTACK_HALF_WIDTH:
					combat.take_damage(facing)
		"strike":
			if timer <= 0:
				state = "recover"; timer = 1.0
				combat.release_attack(self)
		"recover", "stagger":
			if timer <= 0: state = "approach"
	queue_redraw()

func _approach(delta: float, difference: Vector2) -> void:
	var before := position
	if not _router.path.is_empty():
		_router.advance(self, delta, 85)
	else:
		velocity = difference.normalized()*85
		var target := position + velocity*delta
		target = target.clamp(bounds.position+Vector2(20,12), bounds.end-Vector2(20,12))
		move_and_collide(target-position)
	if position.distance_to(before) < 0.05: _stalled += delta
	else: _stalled = 0
	if _stalled > 0.35 and layout != null:
		# Route around scenery to a clear point near the moving player.
		for offset in [Vector2.ZERO,Vector2(24,0),Vector2(-24,0),Vector2(0,24),Vector2(0,-24)]:
			var target: Vector2 = player.position+offset
			if bounds.grow(-12).has_point(target) and _router.set_target(position,target,layout): break
		_stalled = 0

func _draw() -> void:
	var dead := state == "dead"
	var sign_x := 1.0 if facing.x >= 0 else -1.0
	draw_ellipse_shadow(dead)
	if state == "windup" or state == "strike":
		var color := Color(1,0.64,0.15,0.45) if state == "windup" else Color(1,0.22,0.12,0.65)
		var side := facing.orthogonal()*ATTACK_HALF_WIDTH
		draw_colored_polygon(PackedVector2Array([facing*8-side,facing*ATTACK_REACH-side,facing*ATTACK_REACH+side,facing*8+side]),color)
	draw_set_transform(Vector2.ZERO,0,Vector2.ONE*ART_SCALE)
	var body := Color("76513b") if not dead else Color("594a3d")
	if _flash > 0: body = Color("f6dfb4")
	var y := -6.0 if dead else -13.0
	draw_rect(Rect2(-16,y,29,15),Color("352d29"))
	draw_rect(Rect2(-15,y-2,27,13),body)
	draw_rect(Rect2(-10,y-5,18,5),Color("947052") if not dead else body)
	var head_drop := 4.0 if state in ["windup","strike","cinematic_threat"] else 0.0
	var head := Vector2(12*sign_x,y+2+head_drop)
	draw_rect(Rect2(head-Vector2(5,3),Vector2(12,12)),body)
	draw_rect(Rect2(Vector2(18*sign_x-3,y+7+head_drop),Vector2(7,5)),Color("b18a67") if not dead else body)
	draw_rect(Rect2(Vector2(9*sign_x-2,y-6+head_drop),Vector2(5,6)),Color("4b372c"))
	if not dead:
		draw_rect(Rect2(-11,0,5,5),Color("352d29"))
		draw_rect(Rect2(6,0,5,5),Color("352d29"))
		draw_rect(Rect2(Vector2(13*sign_x,y+1+head_drop),Vector2(2,2)),Color("ffda84") if state == "windup" else Color("211c1a"))
		draw_line(Vector2(19*sign_x,y+10+head_drop),Vector2(22*sign_x,y+5+head_drop),Color("e6d2a4"),2)
		if state in ["windup","cinematic_threat"]:
			draw_rect(Rect2(-2,-36,4,9),Color("ffcc56")); draw_rect(Rect2(-2,-25,4,3),Color("ffcc56"))
		if health < 3:
			for i in range(3): draw_rect(Rect2(-10+i*7,-27,5,3),Color("e8c070") if i < health else Color("4a3930"))
	else:
		draw_line(Vector2(12*sign_x,y+1),Vector2(15*sign_x,y+4),Color("261e1b"),1)
		draw_line(Vector2(15*sign_x,y+1),Vector2(12*sign_x,y+4),Color("261e1b"),1)

func draw_ellipse_shadow(dead: bool) -> void:
	draw_set_transform(Vector2(0,3),0,Vector2(1,0.3))
	draw_circle(Vector2.ZERO,(19 if dead else 17)*ART_SCALE,Color(0.08,0.10,0.06,0.28))
	draw_set_transform(Vector2.ZERO)
