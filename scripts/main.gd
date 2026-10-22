extends Node2D
## Vertical slice: one wing of Light Containment. Cell -> corridor (173) ->
## checkpoint (save / document) -> power room -> exit.

const Assets := preload("res://scripts/assets.gd")
const I18n := preload("res://scripts/i18n.gd")

const TILE := 16
var MAP_W := 40
var MAP_H := 32

enum St { TITLE, PLAY, PAUSE, DOC, DEAD, END, INV }

var grid: Array = []
var level: Dictionary = {}
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
var hl_layer: CanvasLayer = null
var hl: Sprite2D = null

var card_level := 0
var inv: Array = []
var docs_found: Dictionary = {}
var _sc_fail := 0
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
	for arg in _args():
		if arg == "--validate" or arg.begins_with("--validate="):
			_validate_level(arg)
			return
	level = _load_level("res://levels/act1.json")
	MAP_W = int(level["size"][0])
	MAP_H = int(level["size"][1])
	var ex: Array = level["exit"]["rect"]
	exit_zone = Rect2(ex[0] * TILE, ex[1] * TILE, ex[2] * TILE, ex[3] * TILE)

	audio = load("res://scripts/audio.gd").new()
	audio.name = "Audio"
	add_child(audio)

	_build_grid()
	_build_floor()
	_build_walls()
	_build_ao()
	_build_lights()
	_build_props()
	_build_decals()
	_build_items()
	_build_doors()
	_build_triggers()
	_spawn_player()
	_spawn_scp()
	_build_ui()
	_build_post()
	_build_highlight()

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

func _load_level(path: String) -> Dictionary:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		push_error("level not found: " + path)
		return {"size": [40, 32], "areas": [], "lights": [], "props": [], "items": [],
			"doors": [], "triggers": [], "scps": [], "spawn": [5.5, 5.5], "exit": {"rect": [9, 25, 3, 3]}}
	var parsed = JSON.parse_string(f.get_as_text())
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("level json is not an object: " + path)
		return {"size": [40, 32], "areas": [], "lights": [], "props": [], "items": [],
			"doors": [], "triggers": [], "scps": [], "spawn": [5.5, 5.5], "exit": {"rect": [9, 25, 3, 3]}}
	return parsed

func _pacing_report() -> void:
	var lv := _load_level("res://levels/act1.json")
	var w := int(lv["size"][0])
	var h := int(lv["size"][1])
	var g := []
	for y in h:
		var row := []
		for x in w:
			row.append("#")
		g.append(row)
	for a in lv["areas"]:
		var r: Array = a["rect"]
		for yy in range(int(r[1]), int(r[1]) + int(r[3])):
			for xx in range(int(r[0]), int(r[0]) + int(r[2])):
				if xx >= 0 and yy >= 0 and xx < w and yy < h:
					g[yy][xx] = "."
	var door_cells := {}
	for d in lv.get("doors", []):
		for c in d["cells"]:
			door_cells[Vector2i(int(c[0]), int(c[1]))] = true

	var route := [
		{"name": "spawn -> corridor",  "at": [13.0, 4.5],  "dwell": 15},
		{"name": "corridor -> locker", "at": [15.0, 12.5], "dwell": 45},
		{"name": "locker -> door 1",   "at": [24.5, 8.5],  "dwell": 20},
		{"name": "door 1 -> log",      "at": [21.0, 15.0], "dwell": 40},
		{"name": "log -> card 2",      "at": [18.5, 19.0], "dwell": 30},
		{"name": "card 2 -> door 2",   "at": [14.2, 16.5], "dwell": 20},
		{"name": "door 2 -> power",    "at": [4.5, 17.5],  "dwell": 40},
		{"name": "power -> elevator",  "at": [29.5, 14.5], "dwell": 30},
	]

	var sp: Array = lv["spawn"]
	var cur := Vector2i(int(sp[0]), int(sp[1]))
	var total_travel := 0
	var total_dwell := 0
	print("PACING name                 tiles   travel_s  dwell_s")
	for step in route:
		var at: Array = step["at"]
		var dst := Vector2i(int(at[0]), int(at[1]))
		var dist := _bfs_tiles(g, w, h, door_cells, cur, dst)
		var travel := float(dist) * 16.0 / 44.0
		total_travel += int(travel)
		total_dwell += int(step["dwell"])
		print("PACING %-20s %5d %9.0f %8d" % [step["name"], dist, travel, int(step["dwell"])])
		cur = dst
	var total := total_travel + total_dwell
	print("PACING total_travel_s=%d total_dwell_s=%d total_s=%d total_min=%.1f" % [
		total_travel, total_dwell, total, float(total) / 60.0])
	print("PACING target_min=25..35 %s" % ["OK" if total >= 25 * 60 and total <= 35 * 60 else "OUT OF RANGE"])
	get_tree().quit(0)

