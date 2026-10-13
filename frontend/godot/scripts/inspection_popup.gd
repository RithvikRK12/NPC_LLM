extends PanelContainer
var title: Label
var message: Label
var close_button: Button

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	offset_left = 24
	offset_right = -24
	offset_top = -250
	offset_bottom = -24
	var content := VBoxContainer.new()
	content.add_theme_constant_override("separation",16)
	add_child(content)
	var header := HBoxContainer.new()
	content.add_child(header)
	title = Label.new()
	title.add_theme_font_size_override("font_size",30)
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(title)
	close_button = Button.new()
	close_button.text = "Close"
	close_button.pressed.connect(close)
	header.add_child(close_button)
	for direction in ["focus_next","focus_previous","focus_neighbor_top","focus_neighbor_bottom","focus_neighbor_left","focus_neighbor_right"]:
		close_button.set(direction,close_button.get_path())
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	content.add_child(scroll)
	message = Label.new()
	message.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	message.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(message)
	hide()

func present(heading: String, text: String) -> void:
	title.text = heading
	message.text = text
	show()
	close_button.grab_focus()

func close() -> void:
	hide()
