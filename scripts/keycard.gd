extends Node2D
## Level 1 keycard pickup. Blinks slowly so it is findable in the dark.

var t := 0.0

func _process(delta: float) -> void:
	t += delta
	queue_redraw()

func _draw() -> void:
	var a := 0.55 + 0.45 * absf(sin(t * 2.2))
	draw_rect(Rect2(-4, -6, 8, 12), Color(0.85, 0.72, 0.35, 1.0))
	draw_rect(Rect2(-4, -6, 8, 3), Color(1.0, 0.9, 0.55, 1.0))
	draw_rect(Rect2(-2, -1, 4, 3), Color(0.15, 0.15, 0.18, 1.0))
	draw_circle(Vector2.ZERO, 1.0 + a * 3.0, Color(1.0, 0.85, 0.4, 0.10 * a))
