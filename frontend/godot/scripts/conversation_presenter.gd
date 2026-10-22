extends Node
## Orders durable finalized replies and emits only replies for the active conversation key.
signal turn_ready(response: Dictionary)

var game_scope := ""
var npc_id := 0
var epoch := 0
var next_sequence := 1
var buffered: Dictionary = {}
var terminal: Dictionary = {}
var seen_turn_ids: Dictionary = {}
var seen_sequences: Dictionary = {}
var history_sequences: Dictionary = {}

func set_context(scope: String, current_epoch: int, first_sequence: int) -> void:
	if scope != game_scope or current_epoch != epoch:
		reset(scope, current_epoch, first_sequence)
	else:
		next_sequence = maxi(next_sequence, first_sequence)
		_drain()

func set_npc(id: int) -> void:
	npc_id = id

func first_sequence_for_world(history: Array, sequences: Array) -> int:
	if not history.is_empty():
		var latest := 0
		for turn in history:
			if turn is Dictionary: latest = maxi(latest, int(turn.get("sequence", 0)))
		if latest > 0: return latest + 1
	var earliest_invalidated := 0
	for entry in sequences:
		if entry is Dictionary and str(entry.get("phase", "")) == "invalidated":
			var sequence := int(entry.get("sequence", 0))
			if sequence > 0: earliest_invalidated = sequence if earliest_invalidated == 0 else mini(earliest_invalidated, sequence)
	return earliest_invalidated if earliest_invalidated > 0 else 1

func accept(response: Dictionary) -> void:
	# The synchronous ChatResponse used by the local playtest predates the
	# sequenced turn envelope. Adapt that response at the presentation boundary
	# so its already-committed reply can still reach the chat window.
	if not response.get("turn") is Dictionary:
		var dialogue := str(response.get("final_dialogue", ""))
		if dialogue.is_empty(): return
		var normalized := response.duplicate(true)
		var scope := str(normalized.get("game_scope", game_scope))
		var response_npc := int(normalized.get("npc", {}).get("id", npc_id))
		var response_epoch := int(normalized.get("conversation_epoch", epoch))
		var sequence := int(normalized.get("sequence", next_sequence))
		normalized["sequence"] = sequence
		if not normalized.get("dialogue_beats", []) is Array or normalized.get("dialogue_beats", []).is_empty():
			normalized["dialogue_beats"] = [dialogue]
		normalized["turn"] = {
			"turn_id": str(normalized.get("turn_id", "sync:%s:%s:%s" % [scope, response_npc, sequence])),
			"sequence": sequence,
			"key": {"game_scope": scope, "npc_id": response_npc, "epoch": response_epoch},
		}
		response = normalized
	var turn: Dictionary = response.get("turn", {})
	var key: Dictionary = turn.get("key", {})
	var scope := str(key.get("game_scope", ""))
	var response_npc := int(key.get("npc_id", -1))
	var response_epoch := int(key.get("epoch", -1))
	var sequence := int(response.get("sequence", turn.get("sequence", -1)))
	var turn_id := str(turn.get("turn_id", ""))
	var dialogue := str(response.get("final_dialogue", ""))
	var beats: Array = response.get("dialogue_beats", [])
	if scope != game_scope or response_npc != npc_id or response_epoch != epoch or sequence < next_sequence or turn_id.is_empty(): return
	if seen_turn_ids.has(turn_id) or seen_sequences.has(sequence) or buffered.has(sequence): return
	if "".join(PackedStringArray(beats.map(func(beat): return str(beat)))) != dialogue: return
	var copy := response.duplicate(true)
	copy["sequence"] = sequence
	buffered[sequence] = copy
	_drain()

func sync_terminal_sequences(sequences: Array) -> void:
	for entry in sequences:
		if entry is Dictionary and str(entry.get("phase", "")) == "invalidated":
			var sequence := int(entry.get("sequence", -1))
			if sequence >= next_sequence: terminal[sequence] = true
	_drain()

func sync_history(turns: Array) -> void:
	for turn in turns:
		if turn is Dictionary:
			var sequence := int(turn.get("sequence", -1))
			if sequence >= next_sequence: history_sequences[sequence] = true
	_drain()

func reset(scope: String, current_epoch: int, first_sequence: int) -> void:
	game_scope = scope
	epoch = current_epoch
	next_sequence = maxi(1, first_sequence)
	buffered.clear()
	terminal.clear()
	seen_turn_ids.clear()
	seen_sequences.clear()
	history_sequences.clear()

func _drain() -> void:
	while true:
		if buffered.has(next_sequence):
			var response: Dictionary = buffered[next_sequence]
			buffered.erase(next_sequence)
			var turn_id := str(response.get("turn", {}).get("turn_id", ""))
			seen_turn_ids[turn_id] = true
			seen_sequences[next_sequence] = true
			turn_ready.emit(response)
			next_sequence += 1
		elif history_sequences.has(next_sequence):
			history_sequences.erase(next_sequence)
			seen_sequences[next_sequence] = true
			next_sequence += 1
		elif terminal.has(next_sequence):
			terminal.erase(next_sequence)
			next_sequence += 1
		else:
			break
