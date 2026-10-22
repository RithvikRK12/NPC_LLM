extends SceneTree

const Presenter = preload("res://scripts/conversation_presenter.gd")
const ChatWindow = preload("res://scripts/chat_window.gd")

var passed := 0
var failed := 0
var shown: Array = []

func _initialize() -> void:
	var presenter = Presenter.new()
	presenter.set_npc(1)
	presenter.turn_ready.connect(func(response: Dictionary): shown.append(response))
	presenter.set_context("scope-a", 2, 1)
	presenter.accept(result(2, "b", "full b", ["full ", "b"]))
	check(shown.is_empty(), "out-of-order turn waits for missing sequence")
	presenter.accept(result(1, "a", "full a", ["full", " a"]))
	check(shown.size() == 2 and shown[0].final_dialogue == "full a" and shown[1].final_dialogue == "full b", "final turns display once in sequence order")
	presenter.accept(result(1, "a", "full a", ["full", " a"]))
	check(shown.size() == 2, "delayed duplicate turn ID is ignored")
	if not shown.is_empty(): check("".join(PackedStringArray(shown[0].dialogue_beats)) == shown[0].final_dialogue, "beats preserve exact final dialogue")
	presenter.accept(result(3, "old", "obsolete", ["obsolete"], "old-scope", 2))
	presenter.accept(result(3, "old-epoch", "obsolete", ["obsolete"], "scope-a", 1))
	check(shown.size() == 2, "obsolete scope and epoch are suppressed")
	presenter.accept(result(4, "four", "four", ["four"]))
	presenter.sync_terminal_sequences([{"sequence": 3, "phase": "finalized"}])
	check(shown.size() == 2, "a finalized sequence gap waits for dialogue delivery or history")
	presenter.sync_terminal_sequences([{"sequence": 3, "phase": "invalidated"}])
	check(shown.size() == 3 and shown.size() > 2 and shown[2].final_dialogue == "four", "server invalidation advances a sequence gap")
	var long_text := "A long story, with every detail preserved. ".repeat(600)
	var long_beats := [long_text.substr(0, 7000), long_text.substr(7000)]
	presenter.accept(result(5, "long", long_text, long_beats))
	check(shown.size() == 4 and "".join(PackedStringArray(shown[3].dialogue_beats)) == long_text, "long readable beats reconstruct exact dialogue without truncation")
	check(not shown[3].has("validated_output"), "story text alone does not synthesize item or action metadata")
	presenter.accept(result(7, "queued-old", "old", ["old"]))
	presenter.reset("scope-b", 0, 1)
	presenter.accept(result(5, "old-running", "old", ["old"], "scope-a", 2))
	check(shown.size() == 4, "clear or new game drops queued old beats")
	presenter.free()
	var restored = Presenter.new()
	restored.set_npc(1)
	var restored_shown: Array = []
	restored.turn_ready.connect(func(response: Dictionary): restored_shown.append(response))
	restored.set_context("scope-a", 2, 1)
	restored.sync_terminal_sequences([{"sequence": 1, "phase": "finalized"}, {"sequence": 2, "phase": "invalidated"}])
	restored.sync_history([{"sequence": 1, "player": "hello", "npc": "there"}])
	restored.accept(result(3, "restored-next", "next", ["next"]))
	check(restored_shown.size() == 1 and restored_shown[0].sequence == 3, "history resolves finalized turns and invalidation advances the next gap")
	var truncated_history: Array = []
	for sequence in range(51, 101): truncated_history.append({"sequence": sequence, "player": "p", "npc": "n"})
	var earliest := restored.first_sequence_for_world(truncated_history, [])
	check(earliest == 101, "a capped latest-fifty history starts after its newest saved turn")
	restored.set_context("scope-history", 2, earliest)
	restored.accept(result(101, "after-history-window", "following old history", ["following old history"], "scope-history", 2))
	check(restored_shown.size() == 2 and restored_shown[1].sequence == 101, "turns after a truncated history window are not blocked by old gaps")
	var font: FontFile = load("res://assets/fonts/PixelifySans.ttf")
	var long_beat := "A single server beat that needs several viewport pages. ".repeat(30)
	var visible_pages: Array[String] = ChatWindow.split_dialogue_beats([long_beat], font, 18, 180.0, 2)
	check(visible_pages.size() > 1, "an oversized server beat is split to fit readable viewport pages")
	check("".join(PackedStringArray(visible_pages)) == long_beat, "splitting a server beat preserves every character")
	restored.free()
	print("conversation_presenter_smoke: %d passed, %d failed" % [passed, failed])
	quit(1 if failed > 0 else 0)

func result(sequence: int, turn_id: String, dialogue: String, beats: Array, scope := "scope-a", epoch := 2) -> Dictionary:
	return {"turn": {"turn_id": turn_id, "sequence": sequence, "key": {"game_scope": scope, "npc_id": 1, "epoch": epoch}}, "sequence": sequence, "final_dialogue": dialogue, "dialogue_beats": beats}

func check(condition: bool, label: String = "") -> void:
	if condition: passed += 1
	else:
		failed += 1
		push_error("conversation_presenter_smoke: FAIL " + label)
