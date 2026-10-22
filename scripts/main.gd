extends Node2D
## Vertical slice: one wing of Light Containment. Cell -> corridor (173) ->
## checkpoint (save / document) -> power room -> exit.

const Assets := preload("res://scripts/assets.gd")
const I18n := preload("res://scripts/i18n.gd")

const TILE := 16
const MAP_W := 40
const MAP_H := 32

enum St { TITLE, PLAY, PAUSE, DOC, DEAD, END }

var grid: Array = []
var st: int = St.TITLE

var player: CharacterBody2D = null
var scp: Node2D = null
var cam: Camera2D = null
var ui: CanvasLayer = null
var audio: Node = null

var doors: Array = []
var items: Array = []
var lights_ref: Array = []
var flicker: Array = []
var triggers: Array = []
var cm_node: CanvasModulate = null
var burst := 0.0

var card_level := 0
var spawn_pos := Vector2.ZERO
var save_pos := Vector2.ZERO
var scp_spawn := Vector2.ZERO
var exit_zone := Rect2()
var prompt: Dictionary = {}
var dead_t := 0.0
var met_173 := false
var shot_mode := false

# ---------------------------------------------------------------- boot

func _ready() -> void:
	audio = load("res://scripts/audio.gd").new()
	audio.name = "Audio"
	add_child(audio)

	_build_grid()
	exit_zone = Rect2(9 * TILE, 25 * TILE, 3 * TILE, 3 * TILE)
	_build_floor()
	_build_walls()
	_build_ao()
	_build_lights()
	_build_props()
	_build_items()
	_build_doors()
	_build_triggers()
	_spawn_player()
	_spawn_scp()
	_build_ui()
	_build_post()

	st = St.TITLE
	player.freeze = true
	ui.show_title(true)
	ui.fade_to(0.0, 1.4)
	audio.start_ambience()

	_apply_args()

func _selftest() -> void:
	var start := Vector2i(5, 5)
	var seen := {}
	var q: Array = [start]
	seen[start] = true
	while q.size() > 0:
		var c: Vector2i = q.pop_back()
		for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
			var n: Vector2i = c + d
			if seen.has(n):
				continue
			var passable := _is_floor(n.x, n.y)
			if not passable:
				for dr in doors:
					if dr.cells.has(n):
						passable = true
			if passable:
				seen[n] = true
				q.append(n)

	print("SELFTEST tiles reachable: ", seen.size())
	var ex_ok := 0
	for y in range(25, 28):
		for x in range(9, 12):
			if seen.has(Vector2i(x, y)):
				ex_ok += 1
	print("SELFTEST exit tiles reachable: ", ex_ok, "/9")
	for it in items:
		var cell := Vector2i(int(it.pos.x / TILE), int(it.pos.y / TILE))
		print("SELFTEST item ", it.kind, " at ", cell, " floor=", _is_floor(cell.x, cell.y), " reachable=", seen.has(cell))
	for dr in doors:
		var ok := true
		for c in dr.cells:
			if not seen.has(c):
				ok = false
		print("SELFTEST door lv", dr.level, " at ", dr.cells, " reachable=", ok)
	var scell := Vector2i(int(scp_spawn.x / TILE), int(scp_spawn.y / TILE))
	print("SELFTEST 173 at ", scell, " floor=", _is_floor(scell.x, scell.y))
	get_tree().quit()

