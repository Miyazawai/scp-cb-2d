extends Node2D
## SCP-966 — invisible unless you have night vision. Only the sound tells you.

const SPEED := 26.0
const KILL_DIST := 9.0

var player: CharacterBody2D = null
var active := false
var hold := false

func setup(p: CharacterBody2D) -> void:
	player = p

func get_seen() -> int:
	return 0

func _process(delta: float) -> void:
	if player == null or player.freeze or hold or not active:
		return
	var d := player.global_position - global_position
	if d.length() > KILL_DIST:
		global_position += d.normalized() * SPEED * delta
	if global_position.distance_to(player.global_position) < KILL_DIST:
		player.die()
	queue_redraw()

func _draw() -> void:
	if player == null or not player.has_nvg:
		return
	draw_circle(Vector2(0, -8), 16.0, Color(0.10, 0.20, 0.12, 0.28))
	draw_rect(Rect2(-5, -22, 10, 24), Color(0.16, 0.30, 0.20, 0.92))
	draw_rect(Rect2(-4, -26, 8, 5), Color(0.20, 0.36, 0.24, 0.95))
	draw_rect(Rect2(-6, -12, 12, 2), Color(0.36, 0.62, 0.40, 0.9))