func _bfs_tiles(g: Array, w: int, h: int, door_cells: Dictionary, from: Vector2i, to: Vector2i) -> int:
	var dist := {from: 0}
	var q: Array = [from]
	var head := 0
	while head < q.size():
		var c: Vector2i = q[head]
		head += 1
		if c == to:
			return int(dist[c])
		for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
			var n: Vector2i = c + d
			if n.x < 0 or n.y < 0 or n.x >= w or n.y >= h:
				continue
			if dist.has(n):
				continue
			if g[n.y][n.x] != "." and not door_cells.has(n):
				continue
			dist[n] = int(dist[c]) + 1
			q.append(n)
	return 99

func _validate_level(arg: String) -> void:
	var path := "res://levels/act1.json"
	if arg.begins_with("--validate="):
		var raw := arg.substr(11)
		path = raw if raw.begins_with("res://") else "res://" + raw
	var lv := _load_level(path)
	if lv.is_empty() or not lv.has("areas"):
		print("VALIDATE %s -> cannot load" % path)
		get_tree().quit(2)
		return

	var w := int(lv["size"][0])
	var h := int(lv["size"][1])
	var g := []
	for y in h:
		var row := []
		for x in w:
			row.append("#")
		g.append(row)
	for a in lv["areas"]:
		var r: Array = a["rect"]
		if int(r[2]) <= 0 or int(r[3]) <= 0:
			print("  ! area %s has an empty rect" % a.get("id", "?"))
		for yy in range(int(r[1]), int(r[1]) + int(r[3])):
			for xx in range(int(r[0]), int(r[0]) + int(r[2])):
				if xx >= 0 and yy >= 0 and xx < w and yy < h:
					g[yy][xx] = "."
				else:
					print("  ! area %s leaves the map at %s" % [a.get("id", "?"), Vector2i(xx, yy)])

	var door_cells := {}
	for d in lv.get("doors", []):
		for c in d["cells"]:
			door_cells[Vector2i(int(c[0]), int(c[1]))] = true

	var sp: Array = lv["spawn"]
	var start := Vector2i(int(sp[0]), int(sp[1]))
	var seen := {start: true}
	var q: Array = [start]
	while q.size() > 0:
		var c: Vector2i = q.pop_back()
		for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
			var n: Vector2i = c + d
			if n.x < 0 or n.y < 0 or n.x >= w or n.y >= h:
				continue
			if seen.has(n):
				continue
			if g[n.y][n.x] != "." and not door_cells.has(n):
				continue
			seen[n] = true
			q.append(n)

	var problems: Array = []
	if not seen.has(start):
		problems.append("spawn %s is not on floor" % start)

	for it in lv.get("items", []):
		var at: Array = it["at"]
		var c := Vector2i(int(at[0]), int(at[1]))
		var inb := c.x >= 0 and c.y >= 0 and c.x < w and c.y < h
		if not inb or g[c.y][c.x] != ".":
			problems.append("item %s is not on floor at %s" % [it.get("kind", "?"), c])
		elif not seen.has(c):
			problems.append("item %s is unreachable at %s" % [it.get("kind", "?"), c])

	for p in lv.get("props", []):
		var at2: Array = p["at"]
		var c2 := Vector2i(int(at2[0]), int(at2[1]))
		if not (c2.x >= 0 and c2.y >= 0 and c2.x < w and c2.y < h) or g[c2.y][c2.x] != ".":
			problems.append("prop %s is not on floor at %s" % [p.get("art", "?"), c2])

	for dc in lv.get("decals", []):
		var at3: Array = dc["at"]
		var c3 := Vector2i(int(at3[0]), int(at3[1]))
		if not (c3.x >= 0 and c3.y >= 0 and c3.x < w and c3.y < h) or g[c3.y][c3.x] != ".":
			problems.append("decal %s is not on floor at %s" % [dc.get("art", "?"), c3])

	var doc_ids := {}
	for doc in lv.get("documents", []):
		var did := String(doc.get("id", ""))
		if did == "":
			problems.append("document without an id")
		elif doc_ids.has(did):
			problems.append("duplicate document id: %s" % did)
		doc_ids[did] = true
		var at4: Array = doc["at"]
		var c4 := Vector2i(int(at4[0]), int(at4[1]))
		if not (c4.x >= 0 and c4.y >= 0 and c4.x < w and c4.y < h) or g[c4.y][c4.x] != ".":
			problems.append("document %s is not on floor at %s" % [did, c4])
		elif not seen.has(c4):
			problems.append("document %s is unreachable at %s" % [did, c4])

	var allowed := ["say", "objective", "sound", "fade", "teleport", "activate_scp", "end_act", "wait", "blackout", "save"]
	for t in lv.get("triggers", []):
		if not t.has("actions"):
			continue
		for act in t["actions"]:
			var verb := String(act.get("do", ""))
			if not allowed.has(verb):
				problems.append("trigger uses an unknown action: %s" % verb)

	for d in lv.get("doors", []):
		for raw_cell in d["cells"]:
			var cell := Vector2i(int(raw_cell[0]), int(raw_cell[1]))
			if not seen.has(cell):
				problems.append("door cell %s is unreachable" % cell)

	var ex: Array = lv["exit"]["rect"]
	for yy in range(int(ex[1]), int(ex[1]) + int(ex[3])):
		for xx in range(int(ex[0]), int(ex[0]) + int(ex[2])):
			if not seen.has(Vector2i(xx, yy)):
				problems.append("exit tile %s is unreachable" % Vector2i(xx, yy))

	print("VALIDATE %s areas=%d lights=%d props=%d decals=%d docs=%d items=%d doors=%d reachable=%d problems=%d" % [
		path, lv["areas"].size(), lv.get("lights", []).size(), lv.get("props", []).size(),
		lv.get("decals", []).size(), lv.get("documents", []).size(), lv.get("items", []).size(),
		lv.get("doors", []).size(), seen.size(), problems.size()])
	for p in problems:
		print("  ! ", p)
	get_tree().quit(1 if problems.size() > 0 else 0)

