extends Node2D
## A patient. Slow, visible, and it does not stop.

const SPEED := 30.0
const KILL_DIST := 9.0

var player: CharacterBody2D = null
var active := true
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
	draw_circle(Vector2(0, -6), 13.0, Color(0.05, 0.05, 0.06, 0.30))
	draw_rect(Rect2(-5, -18, 10, 20), Color(0.16, 0.16, 0.18, 0.96))
	draw_rect(Rect2(-4, -22, 8, 4), Color(0.74, 0.72, 0.66, 0.95))
	draw_rect(Rect2(-2, -20, 4, 2), Color(0.30, 0.05, 0.05, 1.0))
