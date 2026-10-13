# Process-level quit test; inspect disposable backend after process exits.
extends SceneTree
var scene
var mode := "pending"

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--mode="): mode = arg.trim_prefix("--mode=")
	call_deferred("run_check")

func run_check() -> void:
	scene = load("res://scenes/Main.tscn").instantiate()
	scene.backend_url = "http://127.0.0.1:8001"
	root.add_child(scene)
	if mode == "loading":
		scene._begin_shutdown()
		scene._begin_shutdown()
		print("PASS initial loading repeated quit entered shutdown")
		return
	while not scene.world_loaded or scene._operations_pending(): await process_frame
	scene._restart_game()
	while not scene.world_loaded: await process_frame
	scene.player.position = Vector2(73, 83)
	if mode == "pending":
		var chat = scene.chat_windows[1]
		chat.open_chat()
		chat.transfer_item("food", "to_npc")
		if not chat.pending:
			push_error("Transfer must dispatch before shutdown")
			quit(1)
			return
		scene._begin_shutdown()
		scene._begin_shutdown()
		scene._notification(Node.NOTIFICATION_WM_CLOSE_REQUEST)
		print("PASS repeated quit and window close wait for dispatched gift")
	elif mode == "failure":
		scene.backend_url = "http://127.0.0.1:1"
		scene._begin_shutdown()
		while scene.quitting: await process_frame
		if not scene.retry_button.visible or not scene.menu_layer.visible:
			push_error("Failed save must expose recovery")
			quit(1)
			return
		print("PASS actual failed save kept application open; retrying against disposable backend")
		scene.backend_url = "http://127.0.0.1:8001"
		scene.retry_button.pressed.emit()
	else:
		scene._notification(Node.NOTIFICATION_WM_CLOSE_REQUEST)
		print("PASS window close entered shared shutdown")
