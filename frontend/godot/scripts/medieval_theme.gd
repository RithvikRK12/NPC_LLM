extends RefCounted

const INK := Color("302419")
const PARCHMENT := Color("ead7ab")

static func frame(fill: Color = PARCHMENT, border: Color = Color("70482c"), width: int = 4, padding: int = 18) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = fill
	style.border_color = border
	style.set_border_width_all(width)
	style.set_content_margin_all(padding)
	style.shadow_color = Color("20170f80")
	style.shadow_size = 4
	return style

static func set_button_styles(theme: Theme, padding: int) -> void:
	theme.set_stylebox("normal", "Button", frame(Color("c4a675"), Color("70482c"), 3, padding))
	theme.set_stylebox("hover", "Button", frame(Color("f5e4bd"), Color("70482c"), 3, padding))
	theme.set_stylebox("pressed", "Button", frame(Color("d6ad55"), INK, 3, padding))
	theme.set_stylebox("disabled", "Button", frame(Color("c2b18d"), Color("897356"), 2, padding))

static func compact_overlay() -> Theme:
	# Inherit the player's chosen font sizes; reduce only surrounding spacing.
	var theme := Theme.new()
	theme.set_stylebox("panel", "PanelContainer", frame(PARCHMENT,Color("70482c"),4,10))
	set_button_styles(theme,6)
	return theme

static func create(large := false) -> Theme:
	var theme := Theme.new()
	var font := load("res://assets/fonts/PixelifySans.ttf") as FontFile
	var fallback := SystemFont.new()
	fallback.font_names = PackedStringArray(["Arial Unicode MS", "Noto Sans", "Arial", "sans-serif"])
	font.fallbacks = [fallback]
	theme.default_font = font
	theme.default_font_size = 28 if large else 23
	theme.set_font_size("normal_font_size", "RichTextLabel", 30 if large else 25)
	theme.set_font_size("font_size", "LineEdit", 30 if large else 25)
	theme.set_color("font_placeholder_color", "LineEdit", Color("756650"))
	for type in ["Label", "Button", "LineEdit", "RichTextLabel", "CheckButton"]:
		for color in ["font_color", "default_color", "font_hover_color", "font_pressed_color", "font_focus_color"]:
			theme.set_color(color, type, INK)
		theme.set_color("font_disabled_color", type, Color("756650"))
	theme.set_stylebox("panel", "PanelContainer", frame())
	theme.set_stylebox("panel", "PopupPanel", frame())
	theme.set_stylebox("panel", "Window", frame())
	var window_border := ThemeDB.get_default_theme().get_stylebox("embedded_border", "Window").duplicate() as StyleBoxFlat
	window_border.bg_color = Color("70482c")
	window_border.border_color = Color("70482c")
	theme.set_stylebox("embedded_border", "Window", window_border)
	theme.set_color("title_color", "Window", PARCHMENT)
	set_button_styles(theme,10)
	var focus := frame(Color.TRANSPARENT, INK, 2, 0)
	focus.draw_center = false
	theme.set_stylebox("focus", "Button", focus)
	theme.set_stylebox("normal", "LineEdit", frame(Color("fff0ce"), Color("70482c"), 2, 10))
	theme.set_stylebox("focus", "LineEdit", focus)
	theme.set_color("caret_color", "LineEdit", INK)
	theme.set_stylebox("normal", "TextEdit", frame())
	theme.set_stylebox("panel", "TooltipPanel", frame())
	theme.set_color("font_color", "TooltipLabel", INK)
	theme.set_stylebox("background", "ProgressBar", frame(Color("c4a675"), INK, 2, 0))
	theme.set_stylebox("fill", "ProgressBar", frame(Color("68764c"), Color("68764c"), 0, 0))
	return theme