func _apply_args() -> void:
	var a := PackedStringArray()
	a.append_array(OS.get_cmdline_args())
	a.append_array(OS.get_cmdline_user_args())
	if a.has("--selftest"):
		_selftest()
		return
	if a.has("--audit"):
		print("AUDIT art=", Assets.has_art("tiles/floor_concrete_a.png"),
			" char=", Assets.has_art("chars/player_down_0.png"),
			" snd=", Assets.snd("amb_loop.wav") != null)
		get_tree().quit()
		return
	if a.has("--shot4"):
		shot_mode = true
		st = St.TITLE
		ui.show_title(true)
		ui.fade_to(0.0, 0.01)
		_shot("demo_shot4.png")
		return
	if a.has("--shot5"):
		shot_mode = true
		st = St.DOC
		player.freeze = true
		ui.show_title(false)
		ui.fade_to(0.0, 0.01)
		ui.show_doc(I18n.t("doc_title"), I18n.t("doc_body"))
		_shot("demo_shot5.png")
		return
	if a.has("--shot") or a.has("--shot2") or a.has("--shot3"):
		shot_mode = true
		st = St.PLAY
		ui.show_title(false)
		player.freeze = false
		ui.fade_to(0.0, 0.01)
		player.use_mouse_aim = false
		player.facing = Vector2.RIGHT
		var fname := "demo_shot.png"
		if a.has("--shot"):
			player.position = Vector2(19.5 * TILE, 5.5 * TILE)
			scp.position = Vector2(24.0 * TILE, 5.5 * TILE)
			scp.hold = true
			card_level = 1
		elif a.has("--shot3"):
			fname = "demo_shot3.png"
			player.position = Vector2(22.5 * TILE, 6.5 * TILE)
			scp.position = Vector2(19.0 * TILE, 5.0 * TILE)
			scp.hold = true
			ui.set_objective("obj_corridor")
		else:
			fname = "demo_shot2.png"
			player.position = Vector2(5.5 * TILE, 5.5 * TILE)
			scp.position = Vector2(27.0 * TILE, 4.5 * TILE)
			scp.hold = true
			ui.set_objective("obj_cell")
		_shot(fname)
	else:
		ui.set_objective("")

func _shot(fname: String) -> void:
	await get_tree().create_timer(1.4).timeout
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	img.save_png(ProjectSettings.globalize_path("res://" + fname))
	print("SHOT SAVED: ", fname)
	get_tree().quit()

# ---------------------------------------------------------------- map

func _build_grid() -> void:
	for y in MAP_H:
		var row: Array = []
		for x in MAP_W:
			row.append("#")
		grid.append(row)
	_carve(2, 2, 9, 8)       # cell
	_carve(10, 5, 11, 6)     # cell -> corridor
	_carve(12, 3, 30, 8)     # corridor
	_carve(24, 9, 25, 12)    # corridor -> checkpoint
	_carve(16, 13, 30, 20)   # checkpoint
	_carve(10, 16, 15, 17)   # checkpoint -> power
	_carve(3, 13, 9, 20)     # power room
	_carve(6, 21, 7, 23)     # power -> exit
	_carve(3, 24, 12, 28)    # exit hall

func _carve(x0: int, y0: int, x1: int, y1: int) -> void:
	for y in range(y0, y1 + 1):
		for x in range(x0, x1 + 1):
			if x >= 0 and x < MAP_W and y >= 0 and y < MAP_H:
				grid[y][x] = "."

func _is_floor(x: int, y: int) -> bool:
	if x < 0 or y < 0 or x >= MAP_W or y >= MAP_H:
		return false
	return grid[y][x] == "."

# ---------------------------------------------------------------- build

func _sprite(tex_rel: String, pos: Vector2, z: int) -> Sprite2D:
	var t := Assets.tex(tex_rel)
	if t == null:
		return null
	var s := Sprite2D.new()
	s.texture = t
	s.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	s.position = pos
	s.z_index = z
	add_child(s)
	return s

func _quad(rect: Rect2, color: Color, z: int) -> Polygon2D:
	var p := Polygon2D.new()
	p.polygon = PackedVector2Array([
		rect.position, Vector2(rect.end.x, rect.position.y), rect.end,
		Vector2(rect.position.x, rect.end.y)])
	p.color = color
	p.z_index = z
	add_child(p)
	return p

func _build_floor() -> void:
	var variants := ["tiles/floor_concrete_a.png", "tiles/floor_concrete_b.png", "tiles/floor_concrete_c.png"]
	var use_art := Assets.has_art(variants[0])
	for y in MAP_H:
		for x in MAP_W:
			if not _is_floor(x, y):
				continue
			var c := Vector2(x * TILE + 8, y * TILE + 8)
			if use_art:
				_sprite(variants[(x * 7 + y * 13) % 3], c, -2)
			else:
				var shade := 0.0 if (x + y) % 2 == 0 else 0.012
				_quad(Rect2(x * TILE, y * TILE, TILE, TILE), Color(0.105 + shade, 0.118 + shade, 0.14 + shade), -2)

