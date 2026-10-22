extends Node
## Tiny audio front-end: a pool of players for one-shots, plus one ambience bed.

const Assets := preload("res://scripts/assets.gd")

var _pool: Array[AudioStreamPlayer] = []
var _next := 0
var _amb: AudioStreamPlayer = null
var _heart: AudioStreamPlayer = null

func _ready() -> void:
	for i in 8:
		var p := AudioStreamPlayer.new()
		p.bus = "Master"
		add_child(p)
		_pool.append(p)

func play(rel: String, volume_db: float = 0.0, pitch: float = 1.0) -> void:
	var s := Assets.snd(rel)
	if s == null:
		return
	var p := _pool[_next]
	_next = (_next + 1) % _pool.size()
	p.stream = s
	p.volume_db = volume_db
	p.pitch_scale = pitch
	p.play()

func play_at(rel: String, pos: Vector2, volume_db: float = 0.0) -> void:
	var s := Assets.snd(rel)
	if s == null:
		return
	var p := AudioStreamPlayer2D.new()
	p.stream = s
	p.volume_db = volume_db
	p.max_distance = 320.0
	p.position = pos
	get_tree().current_scene.add_child(p)
	p.play()
	p.finished.connect(p.queue_free)

func start_ambience(rel: String = "amb_loop.wav", volume_db: float = -10.0) -> void:
	if _amb:
		return
	var s := Assets.snd(rel)
	if s == null:
		return
	_amb = AudioStreamPlayer.new()
	_amb.stream = s
	_amb.volume_db = volume_db
	add_child(_amb)
	_amb.play()

func set_heartbeat(on: bool) -> void:
	if on:
		if _heart and _heart.playing:
			return
		var s := Assets.snd("heartbeat.wav")
		if s == null:
			return
		if _heart == null:
			_heart = AudioStreamPlayer.new()
			add_child(_heart)
		_heart.stream = s
		_heart.volume_db = -8.0
		_heart.play()
	elif _heart and _heart.playing:
		_heart.stop()
