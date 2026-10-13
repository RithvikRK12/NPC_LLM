extends GridContainer

signal item_selected(item: String)
var selected_item := ""
var items: Array = []
var cards: Dictionary = {}
const Styles = preload("res://scripts/medieval_theme.gd")
const CARD_SIZE := 72
const GAP := 8

func _ready() -> void:
	columns = 8
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
	var ordered := counts.keys()
	ordered.sort()
	for item in ordered:
		var card := Button.new()
		card.custom_minimum_size = Vector2(CARD_SIZE, CARD_SIZE)
		card.tooltip_text = str(item).capitalize()
		var icon := TextureRect.new()
		var path := "res://assets/items/pixel/%s.svg" % item
		if ResourceLoader.exists(path): icon.texture = load(path)
		icon.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		icon.offset_left = 8
		icon.offset_top = 8
		icon.offset_right = -8
		icon.offset_bottom = -8
		icon.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
		card.add_child(icon)
		var count := Label.new()
		count.text = str(counts[item]) if counts[item] > 1 else ("?" if icon.texture == null else "")
		count.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		count.offset_right = -4
		count.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		count.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
		count.add_theme_font_size_override("font_size", 21)
		count.mouse_filter = Control.MOUSE_FILTER_IGNORE
		card.add_child(count)
		card.pressed.connect(select_item.bind(str(item)))
		card.focus_entered.connect(select_item.bind(str(item)))
		add_child(card)
		cards[item] = card
	for unused in range(maxi(columns * 2 - counts.size(), 0)):
		var empty := PanelContainer.new()
		empty.custom_minimum_size = Vector2(CARD_SIZE, CARD_SIZE)
		empty.add_theme_stylebox_override("panel", Styles.frame(Color("b49464"), Color("70482c"), 3, 0))
		add_child(empty)
	_refresh_selection()

func select_item(item: String) -> void:
	if not items.has(item): return
	selected_item = item
	_refresh_selection()
	item_selected.emit(item)

func _refresh_selection() -> void:
	for item in cards:
		var selected: bool = item == selected_item
		cards[item].add_theme_stylebox_override("normal", Styles.frame(Color("f4d989") if selected else Color("c4a675"), Styles.INK if selected else Color("70482c"), 4 if selected else 3, 0))

		cards[item].add_theme_stylebox_override("hover", Styles.frame(Color("fff0ce"), Styles.INK if selected else Color("70482c"), 4 if selected else 3, 0))

func fit_columns(available: float) -> void:
	var next := clampi(int((available + GAP) / (CARD_SIZE + GAP)), 3, 8)
	if next != columns:
		columns = next
		populate(items)