func _build_walls() -> void:
	var body := StaticBody2D.new()
	body.name = "Walls"
	body.collision_layer = 1
	body.collision_mask = 0
	add_child(body)

	var has_top := Assets.has_art("tiles/wall_top.png")
	var has_face := Assets.has_art("tiles/wall_face.png")
	var has_shadow := Assets.has_art("tiles/wall_shadow.png")

	for y in MAP_H:
		for x in MAP_W:
			if _is_floor(x, y):
				continue
			var c := Vector2(x * TILE + 8, y * TILE + 8)
			if has_top:
				_sprite("tiles/wall_top.png", c, 0)
			else:
				_quad(Rect2(x * TILE, y * TILE, TILE, TILE), Color("343d47"), 0)

			var cs := CollisionShape2D.new()
			var shape := RectangleShape2D.new()
			shape.size = Vector2(TILE, TILE)
			cs.shape = shape
			cs.position = c
			body.add_child(cs)

			var occ := LightOccluder2D.new()
			var op := OccluderPolygon2D.new()
			op.polygon = PackedVector2Array([
				Vector2(x * TILE, y * TILE), Vector2(x * TILE + TILE, y * TILE),
				Vector2(x * TILE + TILE, y * TILE + TILE), Vector2(x * TILE, y * TILE + TILE)])
			op.closed = true
			occ.occluder = op
			add_child(occ)

			if _is_floor(x, y + 1):
				if has_face:
					# the face hangs into the floor tile below so the light can
					# actually reach it (occluders only cover the wall tile itself)
					_sprite("tiles/wall_face.png", Vector2(c.x, y * TILE + TILE + 2), 1)
				else:
					_quad(Rect2(x * TILE, y * TILE + 10, TILE, 6), Color("4a5561"), 1)

func _build_ao() -> void:
	for y in MAP_H:
		for x in MAP_W:
			if not _is_floor(x, y):
				continue
			var px := x * TILE
			var py := y * TILE
			if not _is_floor(x, y - 1):
				_edge_shade(Rect2(px, py, TILE, 5), 0.34, true)
			if not _is_floor(x, y + 1):
				_edge_shade(Rect2(px, py + TILE - 5, TILE, 5), 0.26, false)
			if not _is_floor(x - 1, y):
				_edge_shade_h(Rect2(px, py, 5, TILE), 0.28, true)
			if not _is_floor(x + 1, y):
				_edge_shade_h(Rect2(px + TILE - 5, py, 5, TILE), 0.28, false)

func _edge_shade(rect: Rect2, a: float, from_top: bool) -> void:
	for i in 3:
		var h := rect.size.y / 3.0
		var y := rect.position.y + (i if from_top else 2 - i) * h
		var q := Polygon2D.new()
		q.polygon = PackedVector2Array([
			Vector2(rect.position.x, y), Vector2(rect.end.x, y),
			Vector2(rect.end.x, y + h), Vector2(rect.position.x, y + h)])
		q.color = Color(0, 0, 0, a * (1.0 - i * 0.3))
		q.z_index = -1
		add_child(q)

func _edge_shade_h(rect: Rect2, a: float, from_left: bool) -> void:
	for i in 3:
		var w := rect.size.x / 3.0
		var x := rect.position.x + (i if from_left else 2 - i) * w
		var q := Polygon2D.new()
		q.polygon = PackedVector2Array([
			Vector2(x, rect.position.y), Vector2(x + w, rect.position.y),
			Vector2(x + w, rect.end.y), Vector2(x, rect.end.y)])
		q.color = Color(0, 0, 0, a * (1.0 - i * 0.3))
		q.z_index = -1
		add_child(q)

