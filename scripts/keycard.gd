extends Node2D
## Level keycard pickup. Blinks so it is findable in the dark.

var level := 1
var t := 0.0

func setup(data: Dictionary) -> void:
	level = int(data.get("level", 1))

func _process(delta: float) -> void:
	t += delta
	queue_redraw()

func _draw() -> void:
	var a := 0.55 + 0.45 * absf(sin(t * 2.2))
	var body := Color("c99a3f") if level == 1 else Color("d04848")
	var edge := Color("f0c76b") if level == 1 else Color("ff8a7a")
	draw_circle(Vector2.ZERO, 1.0 + a * 5.0, Color(body.r, body.g, body.b, 0.10 * a))
	draw_rect(Rect2(-4, -6, 8, 12), body)
	draw_rect(Rect2(-4, -6, 8, 3), edge)
	draw_rect(Rect2(-2, -1, 4, 3), Color(0.10, 0.11, 0.13))
	draw_rect(Rect2(-4, 5, 8, 1), Color(0.08, 0.09, 0.10))
