extends Node2D
## SCP-372 — always behind you. It drifts to stay out of your cone; turn fast
## enough and you catch it. Catch it three times and it stops hiding.

const BEHIND_DIST := 76.0
const DRIFT := 2.4
const CHASE_SPEED := 62.0
const KILL_DIST := 10.0
const SEEN_LIMIT := 3

var player: CharacterBody2D = null
var active := true
var hold := false
var seen := 0
var chasing := false

func setup(p: CharacterBody2D) -> void:
	player = p

func get_seen() -> int:
	return seen

func _process(delta: float) -> void:
	if player == null or player.freeze or hold or not active:
		return
	if not chasing:
		if player.can_see(global_position):
			seen += 1
			global_position = player.global_position - player.facing * BEHIND_DIST * 1.8
			if seen >= SEEN_LIMIT:
				chasing = true
		else:
			var want: Vector2 = player.global_position - player.facing * BEHIND_DIST
			global_position = global_position.lerp(want, clampf(DRIFT * delta, 0.0, 1.0))
	else:
		var d := player.global_position - global_position
		if d.length() > KILL_DIST:
			global_position += d.normalized() * CHASE_SPEED * delta
		if global_position.distance_to(player.global_position) < KILL_DIST:
			player.die()
	queue_redraw()

func _draw() -> void:
	draw_circle(Vector2(0, -6), 14.0, Color(0.06, 0.05, 0.05, 0.35))
	draw_rect(Rect2(-4, -18, 8, 20), Color(0.12, 0.10, 0.10, 0.95))
	draw_rect(Rect2(-5, -21, 10, 4), Color(0.16, 0.13, 0.13, 0.95))
	draw_rect(Rect2(-6, -6, 2, 8), Color(0.10, 0.08, 0.08, 0.9))
	draw_rect(Rect2(4, -6, 2, 8), Color(0.10, 0.08, 0.08, 0.9))
