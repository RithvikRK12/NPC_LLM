extends GridContainer

signal item_selected(item: String)
var selected_item := ""
var items: Array = []
var cards: Dictionary = {}

func _ready() -> void:
	columns = 5
	add_theme_constant_override("h_separation", 8)
	add_theme_constant_override("v_separation", 8)

func populate(values: Array) -> void:
	items = values.duplicate()
	for child in get_children():
		remove_child(child)
		child.queue_free()
	cards.clear()
	if not items.has(selected_item): selected_item = ""
	var counts := {}
	for item in items: counts[item] = int(counts.get(item, 0)) + 1
	for item in counts:
		var card := Button.new()
		card.custom_minimum_size = Vector2(96, 100)
		card.tooltip_text = "Select " + str(item)
		var content := VBoxContainer.new()
		content.mouse_filter = Control.MOUSE_FILTER_IGNORE
		content.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		content.offset_top = 5
		content.offset_bottom = -5
		card.add_child(content)
		var icon := TextureRect.new()
		var path := "res://assets/items/%s.svg" % item
		if ResourceLoader.exists(path): icon.texture = load(path)
		icon.custom_minimum_size = Vector2(56, 56)
		icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
		content.add_child(icon)
		var caption := Label.new()
		caption.text = str(item).capitalize() + (" ×%s" % counts[item] if counts[item] > 1 else "")
		caption.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		caption.mouse_filter = Control.MOUSE_FILTER_IGNORE
		caption.add_theme_font_size_override("font_size", 15)
		content.add_child(caption)
		card.pressed.connect(select_item.bind(str(item)))
		add_child(card)
		cards[item] = card
	_refresh_selection()

func select_item(item: String) -> void:
	selected_item = item
	_refresh_selection()
	item_selected.emit(item)

func _refresh_selection() -> void:
	for item in cards:
		var style := StyleBoxFlat.new()
		style.bg_color = Color("3c5045") if item == selected_item else Color("293c34")
		style.border_color = Color("e8c786") if item == selected_item else Color("526454")
		style.set_border_width_all(2 if item == selected_item else 1)
		style.set_corner_radius_all(8)
		cards[item].add_theme_stylebox_override("normal", style)
		var hover := style.duplicate()
		hover.bg_color = Color("4a6050")
		cards[item].add_theme_stylebox_override("hover", hover)
