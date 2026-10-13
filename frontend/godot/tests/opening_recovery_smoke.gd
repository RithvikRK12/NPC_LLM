extends SceneTree
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var preview=load("res://scenes/cutscenes/opening/OpeningPreview.tscn").instantiate(); root.add_child(preview)
	preview.session.set_process(false)
	var blocker:=StaticBody2D.new(); var collision:=CollisionShape2D.new(); var shape:=RectangleShape2D.new(); shape.size=Vector2(64,32); collision.shape=shape; blocker.add_child(collision); blocker.position=Vector2(0,3740); preview.view.world.add_child(blocker)
	await physics_frame; await physics_frame
	preview.director.seek(56)
	await physics_frame; await physics_frame
	var ok: bool=preview.session.recovery_failed and preview.player.position==preview.beach.marker("SafeFallback")
	preview.director.advance_clock(4,false)
	await physics_frame
	ok=ok and preview.player.position==preview.beach.marker("SafeFallback") and preview.player.control_enabled
	print("PASS " if ok else "FAIL ","Unexpected recovery obstruction uses one bounded fallback and a safe handoff")
	preview.restart()
	ok=ok and not preview.session.recovery_failed
	preview.queue_free(); await process_frame; await process_frame
	quit(0 if ok else 1)
