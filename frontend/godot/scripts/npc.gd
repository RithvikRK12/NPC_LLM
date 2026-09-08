extends Area2D

var npc_id: int = 0
var display_name: String = "NPC"
var role_name: String = "npc"
var label: Label


func apply_state(data: Dictionary) -> void:
	var trust := float(data.get("trust", 0.0))
	var fear := float(data.get("fear", 0.0))
	var aggression := float(data.get("aggression", 0.0))
	var curiosity := float(data.get("curiosity", 0.0))
	refresh_label(trust, fear, aggression, curiosity)


func refresh_label(trust: float = 0.0, fear: float = 0.0, aggression: float = 0.0, curiosity: float = 0.0) -> void:
	if label == null:
		return
	label.text = "%s\nT %.2f | F %.2f | A %.2f | C %.2f" % [display_name, trust, fear, aggression, curiosity]