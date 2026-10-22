extends CanvasLayer
## All 2D UI: HUD, vignette, fade, title / pause / document / death / end screens.
## Text goes through I18n (Chinese by default). L toggles language.

signal continue_pressed
signal resume_pressed
signal quit_pressed

const I18n := preload("res://scripts/i18n.gd")

const COL_TEXT := Color("e8e2d6")
const COL_DIM := Color("8a939b")
const COL_AMBER := Color("f0c76b")
const COL_RED := Color("d04848")

var font: Font = null
var root: Control = null
var hud: Control = null

var blink_fill: ColorRect = null
var batt_fill: ColorRect = null
var blink_label: Label = null
var light_label: Label = null
var stam_label: Label = null
var stam_fill: ColorRect = null
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
var t_title: Label = null
var t_sub: Label = null
var t_press: Label = null
var t_hint: Label = null
var p_title: Label = null
var p_hint: Label = null
var d_title: Label = null
var d_body: Label = null
var d_hint: Label = null
var dead_title: Label = null
var dead_hint: Label = null
var e_title: Label = null
var e_sub: Label = null
var e_hint: Label = null
var inv_layer: Control = null
var inv_title: Label = null
var inv_hint: Label = null
var inv_slots: Array = []
var inv_boxes: Array = []
var inv_sel := -1

var obj_key := ""

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

	hud = Control.new()
	hud.set_anchors_preset(Control.PRESET_FULL_RECT)
	hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(hud)
	_build_hud()
	_build_title()
	_build_pause()
	_build_doc()
	_build_dead()
	_build_end()
	_build_inv()

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

	refresh()

func _load_font() -> Font:
	for p in ["res://assets/fonts/ArkPixel12.ttf", "res://assets/fonts/Silkscreen-Regular.ttf"]:
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
	l.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.85))
	l.add_theme_constant_override("shadow_offset_x", 1)
	l.add_theme_constant_override("shadow_offset_y", 1)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l

func _gradient(w: int, h: int, a_top: float, a_bottom: float) -> ImageTexture:
	var img := Image.create(w, h, false, Image.FORMAT_RGBA8)
	for y in h:
		var a: float = lerpf(a_top, a_bottom, float(y) / float(maxi(1, h - 1)))
		for x in w:
			img.set_pixel(x, y, Color(0, 0, 0, a))
	return ImageTexture.create_from_image(img)

func _vignette_texture(px: int) -> ImageTexture:
	var img := Image.create(px, px, false, Image.FORMAT_RGBA8)
	var c := px * 0.5
	for y in px:
		for x in px:
			var d := clampf(Vector2(x + 0.5 - c, y + 0.5 - c).length() / c, 0.0, 1.0)
			var a := pow(clampf((d - 0.30) / 0.70, 0.0, 1.0), 1.7)
			img.set_pixel(x, y, Color(1, 1, 1, a))
	return ImageTexture.create_from_image(img)

func _bar(pos: Vector2, w: float, color: Color) -> ColorRect:
	var bg := ColorRect.new()
	bg.position = pos
	bg.size = Vector2(w, 5)
	bg.color = Color(0.04, 0.05, 0.06, 0.88)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hud.add_child(bg)
	var fill := ColorRect.new()
	fill.position = pos + Vector2(1, 1)
	fill.size = Vector2(w - 2, 3)
	fill.color = color
	fill.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hud.add_child(fill)
	return fill

