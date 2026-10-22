extends Node2D
## Demo scene builder + game flow.
## Everything is generated in code: no external art assets.
## Controls: WASD move, mouse aim flashlight, Shift sprint, Space blink, F light, R restart.

const TILE := 16
const MAP_W := 40
const MAP_H := 28

var grid: Array = []

var player: CharacterBody2D = null
var scp: Node2D = null

var walls_body: StaticBody2D = null
var doors: Array = []
var exit_zone := Rect2()
var card_pos := Vector2.ZERO
var card_node: Node2D = null
var card_taken := false

var cam: Camera2D = null
var vignette: TextureRect = null
var shake_amt := 0.0

var blink_fill: ColorRect = null
var blink_label: Label = null
var batt_fill: ColorRect = null
var card_label: Label = null
var center_label: Label = null
var blink_overlay: ColorRect = null

var state := "play"
var shot_mode := false
var say_timer := 0.0

# ---------------------------------------------------------------- setup

func _ready() -> void:
	_make_grid()
	_build_floor()
	_build_walls()
	_build_lights()
	_spawn_player()
	_spawn_scp()
	_spawn_card()
	_build_hud()
	_apply_args()

func _make_grid() -> void:
	grid.clear()
	for y in MAP_H:
		var row: Array = []
		for x in MAP_W:
			row.append("#")
		grid.append(row)
	_carve(2, 2, 9, 7)      # A: start room
	_carve(10, 4, 17, 5)    # corridor 1
	_carve(12, 6, 13, 6)    # connector down
	_carve(11, 7, 15, 10)   # side room (keycard)
	_carve(18, 2, 27, 9)    # B: 173 past the door
	_carve(22, 10, 23, 17)  # corridor 2
	_carve(16, 18, 29, 23)  # C: exit room
	grid[4][17] = "D"
	grid[5][17] = "D"

func _carve(x0: int, y0: int, x1: int, y1: int) -> void:
	for y in range(y0, y1 + 1):
		for x in range(x0, x1 + 1):
			if x >= 0 and x < MAP_W and y >= 0 and y < MAP_H:
				grid[y][x] = "."

# ---------------------------------------------------------------- textures

func _floor_texture() -> ImageTexture:
	var img := Image.create(TILE, TILE, false, Image.FORMAT_RGBA8)
	var rng := RandomNumberGenerator.new()
	rng.seed = 20261022
	for y in TILE:
		for x in TILE:
			var base := Color("1e2229")
			var n := rng.randf_range(-0.022, 0.022)
			var c := Color(base.r + n, base.g + n, base.b + n * 1.05, 1.0)
			if x == 0 or y == 0:
				c = c.darkened(0.40)
			if x == TILE - 1 or y == TILE - 1:
				c = c.darkened(0.18)
			img.set_pixel(x, y, c)
	return ImageTexture.create_from_image(img)

func _wall_texture() -> ImageTexture:
	var img := Image.create(TILE, TILE, false, Image.FORMAT_RGBA8)
	var rng := RandomNumberGenerator.new()
	rng.seed = 771
	for y in TILE:
		for x in TILE:
			var base := Color("434d5c")
			var n := rng.randf_range(-0.02, 0.02)
			var c := Color(base.r + n, base.g + n, base.b + n, 1.0)
			if y < 2:
				c = c.lightened(0.22)          # top highlight
			elif y == 6 or y == 7:
				c = c.darkened(0.28)           # seam
			if x == 0:
				c = c.darkened(0.20)
			if y == TILE - 1:
				c = c.darkened(0.45)
			img.set_pixel(x, y, c)
	return ImageTexture.create_from_image(img)

func _radial_texture(px: int, power: float) -> ImageTexture:
	var img := Image.create(px, px, false, Image.FORMAT_RGBA8)
	var c := px * 0.5
	for y in px:
		for x in px:
			var d := Vector2(x + 0.5 - c, y + 0.5 - c).length() / c
			var a := 0.0
			if d <= 1.0:
				a = pow(clampf(1.0 - d, 0.0, 1.0), power)
			img.set_pixel(x, y, Color(1, 1, 1, a))
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