func _args() -> PackedStringArray:
	var out := PackedStringArray()
	out.append_array(OS.get_cmdline_args())
	out.append_array(OS.get_cmdline_user_args())
	return out

func _scenarios() -> Dictionary:
	return {
		"act1_walkthrough": [
			{ "do": "assert_state", "value": "PLAY", "label": "session starts in play" },
			{ "do": "near", "to": [5.5, 5.5], "tol": 24.0, "label": "spawns in the cell" },
			{ "do": "teleport", "to": [13.0, 4.5] },
			{ "do": "wait", "secs": 0.4 },
			{ "do": "assert_objective", "value": "obj_corridor", "label": "corridor beat fires" },
			{ "do": "teleport", "to": [15.0, 12.5] },
			{ "do": "wait", "secs": 0.2 },
			{ "do": "interact" },
			{ "do": "assert_card", "value": "1", "label": "level 1 card taken in the locker room" },
			{ "do": "teleport", "to": [24.5, 8.2] },
			{ "do": "wait", "secs": 0.2 },
			{ "do": "interact" },
			{ "do": "teleport", "to": [21.0, 16.2] },
			{ "do": "wait", "secs": 0.2 },
			{ "do": "interact" },
			{ "do": "assert_state", "value": "DOC", "label": "incident log opens" },
			{ "do": "close_doc" },
			{ "do": "assert_docs", "value": "incident_log_1", "label": "incident log recorded" },
			{ "do": "teleport", "to": [18.5, 19.0] },
			{ "do": "wait", "secs": 0.2 },
			{ "do": "interact" },
			{ "do": "assert_card", "value": "2", "label": "level 2 card taken" },
			{ "do": "teleport", "to": [14.2, 16.5] },
			{ "do": "wait", "secs": 0.2 },
			{ "do": "interact" },
			{ "do": "teleport", "to": [10.0, 26.0] },
			{ "do": "wait", "secs": 2.4 },
			{ "do": "assert_state", "value": "END", "label": "reaches the exit" },
		],
		"act1_documents": [
			{ "do": "teleport", "to": [21.0, 16.2] },
			{ "do": "wait", "secs": 0.2 },
			{ "do": "interact" },
			{ "do": "assert_state", "value": "DOC", "label": "log opens" },
			{ "do": "assert_docs", "value": "incident_log_1", "label": "picking it up records it" },
			{ "do": "close_doc" },
			{ "do": "assert_state", "value": "PLAY", "label": "closing returns control" },
			{ "do": "teleport", "to": [13.0, 12.5] },
			{ "do": "wait", "secs": 0.2 },
			{ "do": "interact" },
			{ "do": "close_doc" },
			{ "do": "assert_docs", "value": "dressing_note", "label": "second document also recorded" },
		],
		"act1_terminals": [
			{ "do": "teleport", "to": [13.0, 11.0] },
			{ "do": "wait", "secs": 0.2 },
			{ "do": "interact" },
			{ "do": "wait", "secs": 0.2 },
			{ "do": "teleport", "to": [20.0, 17.0] },
			{ "do": "die" },
			{ "do": "wait", "secs": 3.2 },
			{ "do": "assert_state", "value": "PLAY", "label": "respawns into play" },
			{ "do": "near", "to": [13.0, 11.0], "tol": 28.0, "label": "back at the locker-room terminal" },
		],
		"act1_vending": [
			{ "do": "teleport", "to": [21.0, 11.6] },
			{ "do": "wait", "secs": 0.2 },
			{ "do": "interact" },
			{ "do": "assert_state", "value": "PLAY", "label": "machine does not trap the player" },
			{ "do": "assert_toast", "label": "machine answers with something" },
		],
		"act1_elevator": [
			{ "do": "teleport", "to": [29.5, 14.5] },
			{ "do": "wait", "secs": 0.3 },
			{ "do": "assert_objective", "value": "obj_elevator", "label": "elevator objective set" },
			{ "do": "wait", "secs": 2.6 },
			{ "do": "assert_state", "value": "END", "label": "act card shown" },
			{ "do": "near", "to": [29.5, 14.5], "tol": 40.0, "label": "auto-saved at the elevator" },
		],
		"negative_control": [
			{ "do": "assert_docs", "value": "nope", "label": "this must fail" },
		]
	}