func _build_hud() -> void:
	var top_bar := TextureRect.new()
	top_bar.texture = _gradient(4, 24, 0.55, 0.0)
	top_bar.position = Vector2.ZERO
	top_bar.size = Vector2(480, 24)
	top_bar.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	top_bar.stretch_mode = TextureRect.STRETCH_SCALE
	top_bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hud.add_child(top_bar)

	var bot_bar := TextureRect.new()
	bot_bar.texture = _gradient(4, 74, 0.0, 0.80)
	bot_bar.position = Vector2(0, 196)
	bot_bar.size = Vector2(480, 74)
	bot_bar.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	bot_bar.stretch_mode = TextureRect.STRETCH_SCALE
	bot_bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hud.add_child(bot_bar)

	blink_label = label("", 12, COL_DIM)
	blink_label.position = Vector2(10, 200)
	hud.add_child(blink_label)
	blink_fill = _bar(Vector2(10, 214), 76, Color("7fb2d6"))

	light_label = label("", 12, COL_DIM)
	light_label.position = Vector2(10, 222)
	hud.add_child(light_label)
	batt_fill = _bar(Vector2(10, 236), 76, Color("d9a441"))

	stam_label = label("", 12, COL_DIM)
	stam_label.position = Vector2(10, 244)
	hud.add_child(stam_label)
	stam_fill = _bar(Vector2(10, 258), 76, Color("8fd08a"))

	card_label = label("", 12, COL_DIM)
	card_label.position = Vector2(300, 6)
	card_label.size = Vector2(170, 14)
	card_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	hud.add_child(card_label)

	obj_label = label("", 12, COL_AMBER)
	obj_label.position = Vector2(10, 6)
	hud.add_child(obj_label)

	prompt_label = label("", 12, COL_TEXT)
	prompt_label.position = Vector2(0, 196)
	prompt_label.size = Vector2(480, 14)
	prompt_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hud.add_child(prompt_label)

	toast = label("", 12, COL_AMBER)
	toast.position = Vector2(0, 140)
	toast.size = Vector2(480, 14)
	toast.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	toast.modulate.a = 0.0
	hud.add_child(toast)

func _panel() -> ColorRect:
	var bg := ColorRect.new()
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.color = Color(0.02, 0.025, 0.03, 0.93)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return bg

func _build_title() -> void:
	title_layer = Control.new()
	title_layer.set_anchors_preset(Control.PRESET_FULL_RECT)
	title_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(title_layer)
	title_layer.add_child(_panel())

	t_title = label("", 24, COL_TEXT)
	t_title.position = Vector2(0, 74)
	t_title.size = Vector2(480, 30)
	t_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title_layer.add_child(t_title)

	t_sub = label("", 12, COL_DIM)
	t_sub.position = Vector2(0, 110)
	t_sub.size = Vector2(480, 14)
	t_sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title_layer.add_child(t_sub)

	t_press = label("", 12, COL_AMBER)
	t_press.position = Vector2(0, 164)
	t_press.size = Vector2(480, 14)
	t_press.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title_layer.add_child(t_press)
	t_press.name = "Blink"

	t_hint = label("", 12, Color(0.45, 0.48, 0.52))
	t_hint.position = Vector2(0, 238)
	t_hint.size = Vector2(480, 14)
	t_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title_layer.add_child(t_hint)

func _build_pause() -> void:
	pause_layer = Control.new()
	pause_layer.set_anchors_preset(Control.PRESET_FULL_RECT)
	pause_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(pause_layer)
	pause_layer.add_child(_panel())
	p_title = label("", 24, COL_TEXT)
	p_title.position = Vector2(0, 100)
	p_title.size = Vector2(480, 30)
	p_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	pause_layer.add_child(p_title)
	p_hint = label("", 12, COL_DIM)
	p_hint.position = Vector2(0, 138)
	p_hint.size = Vector2(480, 14)
	p_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	pause_layer.add_child(p_hint)
	pause_layer.visible = false

func _build_doc() -> void:
	doc_layer = Control.new()
	doc_layer.set_anchors_preset(Control.PRESET_FULL_RECT)
	doc_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(doc_layer)

	var dim := ColorRect.new()
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.color = Color(0.01, 0.012, 0.016, 0.82)
	dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	doc_layer.add_child(dim)

	var paper := ColorRect.new()
	paper.position = Vector2(54, 32)
	paper.size = Vector2(372, 204)
	paper.color = Color(0.055, 0.06, 0.07, 0.99)
	paper.mouse_filter = Control.MOUSE_FILTER_IGNORE
	doc_layer.add_child(paper)

	var edge := ColorRect.new()
	edge.position = Vector2(54, 32)
	edge.size = Vector2(372, 2)
	edge.color = Color(0.85, 0.72, 0.35, 0.9)
	edge.mouse_filter = Control.MOUSE_FILTER_IGNORE
	doc_layer.add_child(edge)

	d_title = label("", 12, COL_AMBER)
	d_title.position = Vector2(66, 42)
	d_title.size = Vector2(348, 14)
	doc_layer.add_child(d_title)

	d_body = label("", 12, COL_TEXT)
	d_body.position = Vector2(66, 62)
	d_body.size = Vector2(348, 136)
	d_body.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	doc_layer.add_child(d_body)

	d_hint = label("", 12, COL_DIM)
	d_hint.position = Vector2(66, 210)
	d_hint.size = Vector2(348, 14)
	doc_layer.add_child(d_hint)
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

	dead_title = label("", 24, COL_RED)
	dead_title.position = Vector2(0, 100)
	dead_title.size = Vector2(480, 30)
	dead_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	dead_layer.add_child(dead_title)

	dead_hint = label("", 12, COL_DIM)
	dead_hint.position = Vector2(0, 138)
	dead_hint.size = Vector2(480, 14)
	dead_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	dead_layer.add_child(dead_hint)
	dead_layer.visible = false