func _build_lights() -> void:
	var cm := CanvasModulate.new()
	cm.color = Color(0.16, 0.175, 0.215)
	cm_node = cm
	add_child(cm)

	var tex := _radial(128, 1.5)
	var spots := [
		[Vector2(5.5, 4.5), 1.05, false],
		[Vector2(10.5, 5.5), 0.75, false],
		[Vector2(14.5, 5.5), 0.95, false],
		[Vector2(20.5, 4.5), 0.85, false],
		[Vector2(26.5, 5.5), 1.00, true],
		[Vector2(24.5, 10.5), 0.70, false],
		[Vector2(20.0, 16.0), 0.95, false],
		[Vector2(26.5, 17.5), 0.85, false],
		[Vector2(29.0, 14.0), 0.60, false],
		[Vector2(12.5, 16.5), 0.70, false],
		[Vector2(5.5, 15.5), 0.55, true],
		[Vector2(7.0, 19.0), 0.50, true],
		[Vector2(6.5, 22.0), 0.65, false],
		[Vector2(6.0, 26.0), 0.90, false],
		[Vector2(10.0, 26.5), 0.90, false],
	]
	for s in spots:
		var p: Vector2 = s[0] * TILE
		var energy: float = s[1]
		var flick: bool = s[2]
		var l := PointLight2D.new()
		l.texture = tex
		l.texture_scale = 1.7
		l.energy = energy * 0.85
		l.color = Color(1.0, 0.90, 0.78)
		l.shadow_enabled = true
		l.shadow_filter = Light2D.SHADOW_FILTER_PCF5
		l.position = p
		add_child(l)
		lights_ref.append({"pos": p, "radius": 86.0, "node": l, "base": l.energy})
		if flick:
			flicker.append(l)

		if Assets.has_art("tiles/ceiling_lamp.png"):
			_sprite("tiles/ceiling_lamp.png", p, 3)
		else:
			var tube := Polygon2D.new()
			tube.polygon = PackedVector2Array([Vector2(-5, -1), Vector2(5, -1), Vector2(5, 1), Vector2(-5, 1)])
			tube.color = Color(1.0, 0.92, 0.74)
			tube.position = p
			tube.z_index = 3
			add_child(tube)

func _radial(px: int, power: float) -> ImageTexture:
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

func _prop(art: String, cell: Vector2, z: int = 1, fallback_color: Color = Color.TRANSPARENT) -> void:
	var pos := cell * TILE
	if Assets.has_art("tiles/" + art):
		_sprite("tiles/" + art, pos, z)
	elif fallback_color.a > 0.0:
		_quad(Rect2(pos - Vector2(10, 6), Vector2(20, 12)), fallback_color, z)

func _build_props() -> void:
	_prop("locker.png", Vector2(3.5, 7.5), 1, Color("3a4650"))
	_prop("chair.png", Vector2(7.5, 3.5), 1, Color("3a4650"))
	_prop("vent.png", Vector2(15.5, 3.5), 1, Color("2c343c"))
	_prop("blood_splat.png", Vector2(21.5, 6.0), 0)
	_prop("corpse.png", Vector2(28.5, 6.0), 1, Color("7a4a20"))
	_prop("crate.png", Vector2(13.0, 7.5), 1, Color("4a3a28"))
	_prop("crate.png", Vector2(29.0, 3.5), 1, Color("4a3a28"))
	_prop("hazard_sign.png", Vector2(12.5, 3.5), 2)
	_prop("desk.png", Vector2(21.0, 15.0), 1, Color("3d474f"))
	_prop("terminal.png", Vector2(21.0, 15.0), 2, Color("1f4b6b"))
	_prop("desk.png", Vector2(27.0, 18.0), 1, Color("3d474f"))
	_prop("save_terminal.png", Vector2(27.0, 18.0), 2, Color("2f6b3a"))
	_prop("chair.png", Vector2(22.0, 16.0), 1, Color("3a4650"))
	_prop("corpse.png", Vector2(18.5, 19.0), 1, Color("7a4a20"))
	_prop("bodybag.png", Vector2(20.0, 19.5), 1, Color("1c1c20"))
	_prop("locker.png", Vector2(29.5, 19.5), 1, Color("3a4650"))
	_prop("locker.png", Vector2(29.5, 18.5), 1, Color("3a4650"))
	_prop("barrel.png", Vector2(4.5, 18.5), 1, Color("4a4038"))
	_prop("barrel.png", Vector2(5.5, 18.5), 1, Color("4a4038"))
	_prop("crate.png", Vector2(8.0, 19.0), 1, Color("4a3a28"))
	_prop("bodybag.png", Vector2(4.0, 19.0), 1, Color("1c1c20"))
	_prop("blood_splat.png", Vector2(7.0, 17.0), 0)
	_prop("vent.png", Vector2(3.5, 13.5), 1, Color("2c343c"))

