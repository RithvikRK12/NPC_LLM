extends RefCounted
# One ledger per loaded game, shared by every state-bearing transport. Complete
# label maps do not imply a response contains every resource's snapshot.
var game_scope := ""
var revisions: Dictionary = {}
var values: Dictionary = {}
var consumed_activities: Dictionary = {}
const WORLD_FIELDS := ["player_position", "opening_capability", "opening_state", "opening_version", "map_version", "map_recovery_notice", "salvage_ids"]

func reset(scope: String) -> void:
	game_scope = scope
	revisions.clear()
	values.clear()
	consumed_activities.clear()

func apply(data: Dictionary) -> Dictionary:
	var scope := str(data.get("game_scope", ""))
	if scope.is_empty() or scope != game_scope: return {}
	var result := data.duplicate(true)
	var labels: Dictionary = data.get("state_revisions", {})
	# Versioned chat returns the typed RevisionSet; world/encounter snapshots
	# retain their flat revision map during client migration.
	if labels.get("resources") is Dictionary: labels = labels.resources
	_filter_fields(result, data, labels, "world", WORLD_FIELDS)
	_filter_fields(result, data, labels, "inventory:player", ["player_inventory"])
	_filter_fields(result, data, labels, "quest:legacy", ["quest_status", "quest_progress"])
	_filter_fields(result, data, labels, "quest:bow", ["bow_quest"])
	_filter_fields(result, data, labels, "quest:ship_repair", ["ship_repair"])
	_filter_fields(result, data, labels, "activity:ship_inspection", ["craftsman_encounter"])
	_filter_fields(result, data, labels, "encounter:gatherer", ["gatherer_encounter"])
	if data.has("npc"):
		var npc := _npc(data.npc, labels)
		if npc.is_empty(): result.erase("npc")
		else: result.npc = npc
	if data.has("npcs"):
		var npcs: Array = []
		for incoming in data.npcs:
			var npc := _npc(incoming, labels)
			if not npc.is_empty(): npcs.append(npc)
		result.npcs = npcs
	# Cached values retain the server labels that actually accompanied them.
	result.state_revisions = labels.duplicate(true)
	for resource in revisions: result.state_revisions[resource] = revisions[resource]
	return result

func _filter_fields(result: Dictionary, data: Dictionary, labels: Dictionary, resource: String, fields: Array) -> void:
	var incoming: Dictionary = {}
	for field in fields:
		result.erase(field)
		if data.has(field): incoming[field] = data[field]
	if incoming.is_empty(): return
	var revision: Variant = labels.get(resource)
	# JSON integers arrive as floats. Reject fractions, negatives and booleans.
	if not (revision is int or revision is float): return
	if not is_finite(float(revision)) or float(revision) < 0 or float(revision) != floor(float(revision)): return
	if not revisions.has(resource) or int(revision) > int(revisions[resource]):
		revisions[resource] = int(revision)
		values[resource] = incoming.duplicate(true)
	if values.has(resource): result.merge(values[resource].duplicate(true), true)

func _npc(incoming: Dictionary, labels: Dictionary) -> Dictionary:
	var id := int(incoming.get("id", 0))
	if id <= 0: return {}
	var result: Dictionary = {}
	var social := incoming.duplicate(true)
	social.erase("inventory")
	_filter_fields(result, {"npc":social}, labels, "npc:%d" % id, ["npc"])
	var filtered_inventory: Dictionary = {}
	if incoming.has("inventory"):
		_filter_fields(filtered_inventory, incoming, labels, "inventory:npc:%d" % id, ["inventory"])
	var npc: Dictionary = result.get("npc", {"id":id})
	if filtered_inventory.has("inventory"): npc.inventory = filtered_inventory.inventory
	return npc if result.has("npc") or filtered_inventory.has("inventory") else {}

func consume_activity(resource: String, scope: String, state: Dictionary) -> bool:
	# These are existing authoritative activity snapshots, never dialogue text.
	if scope.is_empty() or not state.has("revision"): return false
	var revision: Variant = state.revision
	if not (revision is int or revision is float) or not is_finite(float(revision)) or float(revision) < 0 or float(revision) != floor(float(revision)): return false
	var key := scope + ":" + resource
	if int(revision) <= int(consumed_activities.get(key, -1)): return false
	consumed_activities[key] = int(revision)
	return true
