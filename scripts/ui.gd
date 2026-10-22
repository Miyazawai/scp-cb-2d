extends CanvasLayer
## All 2D UI: HUD, vignette, fade, title / pause / document / death / end screens.

signal continue_pressed
signal resume_pressed
signal quit_pressed

const COL_TEXT := Color("e8e2d6")
const COL_DIM := Color("8a939b")
const COL_AMBER := Color("f0c76b")
const COL_RED := Color("d04848")
const COL_INK := Color("0b0d10")

var font: Font = null
var root: Control = null

var blink_fill: ColorRect = null
var batt_fill: ColorRect = null
var blink_label: Label = null
var card_label: Label = null
var obj_label: Label = null
var prompt_label: Label = null
var toast: Label = null
var toast_t := 0.0
var vignette: TextureRect = null
var blink_overlay: ColorRect = null
var fade_rect: ColorRect = null

var title_layer: Control = null
var pause_layer: Control = null
var doc_layer: Control = null
var dead_layer: Control = null
var end_layer: Control = null
var doc_title: Label = null
var doc_body: Label = null
var dead_layer_time := 0.0

func _ready() -> void:
	layer = 10
	font = _load_font()
	root = Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root)

	vignette = TextureRect.new()
	vignette.texture = _vignette_texture(128)
	vignette.set_anchors_preset(Control.PRESET_FULL_RECT)
	vignette.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	vignette.stretch_mode = TextureRect.STRETCH_SCALE
	vignette.mouse_filter = Control.MOUSE_FILTER_IGNORE
	vignette.modulate = Color(0.62, 0.05, 0.05, 0.0)
	root.add_child(vignette)

	_build_hud()
	_build_title()
	_build_pause()
	_build_doc()
	_build_dead()
	_build_end()

	blink_overlay = ColorRect.new()
	blink_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	blink_overlay.color = Color(0, 0, 0, 0)
	blink_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(blink_overlay)

	fade_rect = ColorRect.new()
	fade_rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	fade_rect.color = Color(0, 0, 0, 1)
	fade_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(fade_rect)

func _load_font() -> Font:
	for p in ["res://assets/fonts/Silkscreen-Regular.ttf", "res://assets/fonts/Silkscreen-Bold.ttf"]:
		if ResourceLoader.exists(p):
			var f = load(p)
			if f is Font:
				return f
	return null