func _build_end() -> void:
	end_layer = Control.new()
	end_layer.set_anchors_preset(Control.PRESET_FULL_RECT)
	end_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(end_layer)
	end_layer.add_child(_panel())
	e_title = label("", 24, COL_TEXT)
	e_title.position = Vector2(0, 86)
	e_title.size = Vector2(480, 30)
	e_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	end_layer.add_child(e_title)

	e_sub = label("", 12, COL_DIM)
	e_sub.position = Vector2(0, 120)
	e_sub.size = Vector2(480, 14)
	e_sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	end_layer.add_child(e_sub)

	e_hint = label("", 12, COL_AMBER)
	e_hint.position = Vector2(0, 166)
	e_hint.size = Vector2(480, 14)
	e_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	end_layer.add_child(e_hint)
	end_layer.visible = false

func _build_inv() -> void:
	inv_layer = Control.new()
	inv_layer.set_anchors_preset(Control.PRESET_FULL_RECT)
	inv_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(inv_layer)

	var dim := ColorRect.new()
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.color = Color(0.01, 0.012, 0.016, 0.86)
	dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	inv_layer.add_child(dim)

	var panel := ColorRect.new()
	panel.position = Vector2(70, 56)
	panel.size = Vector2(340, 160)
	panel.color = Color(0.055, 0.06, 0.07, 0.99)
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	inv_layer.add_child(panel)

	var edge := ColorRect.new()
	edge.position = Vector2(70, 56)
	edge.size = Vector2(340, 2)
	edge.color = Color(0.85, 0.72, 0.35, 0.9)
	edge.mouse_filter = Control.MOUSE_FILTER_IGNORE
	inv_layer.add_child(edge)

	inv_title = label('', 12, COL_AMBER)
	inv_title.position = Vector2(82, 66)
	inv_layer.add_child(inv_title)

	for i in 8:
		var col := i % 4
		var row := int(i / 4)
		var bx := 82 + col * 82
		var by := 92 + row * 56
		var box := ColorRect.new()
		box.position = Vector2(bx, by)
		box.size = Vector2(76, 50)
		box.color = Color(0.09, 0.10, 0.12, 0.95)
		box.mouse_filter = Control.MOUSE_FILTER_IGNORE
		inv_layer.add_child(box)
		inv_boxes.append(box)
		var l := label('', 12, COL_TEXT)
		l.position = Vector2(bx + 5, by + 5)
		l.size = Vector2(68, 40)
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		inv_layer.add_child(l)
		inv_slots.append(l)

	inv_hint = label('', 12, COL_DIM)
	inv_hint.position = Vector2(82, 198)
	inv_layer.add_child(inv_hint)
	inv_layer.visible = false

func show_inv(entries: Array, sel: int) -> void:
	inv_sel = sel
	for i in 8:
		var l: Label = inv_slots[i]
		var box: ColorRect = inv_boxes[i]
		if i < entries.size():
			var e: Dictionary = entries[i]
			var suffix := '' if int(e.get('count', 1)) <= 1 else ' x%d' % int(e.count)
			l.text = '%d %s%s' % [i + 1, String(e.name), suffix]
		else:
			l.text = ''
		box.color = Color(0.16, 0.14, 0.07, 0.95) if i == sel else Color(0.09, 0.10, 0.12, 0.95)
	inv_layer.visible = true
	hud.visible = false

