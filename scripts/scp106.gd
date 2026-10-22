extends Node2D
## SCP-106 — the old man. It does not pathfind: it walks the breadcrumb trail the
## player leaves behind. Slower than a walk, so distance is earned, not given.

signal stepped

const Assets := preload("res://scripts/assets.gd")

const SPEED := 34.0
const KILL_DIST := 9.0
const SAMPLE_GAP := 0.28
const TRAIL_MAX := 260

var player: CharacterBody2D = null
var active := false
var hold := false
var trail: Array = []
var idx := 0

var _sample_t := 0.0
var _started := false
var _sfx: AudioStreamPlayer2D = null
var _sfx_t := 0.0

func _ready() -> void:
	_sfx = AudioStreamPlayer2D.new()
	var s := Assets.snd("scp_step.wav")
	if s != null:
		_sfx.stream = s
	_sfx.max_distance = 340.0
	_sfx.volume_db = -6.0
	_sfx.pitch_scale = 0.55
	add_child(_sfx)

func setup(p: CharacterBody2D) -> void:
	player = p

func get_seen() -> int:
	return 0

func _process(delta: float) -> void:
	if player == null or player.freeze or hold or not active:
		return

	if not _started:
		_started = true
		var p0 := player.global_position + Vector2(-70, 0)
		global_position = p0
		trail = [p0, player.global_position]
		idx = 0

	_sample_t += delta
	if _sample_t >= SAMPLE_GAP:
		_sample_t = 0.0
		trail.append(player.global_position)
		if trail.size() > TRAIL_MAX:
			trail.pop_front()
			idx = maxi(0, idx - 1)

	if trail.size() >= 2:
		var target: Vector2 = trail[mini(idx, trail.size() - 1)]
		var to_target := target - global_position
		if to_target.length() < 5.0:
			idx = mini(idx + 1, trail.size() - 1)
		else:
			global_position += to_target.normalized() * SPEED * delta

	if global_position.distance_to(player.global_position) < KILL_DIST:
		player.die()

	_sfx_t -= delta
	if _sfx_t <= 0.0 and global_position.distance_to(player.global_position) < 300.0:
		_sfx_t = 1.4
		if _sfx and not _sfx.playing:
			_sfx.play()
	queue_redraw()

func _draw() -> void:
	# a black column with wet edges; deliberately unlit so it reads as a hole
	draw_circle(Vector2(0, -10), 20.0, Color(0.02, 0.01, 0.02, 0.30))
	draw_rect(Rect2(-6, -26, 12, 28), Color(0.05, 0.045, 0.055, 0.97))
	draw_rect(Rect2(-7, -27, 14, 3), Color(0.08, 0.07, 0.08, 1.0))
	draw_rect(Rect2(-5, -6, 10, 2), Color(0.12, 0.08, 0.08, 0.9))
	draw_rect(Rect2(-3, -1, 2, 7), Color(0.04, 0.03, 0.04, 0.85))
	draw_rect(Rect2(2, -1, 2, 10), Color(0.04, 0.03, 0.04, 0.85))