func _state_name(s: int) -> String:
	match s:
		St.TITLE: return "TITLE"
		St.PLAY: return "PLAY"
		St.PAUSE: return "PAUSE"
		St.DOC: return "DOC"
		St.DEAD: return "DEAD"
		St.END: return "END"
		St.INV: return "INV"
	return "?"

func _sc_ok(ok: bool, label: String, detail: String = "") -> void:
	if ok:
		print("  ok   ", label)
	else:
		_sc_fail += 1
		print("  FAIL ", label, "  ", detail)

func _scenario_run(name: String) -> void:
	var all := _scenarios()
	if name == "list":
		for k in all.keys():
			print("SCENARIO ", k)
		get_tree().quit(0)
		return
	if not all.has(name):
		print("SCENARIO unknown: ", name)
		get_tree().quit(2)
		return

	_sc_fail = 0
	card_level = 0
	docs_found.clear()
	st = St.PLAY
	player.freeze = false
	player.reset_state()
	ui.show_title(false)
	ui.fade_to(0.0, 0.01)
	await get_tree().process_frame

	print("SCENARIO ", name)
	for step in all[name]:
		match String(step.get("do", "")):
			"teleport":
				var to: Array = step["to"]
				player.position = Vector2(float(to[0]), float(to[1])) * TILE
			"wait":
				await get_tree().create_timer(float(step.get("secs", 0.1))).timeout
			"interact":
				_update_prompt()
				_interact()
			"close_doc":
				ui.hide_doc()
				st = St.PLAY
				player.freeze = false
			"die":
				player.die()
			"near":
				var t2: Array = step["to"]
				var want := Vector2(float(t2[0]), float(t2[1])) * TILE
				var d := player.position.distance_to(want)
				_sc_ok(d <= float(step.get("tol", 16.0)), String(step.get("label", "near")),
					"dist=%.1f want<=%.1f" % [d, float(step.get("tol", 16.0))])
			"assert_state":
				_sc_ok(_state_name(st) == String(step["value"]), String(step.get("label", "state")),
					"got %s want %s" % [_state_name(st), step["value"]])
			"assert_card":
				_sc_ok(card_level == int(step["value"]), String(step.get("label", "card")),
					"got level %d want %s" % [card_level, step["value"]])
			"assert_toast":
				_sc_ok(ui.toast.text != "", String(step.get("label", "toast")), "toast was empty")
			"assert_docs":
				_sc_ok(docs_found.has(String(step["value"])), String(step.get("label", "docs")),
					"found=%s" % str(docs_found.keys()))
			"assert_objective":
				_sc_ok(String(ui.obj_key) == String(step["value"]), String(step.get("label", "objective")),
					"got %s want %s" % [ui.obj_key, step["value"]])
			_:
				_sc_ok(false, "unknown step " + str(step.get("do", "?")), "")

	print("SCENARIO %s %s failures=%d" % [name, "PASS" if _sc_fail == 0 else "FAIL", _sc_fail])
	get_tree().quit(0 if _sc_fail == 0 else 1)