func label(text: String, size: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	if font:
		l.add_theme_font_override("font", font)
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l

func _bar(pos: Vector2, w: float, color: Color) -> Array:
	var bg := ColorRect.new()
	bg.position = pos
	bg.size = Vector2(w, 5)
	bg.color = Color(0.04, 0.05, 0.06, 0.88)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(bg)
	var fill := ColorRect.new()
	fill.position = pos + Vector2(1, 1)
	fill.size = Vector2(w - 2, 3)
	fill.color = color
	fill.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(fill)
	return [bg, fill]

func _vignette_texture(px: int) -> ImageTexture:
	var img := Image.create(px, px, false, Image.FORMAT_RGBA8)
	var c := px * 0.5
	for y in px:
		for x in px:
			var d := clampf(Vector2(x + 0.5 - c, y + 0.5 - c).length() / c, 0.0, 1.0)
			var a := pow(clampf((d - 0.30) / 0.70, 0.0, 1.0), 1.7)
			img.set_pixel(x, y, Color(1, 1, 1, a))
	return ImageTexture.create_from_image(img)

func _gradient(w: int, h: int, a_top: float, a_bottom: float) -> ImageTexture:
	var img := Image.create(w, h, false, Image.FORMAT_RGBA8)
	for y in h:
		var a: float = lerpf(a_top, a_bottom, float(y) / float(maxi(1, h - 1)))
		for x in w:
			img.set_pixel(x, y, Color(0, 0, 0, a))
	return ImageTexture.create_from_image(img)

func _build_hud() -> void:
	var top_bar := TextureRect.new()
	top_bar.texture = _gradient(4, 24, 0.55, 0.0)
	top_bar.position = Vector2(0, 0)
	top_bar.size = Vector2(480, 24)
	top_bar.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	top_bar.stretch_mode = TextureRect.STRETCH_SCALE
	top_bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(top_bar)

	var bot_bar := TextureRect.new()
	bot_bar.texture = _gradient(4, 52, 0.0, 0.72)
	bot_bar.position = Vector2(0, 218)
	bot_bar.size = Vector2(480, 52)
	bot_bar.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	bot_bar.stretch_mode = TextureRect.STRETCH_SCALE
	bot_bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(bot_bar)

	blink_label = label("BLINK", 8, COL_DIM)
	blink_label.position = Vector2(10, 226)
	root.add_child(blink_label)

	var b := _bar(Vector2(10, 238), 74, Color("7fb2d6"))
	blink_fill = b[1]

	var bl := label("LIGHT", 8, COL_DIM)
	bl.position = Vector2(10, 246)
	root.add_child(bl)
	var l := _bar(Vector2(10, 258), 74, Color("d9a441"))
	batt_fill = l[1]

	card_label = label("KEYCARD —", 8, COL_DIM)
	card_label.position = Vector2(388, 10)
	root.add_child(card_label)

	obj_label = label("", 8, COL_AMBER)
	obj_label.position = Vector2(10, 10)
	root.add_child(obj_label)

	prompt_label = label("", 8, COL_TEXT)
	prompt_label.position = Vector2(120, 240)
	prompt_label.size = Vector2(240, 12)
	prompt_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	root.add_child(prompt_label)

	toast = label("", 8, COL_AMBER)
	toast.position = Vector2(0, 150)
	toast.size = Vector2(480, 12)
	toast.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	toast.modulate.a = 0.0
	root.add_child(toast)

func _panel() -> ColorRect:
	var bg := ColorRect.new()
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.color = Color(0.02, 0.025, 0.03, 0.92)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return bg

func _build_title() -> void:
	title_layer = Control.new()
	title_layer.set_anchors_preset(Control.PRESET_FULL_RECT)
	title_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(title_layer)
	title_layer.add_child(_panel())

	var t := label("SCP:CB 2D", 24, COL_TEXT)
	t.position = Vector2(0, 86)
	t.size = Vector2(480, 28)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title_layer.add_child(t)

	var s := label("VERTICAL SLICE  /  SITE-19  LIGHT CONTAINMENT", 8, COL_DIM)
	s.position = Vector2(0, 118)
	s.size = Vector2(480, 12)
	s.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title_layer.add_child(s)

	var c := label("PRESS ENTER", 8, COL_AMBER)
	c.position = Vector2(0, 176)
	c.size = Vector2(480, 12)
	c.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title_layer.add_child(c)
	c.name = "Blink"

	var hint := label("WASD MOVE   MOUSE AIM   SPACE BLINK   E INTERACT", 8, Color(0.45, 0.48, 0.52))
	hint.position = Vector2(0, 246)
	hint.size = Vector2(480, 12)
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title_layer.add_child(hint)

func _build_pause() -> void:
	pause_layer = Control.new()
	pause_layer.set_anchors_preset(Control.PRESET_FULL_RECT)
	pause_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(pause_layer)
	pause_layer.add_child(_panel())
	var t := label("PAUSED", 16, COL_TEXT)
	t.position = Vector2(0, 110)
	t.size = Vector2(480, 20)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	pause_layer.add_child(t)
	var h := label("ESC  RESUME        Q  QUIT", 8, COL_DIM)
	h.position = Vector2(0, 146)
	h.size = Vector2(480, 12)
	h.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	pause_layer.add_child(h)
	pause_layer.visible = false

func _build_doc() -> void:
	doc_layer = Control.new()
	doc_layer.set_anchors_preset(Control.PRESET_FULL_RECT)
	doc_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(doc_layer)

	var dim := ColorRect.new()
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.color = Color(0.01, 0.012, 0.016, 0.80)
	dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	doc_layer.add_child(dim)

	var paper := ColorRect.new()
	paper.position = Vector2(64, 44)
	paper.size = Vector2(352, 182)
	paper.color = Color(0.055, 0.06, 0.07, 0.98)
	paper.mouse_filter = Control.MOUSE_FILTER_IGNORE
	doc_layer.add_child(paper)

	var edge := ColorRect.new()
	edge.position = Vector2(64, 44)
	edge.size = Vector2(352, 2)
	edge.color = Color(0.85, 0.72, 0.35, 0.9)
	edge.mouse_filter = Control.MOUSE_FILTER_IGNORE
	doc_layer.add_child(edge)

	doc_title = label("", 8, COL_AMBER)
	doc_title.position = Vector2(76, 56)
	doc_title.size = Vector2(328, 12)
	doc_layer.add_child(doc_title)

	doc_body = label("", 8, COL_TEXT)
	doc_body.position = Vector2(76, 76)
	doc_body.size = Vector2(328, 128)
	doc_body.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	doc_layer.add_child(doc_body)

	var hint := label("E / ESC  CLOSE", 8, COL_DIM)
	hint.position = Vector2(76, 208)
	hint.size = Vector2(328, 12)
	doc_layer.add_child(hint)
	doc_layer.visible = false

func _build_dead() -> void:
	dead_layer = Control.new()
	dead_layer.set_anchors_preset(Control.PRESET_FULL_RECT)
	dead_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(dead_layer)
	var bg := ColorRect.new()
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.color = Color(0.10, 0.01, 0.01, 0.0)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	dead_layer.add_child(bg)
	dead_layer.set_meta("bg", bg)

	var t := label("YOU DIED", 24, Color("d04848"))
	t.position = Vector2(0, 112)
	t.size = Vector2(480, 28)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	dead_layer.add_child(t)

	var h := label("RESPAWNING AT LAST CHECKPOINT", 8, COL_DIM)
	h.position = Vector2(0, 148)
	h.size = Vector2(480, 12)
	h.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	dead_layer.add_child(h)
	dead_layer.visible = false

func _build_end() -> void:
	end_layer = Control.new()
	end_layer.set_anchors_preset(Control.PRESET_FULL_RECT)
	end_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(end_layer)
	end_layer.add_child(_panel())
	var t := label("DEMO END", 24, COL_TEXT)
	t.position = Vector2(0, 96)
	t.size = Vector2(480, 28)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	end_layer.add_child(t)
	var s := label("SITE-19  //  LIGHT CONTAINMENT  //  SUBLEVEL 2", 8, COL_DIM)
	s.position = Vector2(0, 128)
	s.size = Vector2(480, 12)
	s.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	end_layer.add_child(s)
	var h := label("ESC  QUIT        R  PLAY AGAIN", 8, COL_AMBER)
	h.position = Vector2(0, 176)
	h.size = Vector2(480, 12)
	h.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	end_layer.add_child(h)
	end_layer.visible = false

# ---------------------------------------------------------------- updates

func tick(delta: float, blink_ratio: float, battery_ratio: float, card: int, eyes_open: bool, danger: float) -> void:
	blink_fill.size.x = 72.0 * clampf(blink_ratio, 0.0, 1.0)
	batt_fill.size.x = 72.0 * clampf(battery_ratio, 0.0, 1.0)

	if blink_ratio < 0.18:
		var w: float = 0.35 + 0.65 * absf(sin(Time.get_ticks_msec() / 90.0))
		blink_label.modulate = Color(1.0, 0.45, 0.4, w)
		blink_fill.color = Color(0.95, 0.35, 0.30)
	else:
		blink_label.modulate = Color(1, 1, 1, 1)
		blink_fill.color = Color("7fb2d6")

	card_label.text = "KEYCARD LV%d" % card if card > 0 else "KEYCARD —"

	var pulse: float = 0.55 + 0.45 * sin(Time.get_ticks_msec() / 210.0)
	vignette.modulate = Color(0.62, 0.05, 0.05, clampf(danger * danger, 0.0, 1.0) * 0.9 * pulse)

	blink_overlay.color.a = 0.0 if eyes_open else 0.97

	if toast_t > 0.0:
		toast_t -= delta
		toast.modulate.a = clampf(toast_t / 0.5, 0.0, 1.0)

func set_objective(text: String) -> void:
	obj_label.text = text

func say(text: String, secs: float = 2.6) -> void:
	toast.text = text
	toast_t = secs
	toast.modulate.a = 1.0

func set_prompt(text: String) -> void:
	prompt_label.text = text

func show_title(on: bool) -> void:
	title_layer.visible = on
	var b := title_layer.get_node_or_null("Blink")
	if b and on:
		b.modulate.a = 0.55 + 0.45 * absf(sin(Time.get_ticks_msec() / 420.0))

func show_pause(on: bool) -> void:
	pause_layer.visible = on

func show_doc(title: String, body: String) -> void:
	doc_title.text = title
	doc_body.text = body
	doc_layer.visible = true

func hide_doc() -> void:
	doc_layer.visible = false

func show_dead(on: bool) -> void:
	dead_layer.visible = on
	if on:
		dead_layer_time = 0.0

func set_dead_alpha(a: float) -> void:
	var bg := dead_layer.get_meta("bg") as ColorRect
	if bg:
		bg.color = Color(0.10, 0.01, 0.01, a)

func show_end(on: bool) -> void:
	end_layer.visible = on

func fade_to(a: float, secs: float) -> void:
	var tw := create_tween()
	tw.tween_property(fade_rect, "color:a", a, secs)
