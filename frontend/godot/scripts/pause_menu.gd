extends Control

signal resume_requested
signal missions_requested
signal inventory_requested
signal restart_requested
signal quit_requested
signal zoom_changed(value: float)
signal fullscreen_changed(enabled: bool)

var restart_button: Button
var zoom: HSlider

func action(layout: VBoxContainer, caption: String, callback: Callable) -> Button:
	var button := Button.new()
	button.text = caption
	button.custom_minimum_size.y = 40
	button.pressed.connect(callback)
	layout.add_child(button)
	return button

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var shade := ColorRect.new()
	shade.color = Color(0.015, 0.025, 0.035, 0.8)
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(shade)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(center)
	var panel := PanelContainer.new()
	panel.custom_minimum_size.x = 360
	var style := StyleBoxFlat.new()
	style.bg_color = Color("111c22")
	style.border_color = Color("46bfb9")
	style.set_border_width_all(1)
	style.set_corner_radius_all(6)
	style.set_content_margin_all(22)
	panel.add_theme_stylebox_override("panel", style)
	center.add_child(panel)
	var layout := VBoxContainer.new()
	layout.add_theme_constant_override("separation", 10)
	panel.add_child(layout)
	var title := Label.new()
	title.text = "PAUSED"
	title.add_theme_font_size_override("font_size", 24)
	layout.add_child(title)
	action(layout, "Resume", func(): resume_requested.emit())
	action(layout, "Missions", func(): missions_requested.emit())
	action(layout, "Inventory", func(): inventory_requested.emit())
	restart_button = action(layout, "Restart Game", func(): restart_requested.emit())
	layout.add_child(HSeparator.new())
	var zoom_label := Label.new()
	zoom_label.text = "Camera distance"
	layout.add_child(zoom_label)
	zoom = HSlider.new()
	zoom.min_value = 0.55
	zoom.max_value = 1.35
	zoom.step = 0.05
	zoom.value = 1.0
	zoom.custom_minimum_size.y = 28
	zoom.value_changed.connect(func(value): zoom_changed.emit(value))
	layout.add_child(zoom)
	var fullscreen := CheckButton.new()
	fullscreen.text = "Fullscreen"
	fullscreen.button_pressed = DisplayServer.window_get_mode() == DisplayServer.WINDOW_MODE_FULLSCREEN
	fullscreen.toggled.connect(func(enabled): fullscreen_changed.emit(enabled))
	layout.add_child(fullscreen)
	action(layout, "Save and Quit", func(): quit_requested.emit())
	hide()
