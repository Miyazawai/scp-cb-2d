extends Node2D
## SCP-049 — the plague doctor. It does not hunt. It walks between the bodies
## and turns them into patients, and the patients do the hunting.

const SPEED := 22.0
const CONVERT_DIST := 26.0

var player: CharacterBody2D = null
var corpses: Array = []
var active := true
var hold := false
var main: Node = null
var converted := 0
var _idx := 0

func setup(p: CharacterBody2D, corpse_points: Array, host: Node) -> void:
	player = p
	corpses = corpse_points
	main = host
	if corpses.size() > 0:
		global_position = corpses[0]

func _process(delta: float) -> void:
	if player == null or player.freeze or hold or not active:
		return
	if _idx >= corpses.size():
		queue_redraw()
		return
	var target: Vector2 = corpses[_idx]
	var d := target - global_position
	if d.length() > CONVERT_DIST:
		global_position += d.normalized() * SPEED * delta
	else:
		converted += 1
		if main and main.has_method("spawn_patient"):
			main.spawn_patient(target)
		corpses.remove_at(_idx)
	queue_redraw()

func get_seen() -> int:
	return converted

func _draw() -> void:
	# black coat, pale mask
	draw_circle(Vector2(0, -6), 15.0, Color(0.03, 0.03, 0.04, 0.35))
	draw_rect(Rect2(-6, -22, 12, 26), Color(0.07, 0.07, 0.09, 0.97))
	draw_rect(Rect2(-5, -27, 10, 6), Color(0.80, 0.78, 0.72, 1.0))
	draw_rect(Rect2(-2, -24, 4, 2), Color(0.10, 0.10, 0.10, 1.0))
	draw_rect(Rect2(-7, -4, 14, 2), Color(0.30, 0.28, 0.26, 1.0))