func _apply_args() -> void:
	var a := _args()
	for arg in a:
		if arg == "--pacing":
			_pacing_report()
			return
	for arg in a:
		if arg.begins_with("--scenario"):
			var nm := "list"
			if arg.contains("="):
				nm = arg.split("=")[1]
			_scenario_run(nm)
			return
	if a.has("--selftest"):
		_selftest()
		return
	if a.has("--audit"):
		print("AUDIT art=", Assets.has_art("tiles/floor_concrete_a.png"),
			" char=", Assets.has_art("chars/player_down_0.png"),
			" snd=", Assets.snd("amb_loop.wav") != null)
		get_tree().quit()
		return
	if a.has("--shot9") or a.has("--shot10"):
		shot_mode = true
		st = St.PLAY
		ui.show_title(false)
		ui.fade_to(0.0, 0.01)
		player.use_mouse_aim = false
		player.facing = Vector2.RIGHT
		scp.hold = true
		scp.position = Vector2(27.0, 4.5) * TILE
		if a.has("--shot9"):
			player.position = Vector2(15.5, 13.6) * TILE
			card_level = 0
			ui.set_objective("obj_cell")
			_shot("demo_shot9.png")
		else:
			player.position = Vector2(21.0, 12.4) * TILE
			card_level = 1
			ui.set_objective("obj_checkpoint")
			_shot("demo_shot10.png")
		return
	if a.has("--shot8"):
		shot_mode = true
		st = St.INV
		ui.show_title(false)
		ui.fade_to(0.0, 0.01)
		player.position = Vector2(21.0 * TILE, 16.2 * TILE)
		scp.position = Vector2(27.0 * TILE, 4.5 * TILE)
		scp.hold = true
		card_level = 1
		_inv_add("battery")
		_inv_add("battery")
		_inv_add("card1")
		ui.show_inv(_inv_entries(), 0)
		_shot("demo_shot8.png")
		return
	if a.has("--shot7"):
		shot_mode = true
		st = St.PLAY
		ui.show_title(false)
		ui.fade_to(0.0, 0.01)
		player.use_mouse_aim = false
		player.facing = Vector2.UP
		player.position = Vector2(21.0 * TILE, 16.2 * TILE)
		scp.position = Vector2(27.0 * TILE, 4.5 * TILE)
		scp.hold = true
		card_level = 1
		ui.set_objective("obj_checkpoint")
		_shot("demo_shot7.png")
		return
	if a.has("--start"):
		_shot_after_start()
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

func _shot_after_start() -> void:
	await get_tree().create_timer(0.6).timeout
	_start_game()
	await get_tree().create_timer(2.4).timeout
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	img.save_png(ProjectSettings.globalize_path("res://demo_shot6.png"))
	print("SHOT SAVED: demo_shot6.png")
	get_tree().quit()

func _shot(fname: String) -> void:
	await get_tree().create_timer(1.4).timeout
	_update_prompt()
	_update_highlight()
	ui.tick(0.0, player.blink_ratio(), player.battery_ratio(), player.stamina_ratio(), card_level, player.eyes_open, 0.0)
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
	for a in level["areas"]:
		var r: Array = a["rect"]
		_carve(int(r[0]), int(r[1]), int(r[0]) + int(r[2]) - 1, int(r[1]) + int(r[3]) - 1)
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
	for L in level["lights"]:
		var at: Array = L["at"]
		var p := Vector2(float(at[0]), float(at[1])) * TILE
		var energy := float(L["energy"])
		var flick := bool(L.get("flicker", false))
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
	for p in level["props"]:
		var at: Array = p["at"]
		_prop(String(p["art"]), Vector2(float(at[0]), float(at[1])), int(p.get("z", 1)), Color.TRANSPARENT)
func _build_decals() -> void:
	for dc in level.get("decals", []):
		var at: Array = dc["at"]
		var art := String(dc["art"])
		if Assets.has_art("tiles/" + art):
			var spr := _sprite("tiles/" + art, Vector2(float(at[0]), float(at[1])) * TILE, int(dc.get("z", 0)))
			if spr and dc.has("tint"):
				var tint: Array = dc["tint"]
				spr.modulate = Color(float(tint[0]), float(tint[1]), float(tint[2]), float(tint[3]) if tint.size() > 3 else 1.0)

