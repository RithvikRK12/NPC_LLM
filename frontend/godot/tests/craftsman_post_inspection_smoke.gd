extends "res://tests/craftsman_integration_smoke.gd"

func _initialize() -> void:
	acceptance_message = "Sure! That would be helpful."
	check_post_inspection = true
	super._initialize()
