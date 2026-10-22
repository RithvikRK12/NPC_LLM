extends SceneTree

class BootstrapWorld extends "res://scripts/main.gd":
	func _ready() -> void: pass
	func _process(_delta: float) -> void: pass

class RecordingGateway extends Node:
	var backend_url := ""
	var message := ""
	func invalidate(_scope: String, _epoch: int) -> void: pass
	func submit(_scope: String, _epoch: int, _npc: int, text: String) -> String:
		message = text
		return "recorded:request"

func _initialize() -> void:
	call_deferred("run_check")

func run_check() -> void:
	var ui := Control.new()
	root.add_child(ui)
	var chat = preload("res://scripts/chat_window.gd").new()
	chat.npc_id = 1
	chat.npc_name = "Craftsman"
	ui.add_child(chat)
	chat.game_scope = "signal:test"
	chat.sent_game_scope = "signal:test"
	chat.conversation_epoch = 0
	chat.conversation_presenter.set_context("signal:test", 0, 1)
	chat.pending = true
	var result := {"turn": {"turn_id": "signal:turn", "sequence": 1,
		"key": {"game_scope": "signal:test", "npc_id": 1, "epoch": 0}},
		"final_dialogue": "Welcome back.", "dialogue_beats": ["Welcome back."]}
	chat.conversation_gateway.turn_finalized.emit("signal:request", result)
	var ok: bool = not chat.pending and chat.conversation_text().contains("Welcome back.")
	print("Conversation signal integration: ", "PASS" if ok else "FAIL")
	chat.operation = "clear"
	chat._completed(HTTPRequest.RESULT_SUCCESS, 200, PackedStringArray(), JSON.stringify({
		"current_key": {"epoch": 1}, "next_sequence": 7}).to_utf8_buffer())
	chat.pending = true
	result.turn.key.epoch = 1
	result.turn.sequence = 7
	result.turn.turn_id = "after:clear"
	chat.conversation_gateway.turn_finalized.emit("after:clear", result)
	var clear_ok: bool = not chat.pending
	print("Cleared epoch uses server sequence: ", "PASS" if clear_ok else "FAIL")
	var gateway := RecordingGateway.new()
	chat.add_child(gateway)
	chat.conversation_gateway = gateway
	chat.open_chat()
	chat.message_input.text = "Unsent reply"
	chat.transfer_item("water", "to_npc")
	var gift_ok: bool = gateway.message == "I give you water" and chat.message_input.text == "Unsent reply"
	print("Gift uses durable conversation identity: ", "PASS" if gift_ok else "FAIL")
	var world := BootstrapWorld.new()
	root.add_child(world)
	world.world_request = HTTPRequest.new()
	world.add_child(world.world_request)
	world.backend_url = "http://127.0.0.1:1"
	world.chat_windows = {1: chat}
	chat.pending = true
	world._load_world()
	var bootstrap_ok: bool = world.world_busy
	world.world_request.cancel_request()
	world.world_busy = false
	world.world_loaded = true
	world._load_world()
	bootstrap_ok = bootstrap_ok and not world.world_busy
	print("Pending conversation permits bootstrap world only: ", "PASS" if bootstrap_ok else "FAIL")
	world.queue_free()
	ui.queue_free()
	await process_frame
	quit(0 if ok and clear_ok and gift_ok and bootstrap_ok else 1)