func _on_scp_stepped(dist: float) -> void:
	if dist < 150.0:
		shake_amt = maxf(shake_amt, clampf(1.0 - dist / 150.0, 0.0, 1.0) * 3.2)

func _quad(rect: Rect2, tex: Texture2D, tint: Color, z: int, uv_per_tile: bool = true) -> Polygon2D:
	var p := Polygon2D.new()
	p.polygon = PackedVector2Array([
		rect.position,
		Vector2(rect.end.x, rect.position.y),
		rect.end,
		Vector2(rect.position.x, rect.end.y),
	])
	if uv_per_tile:
		var w := rect.size.x / TILE
		var h := rect.size.y / TILE
		p.uv = PackedVector2Array([Vector2(0, 0), Vector2(w, 0), Vector2(w, h), Vector2(0, h)])
	else:
		p.uv = PackedVector2Array([Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)])
	p.texture = tex
	p.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
	p.color = tint
	p.z_index = z
	return p

func _build_floor() -> void:
	var tex := _floor_texture()
	var root := Node2D.new()
	root.name = "Floor"
	add_child(root)
	for y in MAP_H:
		var x := 0
		while x < MAP_W:
			if grid[y][x] != "#":
				var x0 := x
				while x < MAP_W and grid[y][x] != "#":
					x += 1
				var rect := Rect2(x0 * TILE, y * TILE, (x - x0) * TILE, TILE)
				root.add_child(_quad(rect, tex, Color.WHITE, -2))
			else:
				x += 1

	var exit_pad := _quad(Rect2(28 * TILE, 18 * TILE, 2 * TILE, 6 * TILE), tex, Color("2e6b3c"), -1, false)
	root.add_child(exit_pad)
	exit_zone = Rect2(28 * TILE, 18 * TILE, 2 * TILE, 6 * TILE)

func _build_walls() -> void:
	var tex := _wall_texture()
	walls_body = StaticBody2D.new()
	walls_body.name = "Walls"
	walls_body.collision_layer = 1
	walls_body.collision_mask = 0
	add_child(walls_body)

	var occ_root := Node2D.new()
	occ_root.name = "Occluders"
	add_child(occ_root)

	for y in MAP_H:
		var x := 0
		while x < MAP_W:
			if grid[y][x] == "#":
				var x0 := x
				while x < MAP_W and grid[y][x] == "#":
					x += 1
				var rect := Rect2(x0 * TILE, y * TILE, (x - x0) * TILE, TILE)
				var vis := _quad(rect, tex, Color.WHITE, 0)
				add_child(vis)

				var above_floor: bool = y > 0 and grid[y - 1][x0] != "#"
				var below_floor: bool = y < MAP_H - 1 and grid[y + 1][x0] != "#"
				if above_floor or below_floor:
					var ly := rect.position.y if above_floor else rect.end.y - 2.0
					var lip := Polygon2D.new()
					lip.polygon = PackedVector2Array([
						Vector2(rect.position.x, ly),
						Vector2(rect.end.x, ly),
						Vector2(rect.end.x, ly + 2),
						Vector2(rect.position.x, ly + 2),
					])
					lip.color = Color(0.55, 0.60, 0.70, 0.42)
					lip.z_index = 1
					add_child(lip)

				var cs := CollisionShape2D.new()
				var shape := RectangleShape2D.new()
				shape.size = rect.size
				cs.shape = shape
				cs.position = rect.position + rect.size * 0.5
				walls_body.add_child(cs)

				var occ := LightOccluder2D.new()
				var op := OccluderPolygon2D.new()
				op.polygon = PackedVector2Array([
					rect.position,
					Vector2(rect.end.x, rect.position.y),
					rect.end,
					Vector2(rect.position.x, rect.end.y),
				])
				op.closed = true
				occ.occluder = op
				occ_root.add_child(occ)
			else:
				x += 1

	# locked doors
	for cell in [Vector2i(17, 4), Vector2i(17, 5)]:
		var rect := Rect2(cell.x * TILE, cell.y * TILE, TILE, TILE)
		var node := Node2D.new()
		node.position = rect.position
		add_child(node)
		var body := StaticBody2D.new()
		body.collision_layer = 1
		body.collision_mask = 0
		var cs := CollisionShape2D.new()
		var shape := RectangleShape2D.new()
		shape.size = rect.size
		cs.shape = shape
		cs.position = rect.size * 0.5
		body.add_child(cs)
		node.add_child(body)
		var vis := Polygon2D.new()
		vis.polygon = PackedVector2Array([
			Vector2.ZERO, Vector2(rect.size.x, 0), rect.size, Vector2(0, rect.size.y)
		])
		vis.color = Color("8a5a22")
		vis.z_index = 1
		node.add_child(vis)
		var stripe := Polygon2D.new()
		stripe.polygon = PackedVector2Array([
			Vector2(1, rect.size.y * 0.42), Vector2(rect.size.x - 1, rect.size.y * 0.42),
			Vector2(rect.size.x - 1, rect.size.y * 0.58), Vector2(1, rect.size.y * 0.58)
		])
		stripe.color = Color("d9a441")
		stripe.z_index = 2
		node.add_child(stripe)
		doors.append({"cell": cell, "body": body, "vis": vis, "stripe": stripe, "open": false})

