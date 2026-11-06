extends Node2D
var view: Node
var session: Node
var player: CharacterBody2D
var beach: Node2D
var director: Node
var seek: HSlider
var debug_label: Label
var pause_button: CheckButton
var effect_mode := "All"
func _ready() -> void:
	view=preload("res://scripts/world_view.gd").new(); add_child(view)
	var island=preload("res://scripts/island_world.gd").new(); view.world.add_child(island); island.prepare_region(&"south")
	beach=preload("res://scripts/shipwreck_beach.gd").new(); view.world.add_child(beach)
	player=preload("res://scripts/player.gd").new(); view.world.add_child(player)
	var visual=preload("res://scripts/person.gd").new(); player.add_child(visual)
	var collider:=CollisionShape2D.new(); var shape:=RectangleShape2D.new(); shape.size=Vector2(24,16); collider.shape=shape; player.add_child(collider)
	var layer:=CanvasLayer.new(); layer.layer=20; add_child(layer)
	var fade:=ColorRect.new(); fade.color=Color.BLACK; fade.mouse_filter=Control.MOUSE_FILTER_IGNORE; fade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT); layer.add_child(fade)
	session=preload("res://scenes/cutscenes/opening/opening_session.gd").new(); session.configure(view,player,beach,fade); add_child(session)
	director=session.director
	session.completed.connect(func(): player.set_physics_process(true))
	var controls:=CanvasLayer.new(); controls.layer=30; add_child(controls)
	var panel:=VBoxContainer.new(); panel.position=Vector2(16,100); controls.add_child(panel)
	debug_label=Label.new(); panel.add_child(debug_label)
	var select:=OptionButton.new(); panel.add_child(select)
	for i in range(director.TIMING.boundaries.size()-1): select.add_item("S%02d" % (i+1))
	select.item_selected.connect(func(i): restart(); director.preview_shot(StringName("S%02d" % (i+1))))
	var effects:=OptionButton.new(); panel.add_child(effects)
	for id in ["All","Ocean","Ship","Fog","Coast","Crash","Audio"]: effects.add_item(id)
	effects.item_selected.connect(func(i):
		effect_mode=effects.get_item_text(i)
		restart()
		director.seek(33.1 if effect_mode=="Crash" else (29.5 if effect_mode=="Coast" else 0.0)))
	var restart_button:=Button.new(); restart_button.text="Restart"; panel.add_child(restart_button); restart_button.pressed.connect(restart)
	pause_button=CheckButton.new(); pause_button.text="Pause"; panel.add_child(pause_button); pause_button.toggled.connect(func(v): director.set_paused(v))
	for option in ["2×", "Reduced motion", "Reduced flashes", "Markers", "Captions"]:
		var button:=CheckButton.new(); button.text=option; panel.add_child(button)
		button.toggled.connect(func(v):
			match option:
				"2×": session.forced_rate=v
				"Reduced motion": session.reduced_motion=v
				"Reduced flashes": session.reduced_flashes=v
				"Markers": beach.debug_geometry=v; beach.queue_redraw()
				"Captions": session.captions=v
		)
	seek=HSlider.new(); seek.max_value=director.T.END; seek.step=0.1; seek.custom_minimum_size=Vector2(230,24); panel.add_child(seek)
	seek.value_changed.connect(_seek_preview)
func _seek_preview(t: float) -> void:
	session.active=true; session.recovery_started=false; session.recovery_failed=false
	player.set_control_enabled(false); player.set_physics_process(false); player.get_child(0).set_scripted_mode(true)
	session.audio.reset(); session.stage.crash.reset()
	director.running=true
	director.seek(t)
func restart() -> void:
	session.active=true; session.recovery_started=false; session.recovery_failed=false; session.stage.reset(); session.audio.reset(); player.set_control_enabled(false); player.set_physics_process(false); player.get_child(0).set_scripted_mode(true); director.start()
	if pause_button: pause_button.button_pressed=false
func _process(_delta: float) -> void:
	if director:
		var stage: Node2D=session.stage
		if effect_mode!="All":
			stage.visible=true
			stage.ocean.visible=true
			stage.ship.visible=effect_mode=="Ship" or effect_mode=="Crash"
			stage.coast.visible=effect_mode=="Coast"
			stage.scenery.visible=effect_mode=="Coast"
			stage.weather.visible=effect_mode=="Fog"
			stage.crash.visible=effect_mode=="Crash"
		else:
			stage.ocean.show(); stage.ship.show(); stage.crash.show()
			stage.coast.visible=director.time>=director.T.REVEAL
			stage.scenery.visible=stage.coast.visible
		debug_label.text="PREVIEW • fake save\nS%02d · %.2f / 60" % [director.shot+1,director.time]
func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and event.keycode==KEY_ESCAPE: pause_button.button_pressed=not pause_button.button_pressed