func _build_items() -> void:
	items.append(_make_item(Vector2(28.5, 6.0) * TILE, "card", {"level": 1, "label_key": "card_lv1"}))
	items.append(_make_item(Vector2(18.5, 19.0) * TILE, "card", {"level": 2, "label_key": "card_lv2"}))
	items.append(_make_item(Vector2(21.0, 15.0) * TILE, "doc", {
		"title_key": "doc_title",
		"body_key": "doc_body"
	}))
	items.append(_make_item(Vector2(27.0, 18.0) * TILE, "save", {"label": "CHECKPOINT"}))

func _make_item(pos: Vector2, kind: String, data: Dictionary) -> Dictionary:
	var node := Node2D.new()
	node.position = pos
	node.z_index = 2
	add_child(node)
	var it := {"pos": pos, "kind": kind, "data": data, "taken": false, "node": node}
	if kind == "card":
		node.set_script(load("res://scripts/keycard.gd"))
		node.call("setup", data)
	return it

func _build_doors() -> void:
	doors.append(_make_door([Vector2i(24, 9), Vector2i(25, 9)], 1))
	doors.append(_make_door([Vector2i(15, 16), Vector2i(15, 17)], 2))

func _make_door(cells: Array, level: int) -> Dictionary:
	var body := StaticBody2D.new()
	body.collision_layer = 1
	body.collision_mask = 0
	add_child(body)
	var panels := []
	for cell in cells:
		var pos := Vector2(cell.x * TILE + 8, cell.y * TILE + 8)
		var cs := CollisionShape2D.new()
		var shape := RectangleShape2D.new()
		shape.size = Vector2(TILE, TILE)
		cs.shape = shape
		cs.position = pos
		body.add_child(cs)
		var art := "tiles/door_panel.png" if Assets.has_art("tiles/door_panel.png") else ""
		if art != "":
			var s := Sprite2D.new()
			s.texture = Assets.tex(art)
			s.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
			s.position = pos
			s.z_index = 2
			add_child(s)
			panels.append(s)
		else:
			panels.append(_quad(Rect2(pos - Vector2(8, 8), Vector2(16, 16)), Color("8a5a22"), 2))
		if Assets.has_art("tiles/door_frame.png"):
			_sprite("tiles/door_frame.png", pos, 1)
	return {"cells": cells, "level": level, "body": body, "panels": panels, "open": false,
			"center": Vector2(cells[0].x * TILE + 8, cells[0].y * TILE + 8)}

func _build_triggers() -> void:
	triggers.append({"rect": Rect2(12 * TILE, 2 * TILE, 3 * TILE, 8 * TILE), "kind": "corridor", "fired": false})
	triggers.append({"rect": Rect2(16 * TILE, 13 * TILE, 5 * TILE, 8 * TILE), "kind": "checkpoint", "fired": false})
	triggers.append({"rect": Rect2(3 * TILE, 13 * TILE, 4 * TILE, 8 * TILE), "kind": "power", "fired": false})

func _fire(kind: String) -> void:
	match kind:
		"corridor":
			ui.say(I18n.t("say_corridor"), 3.2)
			ui.set_objective("obj_corridor")
			audio.play("alarm_loop.wav", -12.0)
			burst = 1.8
		"checkpoint":
			ui.set_objective("obj_checkpoint")
			ui.say(I18n.t("say_checkpoint"), 2.4)
			audio.play("door_hiss.wav", -14.0)
		"power":
			ui.say(I18n.t("say_power"), 2.6)
			audio.play("door_close.wav", -14.0)
			burst = 1.2

func _spawn_player() -> void:
	spawn_pos = Vector2(5.5, 5.5) * TILE
	save_pos = spawn_pos
	player = CharacterBody2D.new()
	player.name = "Player"
	player.set_script(load("res://scripts/player.gd"))
	player.collision_layer = 2
	player.collision_mask = 1
	var cs := CollisionShape2D.new()
	var shape := CircleShape2D.new()
	shape.radius = 5.0
	cs.shape = shape
	player.add_child(cs)
	player.position = spawn_pos
	player.lights = lights_ref
	player.audio = audio
	add_child(player)
	player.died.connect(_on_died)

	cam = Camera2D.new()
	cam.position_smoothing_enabled = true
	cam.position_smoothing_speed = 7.0
	cam.limit_left = 0
	cam.limit_top = 0
	cam.limit_right = MAP_W * TILE
	cam.limit_bottom = MAP_H * TILE
	player.add_child(cam)
	cam.make_current()