func _build_items() -> void:
	for it in level["items"]:
		var at: Array = it["at"]
		var data := {}
		if it.has("level"):
			data["level"] = int(it["level"])
		if it.has("label_key"):
			data["label_key"] = String(it["label_key"])
		items.append(_make_item(Vector2(float(at[0]), float(at[1])) * TILE, String(it["kind"]), data))
	for doc in level.get("documents", []):
		var dat: Array = doc["at"]
		var dd := {
			"doc_id": String(doc["id"]),
			"title_key": String(doc["title_key"]),
			"body_key": String(doc["body_key"]),
			"critical": bool(doc.get("critical", false)),
		}
		items.append(_make_item(Vector2(float(dat[0]), float(dat[1])) * TILE, "doc", dd))
func _make_item(pos: Vector2, kind: String, data: Dictionary) -> Dictionary:
	var node := Node2D.new()
	node.position = pos
	node.z_index = 2
	add_child(node)
	var it := {"pos": pos, "kind": kind, "data": data, "taken": false, "node": node}
	if kind == "card" or kind == "battery":
		node.set_script(load("res://scripts/pickup.gd"))
		var d2: Dictionary = data.duplicate()
		d2["kind"] = kind
		node.call("setup", d2)
	return it

func _build_doors() -> void:
	for d in level["doors"]:
		var cells := []
		for c in d["cells"]:
			cells.append(Vector2i(int(c[0]), int(c[1])))
		doors.append(_make_door(cells, int(d["level"])))
func _make_door(cells: Array, level: int) -> Dictionary:
	var body := StaticBody2D.new()
	body.collision_layer = 1
	body.collision_mask = 0
	add_child(body)
	var panels := []
	var shapes := []
	for cell in cells:
		var pos := Vector2(cell.x * TILE + 8, cell.y * TILE + 8)
		var cs := CollisionShape2D.new()
		var shape := RectangleShape2D.new()
		shape.size = Vector2(TILE, TILE)
		cs.shape = shape
		cs.position = pos
		body.add_child(cs)
		shapes.append(cs)
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
	return {"cells": cells, "level": level, "body": body, "panels": panels, "shapes": shapes,
			"open": false, "force_t": 0.0,
			"center": Vector2(cells[0].x * TILE + 8, cells[0].y * TILE + 8)}

func _set_door(d, open: bool) -> void:
	if d.open == open:
		return
	d.open = open
	for cs in d.shapes:
		cs.set_deferred("disabled", open)
	for p in d.panels:
		if p is Sprite2D:
			var key := "tiles/door_panel_open.png" if open else "tiles/door_panel.png"
			if Assets.has_art(key):
				p.texture = Assets.tex(key)
		elif p is Polygon2D:
			p.color = Color("2f6b3a") if open else Color("8a5a22")
	if open:
		audio.play("door_hiss.wav", -4.0)
	else:
		audio.play("door_close.wav", -4.0)

func _build_triggers() -> void:
	for t in level["triggers"]:
		var r: Array = t["rect"]
		triggers.append({
			"rect": Rect2(float(r[0]) * TILE, float(r[1]) * TILE, float(r[2]) * TILE, float(r[3]) * TILE),
			"kind": String(t.get("kind", "")),
			"actions": t.get("actions", []),
			"fired": false
		})
func _run_actions(actions: Array) -> void:
	for act in actions:
		match String(act.get("do", "")):
			"say":
				ui.say(I18n.t(String(act.get("key", ""))), float(act.get("secs", 3.0)))
			"objective":
				ui.set_objective(String(act.get("key", "")))
			"sound":
				audio.play(String(act.get("file", "")), float(act.get("db", 0.0)))
			"fade":
				ui.fade_to(float(act.get("to", 0.0)), float(act.get("secs", 0.6)))
			"activate_scp":
				if scp:
					scp.active = true
			"teleport":
				var to: Array = act["to"]
				if player:
					player.position = Vector2(float(to[0]), float(to[1])) * TILE
			"save":
				save_pos = player.position
			"wait":
				await get_tree().create_timer(float(act.get("secs", 0.5))).timeout
			"blackout":
				burst = float(act.get("secs", 1.0))
			"end_act":
				st = St.END
				player.freeze = true
				ui.show_end(true)

