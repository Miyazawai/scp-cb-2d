extends Node2D
## SCP-173 — "moves only while unobserved", implemented as discrete teleport steps.
##
## It never glides. While the player cannot see it, every STEP_INTERVAL it
## snaps STEP_DIST forward along a clear line toward the player. Look back and
## it is simply somewhere new, frozen mid-stride. That is what makes it feel
## instant instead of slow.

signal stepped(distance_to_player: float)

const Assets := preload("res://scripts/assets.gd")

const STEP_DIST := 40.0          # ~2.5 tiles per jump
const STEP_INTERVAL := 0.24      # one jump per forced blink, ~4/s while you look away
const KILL_DIST := 8.5
const MAX_STANDOFF := 6.0        # it never lands right on top of you; it kills first

var player: CharacterBody2D = null
var hold := false                # debug/screenshot: keep it still
var active := false              # dormant until the containment-failure beat
var _timer := 0.0
var _shown := false
var _flash := 0.0

var _sfx: AudioStreamPlayer2D = null
var _sprite: Sprite2D = null
var _tex_idle: Texture2D = null
var _tex_step: Texture2D = null
var _tex_lunge: Texture2D = null
var _look_t := 0.0

func _ready() -> void:
	_tex_idle = Assets.tex("chars/scp173_idle.png")
	_tex_step = Assets.tex("chars/scp173_step.png")
	_tex_lunge = Assets.tex("chars/scp173_lunge.png")
	if _tex_idle:
		_sprite = Sprite2D.new()
		_sprite.texture = _tex_idle
		_sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		_sprite.offset = Vector2(0, -12)
		_sprite.z_index = 3
		add_child(_sprite)

	_sfx = AudioStreamPlayer2D.new()
	var s := Assets.snd("scp_step.wav")
	_sfx.stream = s if s != null else _make_scrape()
	_sfx.max_distance = 300.0
	_sfx.volume_db = -4.0
	add_child(_sfx)

func setup(p: CharacterBody2D) -> void:
	player = p

func _process(delta: float) -> void:
	if player == null or player.freeze:
		return
	_flash = maxf(0.0, _flash - delta * 5.0)

	var seen: bool = player.can_see(global_position)
	_shown = seen

	if seen:
		# reset the wind-up so the first step after you look away is never free
		_timer = 0.0
	elif not hold and active:
		_timer += delta
		while _timer >= STEP_INTERVAL:
			_timer -= STEP_INTERVAL
			_step()

	queue_redraw()

func _step() -> void:
	var to_player: Vector2 = player.global_position - global_position
	var dist := to_player.length()
	if dist <= KILL_DIST:
		player.die()
		return
	# it stalks you, it does not teleport across the wing
	if dist > 340.0:
		return

	var dir := to_player / dist
	var travel := minf(STEP_DIST, dist - MAX_STANDOFF)
	if travel <= 0.5:
		return

	# pick the first arc with a clear line; a statue cannot clip through walls
	var space := get_world_2d().direct_space_state
	for deg in [0.0, 18.0, -18.0, 36.0, -36.0, 60.0, -60.0]:
		var d: Vector2 = dir.rotated(deg_to_rad(deg))
		var target: Vector2 = global_position + d * travel
		var q := PhysicsRayQueryParameters2D.create(global_position, target, 1)
		if space.intersect_ray(q).is_empty():
			global_position = target
			_flash = 1.0
			if _sfx and not _sfx.playing:
				_sfx.play()
			stepped.emit(global_position.distance_to(player.global_position))
			if global_position.distance_to(player.global_position) < KILL_DIST:
				player.die()
			return

func _make_scrape() -> AudioStreamWAV:
	var rate := 22050
	var n := int(rate * 0.14)
	var data := PackedByteArray()
	data.resize(n * 2)
	var rng := RandomNumberGenerator.new()
	rng.seed = 90210
	var prev := 0.0
	for i in n:
		var t := float(i) / float(n)
		var env := pow(1.0 - t, 2.4)
		var noise: float = rng.randf_range(-1.0, 1.0)
		prev = prev * 0.70 + noise * 0.30
		var v: float = prev * env * 0.75
		data.encode_s16(i * 2, int(clampf(v, -1.0, 1.0) * 32767.0))
	var st := AudioStreamWAV.new()
	st.format = AudioStreamWAV.FORMAT_16_BITS
	st.mix_rate = rate
	st.stereo = false
	st.data = data
	return st

func _draw() -> void:
	var base := Color("b7b0a2")
	if _sprite != null:
		# sprite mode: swap frames instead of drawing
		var d: float = player.global_position.distance_to(global_position) if player else 999.0
		if d < 40.0 and _tex_lunge:
			_sprite.texture = _tex_lunge
		elif _flash > 0.05 and _tex_step:
			_sprite.texture = _tex_step
		else:
			_sprite.texture = _tex_idle
		return
	# faint afterimage of the last position, sells the "it just moved" read
	if _flash > 0.01:
		var a := _flash * 0.22
		draw_rect(Rect2(-4, 1, 8, 7), Color(base.r, base.g, base.b, a))
		draw_rect(Rect2(-3, -7, 6, 8), Color(base.r, base.g, base.b, a))
	draw_rect(Rect2(-4, 1, 8, 7), base)
	draw_rect(Rect2(-3, -7, 6, 8), base.lightened(0.06))
	draw_rect(Rect2(-8, 2, 4, 6), base.darkened(0.08))
	draw_rect(Rect2(4, 2, 4, 6), base.darkened(0.08))
	draw_rect(Rect2(-4, 8, 3, 3), base.darkened(0.14))
	draw_rect(Rect2(1, 8, 3, 3), base.darkened(0.14))
	draw_rect(Rect2(-2, -4, 4, 1), base.darkened(0.30))