func _spawn_scp() -> void:
	scp_spawn = Vector2(27.0, 4.5) * TILE
	scp = Node2D.new()
	scp.name = "SCP-173"
	scp.set_script(load("res://scripts/scp173.gd"))
	scp.position = scp_spawn
	add_child(scp)
	scp.setup(player)
	scp.connect("stepped", _on_scp_stepped)

func _build_ui() -> void:
	ui = load("res://scripts/ui.gd").new()
	ui.name = "UI"
	add_child(ui)

func _build_post() -> void:
	var layer := CanvasLayer.new()
	layer.layer = 5
	add_child(layer)
	var rect := ColorRect.new()
	rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var mat := ShaderMaterial.new()
	mat.shader = load("res://shaders/grain.gdshader")
	rect.material = mat
	layer.add_child(rect)

# ---------------------------------------------------------------- flow

func _start_game() -> void:
	ui.show_title(false)
	ui.fade_to(1.0, 0.4)
	await get_tree().create_timer(0.45).timeout
	player.position = spawn_pos
	player.freeze = false
	player.reset_state()
	scp.position = scp_spawn
	st = St.PLAY
	ui.set_objective("obj_cell")
	ui.say(I18n.t("say_start"), 2.8)
	ui.fade_to(0.0, 0.8)
	audio.play("blink.wav", -14.0)

func _on_died() -> void:
	if st == St.DEAD:
		return
	st = St.DEAD
	dead_t = 0.0
	ui.show_dead(true)
	audio.play("stinger.wav", -4.0)
	ui.fade_to(0.55, 0.6)

func _respawn() -> void:
	ui.show_dead(false)
	player.position = save_pos
	player.freeze = false
	player.reset_state()
	scp.position = scp_spawn
	ui.fade_to(0.0, 0.5)
	st = St.PLAY

func _win() -> void:
	st = St.END
	player.freeze = true
	ui.fade_to(0.0, 0.01)
	ui.fade_to(1.0, 1.2)
	await get_tree().create_timer(1.3).timeout
	ui.show_end(true)
	ui.fade_to(0.0, 0.6)

func _on_scp_stepped(dist: float) -> void:
	if dist < 160.0 and cam:
		var k: float = clampf(1.0 - dist / 160.0, 0.0, 1.0)
		cam.offset = Vector2(randf_range(-1, 1), randf_range(-1, 1)) * k * 3.0

# ---------------------------------------------------------------- per-frame

func _process(delta: float) -> void:
	if shot_mode:
		pass
	else:
		match st:
			St.DEAD:
				dead_t += delta
				ui.set_dead_alpha(clampf(dead_t / 0.6, 0.0, 1.0) * 0.85)
				if dead_t > 2.4:
					_respawn()
			St.PLAY:
				_update_prompt()
				_check_triggers()
			St.TITLE:
				ui.show_title(true)

	if player == null:
		return

	if cm_node:
		if burst > 0.0:
			burst -= delta
			var k := 0.25 + 0.75 * float(randi() % 2)
			cm_node.color = Color(0.16, 0.175, 0.215) * k
		else:
			cm_node.color = Color(0.16, 0.175, 0.215)

	# only the lights around the player are powered: distant rooms stay black,
	# which keeps the wing's layout a mystery until you walk into it
	for s in lights_ref:
		var n: PointLight2D = s["node"]
		if n == null:
			continue
		var dd: float = player.position.distance_to(s["pos"])
		var falloff: float = clampf(1.0 - (dd - 108.0) / 42.0, 0.0, 1.0)
		var want: float = float(s["base"]) * falloff
		if flicker.has(n):
			want *= 0.85
		n.energy = lerpf(n.energy, want, clampf(delta * 6.0, 0.0, 1.0))

	# flicker
	for l in flicker:
		var base: float = 1.5 * 0.55
		l.energy = base * (0.55 + 0.45 * sin(Time.get_ticks_msec() / 130.0 + l.position.x))
		if randf() < 0.004:
			l.energy = base * 0.1

	if cam:
		if st != St.PLAY:
			cam.offset = Vector2.ZERO
		else:
			cam.offset = cam.offset.lerp(Vector2.ZERO, clampf(delta * 8.0, 0.0, 1.0))

	var danger := 0.0
	if scp and st == St.PLAY:
		var d: float = player.position.distance_to(scp.position)
		if not met_173 and player.can_see(scp.position):
			met_173 = true
			ui.say(I18n.t("say_173"), 3.4)
			ui.set_objective("obj_corridor")
			audio.play("stinger.wav", -12.0)
		if not player.can_see(scp.position):
			danger = clampf(1.0 - d / 200.0, 0.0, 1.0)
		if danger > 0.35:
			audio.set_heartbeat(true)
		else:
			audio.set_heartbeat(false)

	ui.tick(delta, player.blink_ratio(), player.battery_ratio(), card_level, player.eyes_open, danger)