func _fire(kind: String) -> void:
	match kind:
		"corridor":
			scp.active = true
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
	var sp: Array = level["spawn"]
	spawn_pos = Vector2(float(sp[0]), float(sp[1])) * TILE
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
	var s0: Array = level["scps"][0]["at"]
	scp_spawn = Vector2(float(s0[0]), float(s0[1])) * TILE
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
	if st != St.TITLE:
		return
	# flip the state first: _process re-shows the title every frame while we are
	# still in TITLE, which would undo the hide below during the fade-out.
	st = St.PLAY
	ui.show_title(false)
	ui.fade_to(1.0, 0.4)
	await get_tree().create_timer(0.45).timeout
	player.position = spawn_pos
	player.freeze = false
	player.reset_state()
	scp.position = scp_spawn
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

func _ring_texture(px: int, r: float, w: float) -> ImageTexture:
	var img := Image.create(px, px, false, Image.FORMAT_RGBA8)
	var c := px * 0.5
	for y in px:
		for x in px:
			var dd := Vector2(x + 0.5 - c, y + 0.5 - c).length()
			var a := 0.0
			if absf(dd - r) <= w:
				a = 1.0 - absf(dd - r) / w
			img.set_pixel(x, y, Color(1, 1, 1, a * a))
	return ImageTexture.create_from_image(img)

func _build_highlight() -> void:
	hl_layer = CanvasLayer.new()
	hl_layer.layer = 2
	hl_layer.follow_viewport_enabled = true
	add_child(hl_layer)
	hl = Sprite2D.new()
	hl.texture = _ring_texture(48, 15.0, 2.2)
	hl.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	hl.visible = false
	hl_layer.add_child(hl)

func _update_highlight() -> void:
	if hl == null:
		return
	if st != St.PLAY or prompt.is_empty() or not prompt.has("pos"):
		hl.visible = false
		return
	hl.visible = true
	hl.position = prompt["pos"] + Vector2(0, 2)
	var t := Time.get_ticks_msec() / 1000.0
	var k := 0.5 + 0.5 * absf(sin(t * 3.4))
	hl.scale = Vector2.ONE * (1.0 + 0.06 * sin(t * 3.4))
	var c := Color("f0c76b")
	if prompt.kind == "door":
		var d = prompt.ref
		if d.open:
			c = Color("6fd08a")
		elif card_level >= d.level:
			c = Color("f0c76b")
		else:
			c = Color("d04848")
	hl.modulate = Color(c.r, c.g, c.b, 0.35 + 0.55 * k)

func _door_force(delta: float) -> void:
	# 173 does not need a card: it simply walks through a closed door.
	for d in doors:
		if d.open:
			d.force_t = 0.0
			continue
		if scp and scp.active and scp.position.distance_to(d.center) < 30.0:
			d.force_t += delta
			if d.force_t > 0.8:
				d.force_t = 0.0
				_set_door(d, true)
				audio.play("door_close.wav", -1.0)
				audio.play("scp_step.wav", -1.0)
				_on_scp_stepped(0.0)
		else:
			d.force_t = 0.0

func _process(delta: float) -> void:
	if ui == null:
		return
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
				_door_force(delta)
			St.TITLE:
				ui.show_title(true)

	_update_highlight()

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

	ui.tick(delta, player.blink_ratio(), player.battery_ratio(), player.stamina_ratio(), card_level, player.eyes_open, danger)

# ---------------------------------------------------------------- interaction

