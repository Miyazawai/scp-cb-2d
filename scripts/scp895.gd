extends Node2D
## SCP-895 — safe only through the monitor room. Looking at it directly inverts you.

const CONTAMINE_SECS := 3.0

var player: CharacterBody2D = null
var active := true
var hold := false
var safe_rect := Rect2()

func setup(p: CharacterBody2D, safe: Rect2) -> void:
	player = p
	safe_rect = safe

func get_seen() -> int:
	return 0

func _process(_delta: float) -> void:
	if player == null or player.freeze or hold or not active:
		return
	if safe_rect.has_point(player.global_position):
		return
	if player.can_see(global_position):
		player.contaminate(CONTAMINE_SECS)
	queue_redraw()

func _draw() -> void:
	draw_rect(Rect2(-7, -10, 14, 20), Color(0.10, 0.02, 0.02, 0.95))
	draw_rect(Rect2(-7, -10, 14, 3), Color(0.55, 0.10, 0.10, 0.9))
	draw_rect(Rect2(-3, -4, 6, 2), Color(0.70, 0.15, 0.15, 0.85))
	draw_rect(Rect2(-3, 2, 6, 2), Color(0.70, 0.15, 0.15, 0.85))