func hide_inv() -> void:
	inv_layer.visible = false
	hud.visible = true

# ---------------------------------------------------------------- text

func refresh() -> void:
	blink_label.text = I18n.t("ui_blink")
	light_label.text = I18n.t("ui_light")
	stam_label.text = I18n.t("ui_stamina")
	t_title.text = I18n.t("title_name")
	t_sub.text = I18n.t("title_sub")
	t_press.text = I18n.t("title_press")
	t_hint.text = I18n.t("title_hint")
	p_title.text = I18n.t("pause_title")
	p_hint.text = I18n.t("pause_hint")
	d_hint.text = I18n.t("doc_close")
	dead_title.text = I18n.t("dead_title")
	dead_hint.text = I18n.t("dead_hint")
	e_title.text = I18n.t("end_title")
	e_sub.text = I18n.t("end_sub")
	e_hint.text = I18n.t("end_hint")
	inv_title.text = I18n.t('inv_title')
	inv_hint.text = I18n.t('inv_hint')
	if obj_key != "":
		obj_label.text = I18n.t(obj_key)

func tick(delta: float, blink_ratio: float, battery_ratio: float, stamina_ratio: float, card: int, eyes_open: bool, danger: float) -> void:
	blink_fill.size.x = 74.0 * clampf(blink_ratio, 0.0, 1.0)
	batt_fill.size.x = 74.0 * clampf(battery_ratio, 0.0, 1.0)
	stam_fill.size.x = 74.0 * clampf(stamina_ratio, 0.0, 1.0)
	stam_fill.color = Color("d05a48") if stamina_ratio < 0.22 else Color("8fd08a")

	if blink_ratio < 0.18:
		var w: float = 0.35 + 0.65 * absf(sin(Time.get_ticks_msec() / 90.0))
		blink_label.modulate = Color(1.0, 0.45, 0.4, w)
		blink_fill.color = Color(0.95, 0.35, 0.30)
	else:
		blink_label.modulate = Color(1, 1, 1, 1)
		blink_fill.color = Color("7fb2d6")

	card_label.text = I18n.t("ui_card") % card if card > 0 else I18n.t("ui_card_none")

	var pulse: float = 0.55 + 0.45 * sin(Time.get_ticks_msec() / 210.0)
	vignette.modulate = Color(0.62, 0.05, 0.05, clampf(danger * danger, 0.0, 1.0) * 0.9 * pulse)

	blink_overlay.color.a = 0.0 if eyes_open else 0.97

	if toast_t > 0.0:
		toast_t -= delta
		toast.modulate.a = clampf(toast_t / 0.5, 0.0, 1.0)

func set_objective(key: String) -> void:
	obj_key = key
	obj_label.text = I18n.t(key)

func set_prompt(text: String) -> void:
	prompt_label.text = text

func say(text: String, secs: float = 2.6) -> void:
	toast.text = text
	toast_t = secs
	toast.modulate.a = 1.0

func show_title(on: bool) -> void:
	title_layer.visible = on
	hud.visible = not on
	if on and t_press:
		t_press.modulate.a = 0.55 + 0.45 * absf(sin(Time.get_ticks_msec() / 420.0))

func show_pause(on: bool) -> void:
	pause_layer.visible = on
	hud.visible = not on

func show_doc(title: String, body: String) -> void:
	d_title.text = title
	d_body.text = body
	doc_layer.visible = true
	hud.visible = false

func hide_doc() -> void:
	doc_layer.visible = false
	hud.visible = true

func show_dead(on: bool) -> void:
	dead_layer.visible = on
	hud.visible = not on

func set_dead_alpha(a: float) -> void:
	var bg := dead_layer.get_meta("bg") as ColorRect
	if bg:
		bg.color = Color(0.10, 0.01, 0.01, a)

func show_end(on: bool) -> void:
	end_layer.visible = on
	hud.visible = not on

func fade_to(a: float, secs: float) -> void:
	var tw := create_tween()
	tw.tween_property(fade_rect, "color:a", a, secs)