var light_spots: Array = []

func _build_lights() -> void:
	var cm := CanvasModulate.new()
	cm.color = Color(0.24, 0.255, 0.315)
	add_child(cm)

	var tex := _radial_texture(128, 1.5)
	var spots := [
		Vector2(5.5 * TILE, 4.5 * TILE), Vector2(13.5 * TILE, 4.5 * TILE),
		Vector2(13.0 * TILE, 8.5 * TILE),
		Vector2(21.5 * TILE, 4.0 * TILE), Vector2(25.0 * TILE, 8.0 * TILE),
		Vector2(22.5 * TILE, 12.0 * TILE), Vector2(22.5 * TILE, 16.0 * TILE),
		Vector2(20.0 * TILE, 20.0 * TILE), Vector2(26.5 * TILE, 21.5 * TILE),
	]
	for p in spots:
		light_spots.append({"pos": p, "radius": 84.0})
		var l := PointLight2D.new()
		l.texture = tex
		l.texture_scale = 1.75
		l.energy = 1.45
		l.color = Color(1.0, 0.90, 0.78)
		l.shadow_enabled = true
		l.shadow_filter = Light2D.SHADOW_FILTER_PCF5
		l.position = p
		add_child(l)

		var housing := Polygon2D.new()
		housing.polygon = PackedVector2Array([
			Vector2(-8, -3), Vector2(8, -3), Vector2(8, 3), Vector2(-8, 3)
		])
		housing.color = Color("20242b")
		housing.position = p
		housing.z_index = 3
		add_child(housing)

		var tube := Polygon2D.new()
		tube.polygon = PackedVector2Array([
			Vector2(-5, -1), Vector2(5, -1), Vector2(5, 1), Vector2(-5, 1)
		])
		tube.color = Color(1.0, 0.92, 0.74)
		tube.position = p
		tube.z_index = 4
		add_child(tube)

# ---------------------------------------------------------------- actors

func _spawn_player() -> void:
	player = CharacterBody2D.new()
	player.name = "Player"
	player.set_script(preload("res://scripts/player.gd"))
	player.collision_layer = 2
	player.collision_mask = 1
	var cs := CollisionShape2D.new()
	var shape := CircleShape2D.new()
	shape.radius = 5.0
	cs.shape = shape
	player.add_child(cs)
	player.position = Vector2(5 * TILE + 8, 5 * TILE + 8)
	player.lights = light_spots
	add_child(player)
	player.died.connect(_on_player_died)

	cam = Camera2D.new()
	cam.position_smoothing_enabled = true
	cam.position_smoothing_speed = 8.0
	cam.limit_left = 0
	cam.limit_top = 0
	cam.limit_right = MAP_W * TILE
	cam.limit_bottom = MAP_H * TILE
	player.add_child(cam)
	cam.make_current()