func _update_prompt() -> void:
	prompt = {}
	var best := 34.0
	for d in doors:
		var dist: float = player.position.distance_to(d.center)
		if dist < best and dist < 44.0:
			best = dist
			var txt := ""
			if d.open:
				txt = I18n.t("prompt_close")
			elif card_level >= d.level:
				txt = I18n.t("prompt_open")
			else:
				txt = I18n.t("prompt_locked") % d.level
			prompt = {"kind": "door", "ref": d, "text": txt, "pos": d.center}
	for it in items:
		if it.taken:
			continue
		var dist: float = player.position.distance_to(it.pos)
		if dist < best and dist < 28.0:
			best = dist
			var txt := ""
			match it.kind:
				"card": txt = I18n.t("prompt_take") % I18n.t(it.data.label_key)
				"battery": txt = I18n.t("prompt_take_b") % I18n.t("item_battery")
				"doc": txt = I18n.t("prompt_read")
				"save": txt = I18n.t("prompt_save")
				"vending": txt = I18n.t("prompt_vend")
			prompt = {"kind": it.kind, "ref": it, "text": txt, "pos": it.pos}
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
			if d.open:
				_set_door(d, false)
			elif card_level >= d.level:
				_set_door(d, true)
			else:
				audio.play("keycard_deny.wav", -3.0)
				ui.set_prompt(I18n.t("prompt_locked") % d.level)
		"card":
			var it = prompt.ref
			it.taken = true
			it.node.queue_free()
			card_level = maxi(card_level, int(it.data.level))
			_inv_add("card%d" % card_level)
			audio.play("pickup.wav", -2.0)
			ui.set_objective("obj_door1" if card_level == 1 else "obj_exit")
		"doc":
			var meta = prompt.ref.data
			if meta.has("doc_id"):
				docs_found[String(meta["doc_id"])] = true
			st = St.DOC
			player.freeze = true
			ui.show_doc(I18n.t(prompt.ref.data.title_key), I18n.t(prompt.ref.data.body_key))
			audio.play("pickup.wav", -8.0)
		"battery":
			var it2 = prompt.ref
			it2.taken = true
			it2.node.queue_free()
			_inv_add("battery")
			audio.play("pickup.wav", -2.0)
			ui.say(I18n.t("say_battery"), 1.8)
		"vending":
			var roll := randf()
			if roll < 0.25:
				player.stamina = minf(100.0, player.stamina + 35.0)
				ui.say(I18n.t("vending_stamina"), 2.2)
			elif roll < 0.5:
				player.battery = minf(100.0, player.battery + 45.0)
				ui.say(I18n.t("vending_battery"), 2.2)
			elif roll < 0.8:
				ui.say(I18n.t("vending_nothing"), 2.2)
			else:
				player.stamina = maxf(0.0, player.stamina - 30.0)
				ui.say(I18n.t("vending_bad"), 2.2)
			audio.play("pickup.wav", -4.0)
		"save":
			save_pos = player.position
			audio.play("keycard_beep.wav", -3.0)
			ui.set_objective("obj_saved")

func _open_door(d) -> void:
	_set_door(d, true)

func _inv_add(id: String) -> void:
	for e in inv:
		if String(e.id) == id:
			e.count += 1
			return
	inv.append({"id": id, "count": 1})

func _inv_entries() -> Array:
	var out: Array = []
	for e in inv:
		var nm := ""
		match String(e.id):
			"battery": nm = I18n.t("item_battery")
			"card1": nm = I18n.t("item_card") % 1
			"card2": nm = I18n.t("item_card") % 2
			_: nm = String(e.id)
		out.append({"name": nm, "count": int(e.count)})
	return out

func _inv_use(idx: int) -> void:
	if idx < 0 or idx >= inv.size():
		return
	var e: Dictionary = inv[idx]
	if String(e.id) != "battery":
		ui.say(I18n.t("say_no_battery"), 1.2)
		return
	player.battery = minf(100.0, player.battery + 55.0)
	e.count = int(e.count) - 1
	audio.play("keycard_beep.wav", -4.0)
	ui.say(I18n.t("say_use_battery"), 1.8)
	if int(e.count) <= 0:
		inv.erase(e)
	if st == St.INV:
		ui.show_inv(_inv_entries(), -1)

func _check_triggers() -> void:
	for t in triggers:
		if t.fired:
			continue
		if t.rect.has_point(player.position):
			t.fired = true
			if t.get("actions", []).size() > 0:
				_run_actions(t["actions"])
			else:
				_fire(t.kind)
	if exit_zone.size.x > 0 and exit_zone.has_point(player.position):
		_win()

# ---------------------------------------------------------------- input

func _input(event: InputEvent) -> void:
	if not (event is InputEventKey) or not event.pressed or event.echo:
		return
	var k: int = event.physical_keycode
	if (k == KEY_I) and (st == St.PLAY or st == St.INV):
		if st == St.PLAY:
			st = St.INV
			player.freeze = true
			ui.show_inv(_inv_entries(), -1)
		else:
			st = St.PLAY
			player.freeze = false
			ui.hide_inv()
		return
	if k >= KEY_1 and k <= KEY_8 and (st == St.PLAY or st == St.INV):
		_inv_use(k - KEY_1)
		return
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
		St.INV:
			if k == KEY_ESCAPE:
				st = St.PLAY
				player.freeze = false
				ui.hide_inv()
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
