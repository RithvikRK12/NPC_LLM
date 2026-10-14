extends SceneTree
var failures: Array[String] = []
var defeats := 0
func check(ok: bool, label: String) -> void:
	if not ok: failures.append(label); push_error(label)
func _initialize() -> void:
	call_deferred("run")
func steps(combat: Node, seconds: float) -> void:
	for i in range(ceili(seconds / 0.01)): combat.advance(0.01)
func run() -> void:
	if not ResourceLoader.exists("res://scripts/player_combat.gd") or not ResourceLoader.exists("res://scripts/boar.gd"):
		check(false, "Gatherer combat controllers must exist")
		quit(1); return
	var player := CharacterBody2D.new()
	root.add_child(player)
	var foot := CollisionShape2D.new()
	var foot_shape := RectangleShape2D.new()
	foot_shape.size = Vector2(16,12); foot.shape = foot_shape
	player.add_child(foot)
	var combat = load("res://scripts/player_combat.gd").new()
	root.add_child(combat)
	var boars: Array = []
	for i in range(2):
		var boar = load("res://scripts/boar.gd").new()
		root.add_child(boar)
		boar.configure(player, combat, null, Rect2(-200,-200,400,400))
		boar.reset_at(Vector2(28, i * 8))
		boars.append(boar)
	check(boars[0]._shape.shape.size.x>=32, "Larger boar trunk has matching collision")
	combat.configure(player, boars, null, Rect2(-200,-200,400,400))
	combat.defeated.connect(func(): defeats += 1)
	combat.start()
	check(combat.hearts == 3, "Starts with three hearts")
	steps(combat, 0.90)
	check(boars[0].state == "approach" and boars[1].state == "approach", "Safe first second forbids warnings")
	steps(combat, 0.20)
	check((boars[0].state == "windup") != (boars[1].state == "windup"), "Only one boar obtains attack token")
	var owner = boars[0] if boars[0].state == "windup" else boars[1]
	owner.set_dead()
	check(combat.attack_owner == null, "Dying releases the attack token immediately")
	combat.reset(); combat.start()
	for boar in boars: boar.active = false
	combat.facing = Vector2.RIGHT
	check(combat.attack(), "Fresh press starts swing")
	check(not combat.attack(), "Repeated press during swing rejected")
	steps(combat, 0.22)
	check(boars[0].health == 2 and boars[1].health == 2, "One swing hits both overlaps exactly once")
	steps(combat, 0.28)
	# Knockback should not disguise repeated-hit bugs: return targets to the same hit area.
	for boar in boars: boar.position = Vector2(28,0)
	combat.attack(); steps(combat, 0.50)
	for boar in boars: boar.position = Vector2(28,0)
	combat.attack(); steps(combat, 0.50)
	check(boars[0].health == 0 and boars[1].health == 0, "Three separate swings kill each boar")
	check(boars[0].state == "dead" and boars[0].collision_layer == 0, "Corpse harmless and nonblocking")
	combat.take_damage(Vector2.ZERO); combat.take_damage(Vector2.ZERO)
	check(combat.hearts == 2, "Shared immunity prevents simultaneous double damage")
	steps(combat, 1.01); combat.take_damage(Vector2.ZERO)
	steps(combat, 1.01); combat.take_damage(Vector2.ZERO)
	check(combat.hearts == 0 and not combat.enabled and defeats == 1, "Defeat wins when final boars are dead and emits once")
	combat.take_damage(Vector2.ZERO)
	check(defeats == 1, "Stopped combat cannot emit a second defeat")
	combat.reset()
	check(combat.hearts == 3 and boars[0].health == 3 and boars[1].health == 3, "Retry restores all hearts and both boars")
	combat.start(); combat.facing = Vector2.LEFT
	for boar in boars: boar.active = false; boar.position = Vector2(28,0)
	combat.attack(); steps(combat,0.50)
	check(boars[0].health == 3, "Directional swing cannot hit behind the player")
	combat.stop()
	var frozen_state: String = boars[0].state
	steps(combat, 4.0)
	check(boars[0].state == frozen_state and combat.hearts == 3, "Stopped timers and damage remain frozen")
	combat.reset(); combat.start(); player.position = Vector2.ZERO
	boars[0].set_dead()
	boars[1].position = Vector2(28,0); boars[1].health = 1
	boars[1].state = "windup"; boars[1].timer = 0.01; boars[1].facing = Vector2.LEFT
	combat.hearts = 1; combat.immunity = 0; combat.facing = Vector2.RIGHT
	combat.attack(); combat.advance(0.11)
	check(combat.hearts == 0 and boars[1].health == 1 and defeats == 2, "Incoming lethal strike wins over simultaneous final swing")
	combat.reset(); combat.start(); player.position = Vector2.ZERO
	boars[0].position = Vector2(28,0); boars[1].active = false
	steps(combat, 1.10)
	check(boars[0].state == "windup", "Nearby boar visibly warns before attack")
	player.position = Vector2(0,60)
	steps(combat, 0.65)
	check(combat.hearts == 3, "Sidestep evades locked warning direction")
	combat.reset(); combat.start()
	for boar in boars: boar.active = false
	await physics_frame
	player.position = Vector2(160,0)
	player.move_and_collide(Vector2(100,0))
	check(player.position.x <= 193, "Combat boundary physically blocks the player")
	combat.stop()
	await physics_frame
	player.position = Vector2(160,0)
	player.move_and_collide(Vector2(100,0))
	check(player.position.x > 250, "Stopping combat restores free exploration across arena boundary")
	combat.queue_free(); player.queue_free()
	for boar in boars: boar.queue_free()
	await create_timer(0.2).timeout
	if failures.is_empty(): print("PASS gatherer combat: safe start, token, swings, immunity, defeat, retry, direction, stop")
	quit(0 if failures.is_empty() else 1)
