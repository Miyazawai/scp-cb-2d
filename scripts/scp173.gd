extends Node2D
## SCP-173: moves only while the player cannot see it.
## Seen == inside the flashlight cone AND lit AND eyes open (see player.can_see).

const MOVE_SPEED := 44.0
const KILL_DIST := 8.5

var player: CharacterBody2D = null
var _idle_time := 0.0
var _shake := 0.0

func setup(p: CharacterBody2D) -> void:
	player = p

func _process(delta: float) -> void:
	if player == null or player.freeze:
		return
	var seen: bool = player.can_see(global_position)
	if not seen:
		var to_player: Vector2 = player.global_position - global_position
		var dist := to_player.length()
		if dist > 0.001:
			global_position += to_player / dist * MOVE_SPEED * delta
		_idle_time = 0.0
	else:
		_idle_time += delta

	var d := global_position.distance_to(player.global_position)
	if d < KILL_DIST:
		player.die()

	_shake = 0.0 if seen else _shake + delta
	queue_redraw()

func _draw() -> void:
	# concrete statue: blocky, no face
	var base := Color("b7b0a2")
	draw_rect(Rect2(-4, 1, 8, 7), base)
	draw_rect(Rect2(-3, -7, 6, 8), base.lightened(0.06))
	draw_rect(Rect2(-8, 2, 4, 6), base.darkened(0.08))
	draw_rect(Rect2(4, 2, 4, 6), base.darkened(0.08))
	draw_rect(Rect2(-4, 8, 3, 3), base.darkened(0.14))
	draw_rect(Rect2(1, 8, 3, 3), base.darkened(0.14))
	draw_rect(Rect2(-2, -4, 4, 1), base.darkened(0.3))