# ---------------------------------------------------------------- interaction

func _update_prompt() -> void:
	prompt = {}
	var best := 34.0
	for d in doors:
		if d.open:
			continue
		var dist: float = player.position.distance_to(d.center)
		if dist < best and dist < 40.0:
			best = dist
			var txt := I18n.t("prompt_open") if card_level >= d.level else I18n.t("prompt_locked") % d.level
			prompt = {"kind": "door", "ref": d, "text": txt}
	for it in items:
		if it.taken:
			continue
		var dist: float = player.position.distance_to(it.pos)
		if dist < best and dist < 28.0:
			best = dist
			var txt := ""
			match it.kind:
				"card": txt = I18n.t("prompt_take") % I18n.t(it.data.label_key)
				"doc": txt = I18n.t("prompt_read")
				"save": txt = I18n.t("prompt_save")
			prompt = {"kind": it.kind, "ref": it, "text": txt}
	if prompt.is_empty():
		ui.set_prompt("")
	else:
		ui.set_prompt(prompt.text)

func _interact() -> void:
	if prompt.is_empty():
		return
	match prompt.kind:
		"door":
			var d = prompt.ref
			if card_level >= d.level:
				_open_door(d)
			else:
				audio.play("keycard_deny.wav", -3.0)
				ui.set_prompt(I18n.t("prompt_locked") % d.level)
		"card":
			var it = prompt.ref
			it.taken = true
			it.node.queue_free()
			card_level = maxi(card_level, int(it.data.level))
			audio.play("pickup.wav", -2.0)
			ui.set_objective("obj_door1" if card_level == 1 else "obj_exit")
		"doc":
			st = St.DOC
			player.freeze = true
			ui.show_doc(I18n.t(prompt.ref.data.title_key), I18n.t(prompt.ref.data.body_key))
			audio.play("pickup.wav", -8.0)
		"save":
			save_pos = player.position
			audio.play("keycard_beep.wav", -3.0)
			ui.set_objective("obj_saved")

func _open_door(d) -> void:
	d.open = true
	if d.body:
		d.body.queue_free()
	for p in d.panels:
		if p is Sprite2D and Assets.has_art("tiles/door_panel_open.png"):
			p.texture = Assets.tex("tiles/door_panel_open.png")
		elif p is Polygon2D:
			p.color = Color("2f6b3a")
	audio.play("door_hiss.wav", -4.0)

func _check_triggers() -> void:
	for t in triggers:
		if t.fired:
			continue
		if t.rect.has_point(player.position):
			t.fired = true
			_fire(t.kind)
	if exit_zone.size.x > 0 and exit_zone.has_point(player.position):
		_win()

# ---------------------------------------------------------------- input

func _input(event: InputEvent) -> void:
	if not (event is InputEventKey) or not event.pressed or event.echo:
		return
	var k: int = event.physical_keycode
	if k == KEY_L:
		I18n.toggle()
		ui.refresh()
		return
	match st:
		St.TITLE:
			if k == KEY_ENTER or k == KEY_KP_ENTER or k == KEY_SPACE:
				_start_game()
		St.PLAY:
			if k == KEY_E:
				_interact()
			elif k == KEY_ESCAPE:
				st = St.PAUSE
				player.freeze = true
				ui.show_pause(true)
		St.PAUSE:
			if k == KEY_ESCAPE:
				st = St.PLAY
				player.freeze = false
				ui.show_pause(false)
			elif k == KEY_Q:
				get_tree().quit()
		St.DOC:
			if k == KEY_E or k == KEY_ESCAPE:
				ui.hide_doc()
				st = St.PLAY
				player.freeze = false
		St.END:
			if k == KEY_ESCAPE:
				get_tree().quit()
			elif k == KEY_R:
				get_tree().reload_current_scene()