func _spawn_scp() -> void:
	scp = Node2D.new()
	scp.name = "SCP-173"
	scp.set_script(preload("res://scripts/scp173.gd"))
	scp.position = Vector2(19 * TILE + 8, 4 * TILE + 8)
	add_child(scp)
	scp.setup(player)
	scp.connect("stepped", _on_scp_stepped)

func _spawn_card() -> void:
	card_pos = Vector2(13 * TILE + 8, 9 * TILE + 8)
	card_node = Node2D.new()
	card_node.name = "Keycard"
	card_node.set_script(preload("res://scripts/keycard.gd"))
	card_node.position = card_pos
	add_child(card_node)

# ---------------------------------------------------------------- hud

func _label(text: String, size: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	return l

func _bar_root(pos: Vector2, w: float) -> ColorRect:
	var bg := ColorRect.new()
	bg.position = pos
	bg.size = Vector2(w, 4)
	bg.color = Color(0.06, 0.07, 0.08, 0.85)
	return bg

func _build_hud() -> void:
	var layer := CanvasLayer.new()
	layer.name = "HUD"
	add_child(layer)

	var root := Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(root)

	vignette = TextureRect.new()
	vignette.texture = _vignette_texture(128)
	vignette.set_anchors_preset(Control.PRESET_FULL_RECT)
	vignette.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	vignette.stretch_mode = TextureRect.STRETCH_SCALE
	vignette.mouse_filter = Control.MOUSE_FILTER_IGNORE
	vignette.modulate = Color(0.62, 0.05, 0.05, 0.0)
	root.add_child(vignette)

	blink_label = _label("BLINK", 7, Color("8fa6b8"))
	blink_label.position = Vector2(8, 230)
	root.add_child(blink_label)
	var blink_bg := _bar_root(Vector2(8, 239), 70)
	root.add_child(blink_bg)
	blink_fill = ColorRect.new()
	blink_fill.position = Vector2(9, 240)
	blink_fill.size = Vector2(68, 2)
	blink_fill.color = Color("7fb2d6")
	root.add_child(blink_fill)

	var tl := _label("LIGHT", 7, Color("8fa6b8"))
	tl.position = Vector2(8, 246)
	root.add_child(tl)
	var batt_bg := _bar_root(Vector2(8, 255), 70)
	root.add_child(batt_bg)
	batt_fill = ColorRect.new()
	batt_fill.position = Vector2(9, 256)
	batt_fill.size = Vector2(68, 2)
	batt_fill.color = Color("d9a441")
	root.add_child(batt_fill)

	card_label = _label("KEYCARD: NONE", 7, Color("8fa6b8"))
	card_label.position = Vector2(370, 8)
	root.add_child(card_label)

	center_label = _label("", 12, Color("e8e2d6"))
	center_label.position = Vector2(0, 96)
	center_label.size = Vector2(480, 20)
	center_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	root.add_child(center_label)

	blink_overlay = ColorRect.new()
	blink_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	blink_overlay.color = Color(0, 0, 0, 0)
	blink_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(blink_overlay)

# ---------------------------------------------------------------- args / flow

func _args() -> PackedStringArray:
	var a := PackedStringArray()
	a.append_array(OS.get_cmdline_args())
	a.append_array(OS.get_cmdline_user_args())
	return a

func _apply_args() -> void:
	var a := _args()
	if a.has("--shot") or a.has("--shot2") or a.has("--shot3"):
		shot_mode = true
		player.use_mouse_aim = false
		player.facing = Vector2.RIGHT
		var fname := "demo_shot.png"
		if a.has("--shot"):
			player.position = Vector2(19.5 * TILE, 5.5 * TILE)
			scp.position = Vector2(24.0 * TILE, 5.5 * TILE)
			card_taken = true
			player.card_level = 1
		elif a.has("--shot3"):
			fname = "demo_shot3.png"
			player.position = Vector2(12.5 * TILE, 4.5 * TILE)
			scp.position = Vector2(9.5 * TILE, 4.5 * TILE)   # behind the player, close
			scp.hold = true
		else:
			fname = "demo_shot2.png"
			player.position = Vector2(5.5 * TILE, 5.5 * TILE)
			scp.position = Vector2(13.0 * TILE, 4.5 * TILE)
		_shot_and_quit(fname)
	else:
		_say("WASD MOVE   MOUSE AIM   SPACE BLINK", 4.0)

func _shot_and_quit(fname: String) -> void:
	await get_tree().create_timer(1.2).timeout
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var path := ProjectSettings.globalize_path("res://" + fname)
	img.save_png(path)
	print("SHOT SAVED: ", path)
	get_tree().quit()

func _say(text: String, secs: float) -> void:
	center_label.text = text
	say_timer = secs

func _process(delta: float) -> void:
	if player == null:
		return
	blink_fill.size.x = 68.0 * player.blink_ratio()
	batt_fill.size.x = 68.0 * player.battery_ratio()

	# forced-blink warning: you must know it is coming, or the death is unfair
	var br: float = player.blink_ratio()
	if br < 0.18:
		var warn: float = 0.35 + 0.65 * absf(sin(float(Time.get_ticks_msec()) / 90.0))
		blink_label.modulate = Color(1.0, 0.45, 0.4, warn)
		blink_fill.color = Color(0.95, 0.35, 0.30)
	else:
		blink_label.modulate = Color(1, 1, 1, 1)
		blink_fill.color = Color("7fb2d6")
	card_label.text = "KEYCARD: %s" % ("LV1" if player.card_level >= 1 else "NONE")
	blink_overlay.color.a = 0.0 if player.eyes_open else 0.97

	# pressure: the panel bleeds red while it is close and you cannot see it
	if scp:
		var d: float = player.position.distance_to(scp.position)
		var seen: bool = player.can_see(scp.position)
		var danger := 0.0
		if not seen:
			danger = clampf(1.0 - d / 190.0, 0.0, 1.0)
		var pulse: float = 0.55 + 0.45 * sin(float(Time.get_ticks_msec()) / 210.0)
		vignette.modulate = Color(0.62, 0.05, 0.05, danger * danger * 0.9 * pulse)

	shake_amt = maxf(0.0, shake_amt - delta * 9.0)
	if cam:
		cam.offset = Vector2(randf_range(-1.0, 1.0), randf_range(-1.0, 1.0)) * shake_amt

	if say_timer > 0.0:
		say_timer -= delta
		if say_timer <= 0.0:
			center_label.text = ""

	if state == "play":
		_pickup_check()
		_door_check()
		_exit_check()

func _pickup_check() -> void:
	if card_taken:
		return
	if player.position.distance_to(card_pos) < 11.0:
		card_taken = true
		player.card_level = 1
		card_node.queue_free()
		_say("LEVEL 1 KEYCARD ACQUIRED", 2.0)

func _door_check() -> void:
	for d in doors:
		if d.open:
			continue
		var center := Vector2(d.cell.x * TILE + 8, d.cell.y * TILE + 8)
		if player.position.distance_to(center) < 20.0:
			if player.card_level >= 1:
				d.open = true
				d.body.queue_free()
				d.vis.color = Color("2f6b3a")
				d.stripe.color = Color("7bd08a")
				_say("DOOR UNLOCKED", 1.5)
			else:
				_say("LEVEL 1 KEYCARD REQUIRED", 1.0)

func _exit_check() -> void:
	if exit_zone.has_point(player.position):
		state = "won"
		player.freeze = true
		_say("ESCAPED  —  PRESS R", 999.0)

func _on_player_died() -> void:
	state = "dead"
	_say("YOU DIED  —  PRESS R", 999.0)

func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.physical_keycode == KEY_R:
			get_tree().reload_current_scene()
		elif event.physical_keycode == KEY_ESCAPE:
			get_tree().quit()
