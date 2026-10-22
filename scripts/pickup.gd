extends Node2D
## Ground pickup: keycard or spare battery. Pulses so it is findable in the dark.

var kind := "card"
var level := 1
var t := 0.0

func setup(data: Dictionary) -> void:
	kind = String(data.get("kind", "card"))
	level = int(data.get("level", 1))

func _process(delta: float) -> void:
	t += delta
	queue_redraw()

func _draw() -> void:
	var a := 0.55 + 0.45 * absf(sin(t * 2.2))
	if kind == "battery":
		draw_circle(Vector2.ZERO, 2.0 + a * 6.0, Color(0.75, 0.85, 0.45, 0.12 * a))
		draw_rect(Rect2(-4, -6, 8, 12), Color("2b3a33"))
		draw_rect(Rect2(-3, -5, 6, 10), Color("8fd08a"))
		draw_rect(Rect2(-2, -3, 4, 6), Color("d8f0a0"))
		draw_rect(Rect2(-1, -8, 2, 2), Color("9aa5ad"))
		draw_rect(Rect2(-4, 5, 8, 1), Color(0.08, 0.09, 0.10))
		return
	var body := Color("c99a3f") if level == 1 else Color("d04848")
	var edge := Color("f0c76b") if level == 1 else Color("ff8a7a")
	draw_circle(Vector2.ZERO, 1.0 + a * 5.0, Color(body.r, body.g, body.b, 0.10 * a))
	draw_rect(Rect2(-4, -6, 8, 12), body)
	draw_rect(Rect2(-4, -6, 8, 3), edge)
	draw_rect(Rect2(-2, -1, 4, 3), Color(0.10, 0.11, 0.13))
	draw_rect(Rect2(-4, 5, 8, 1), Color(0.08, 0.09, 0.10))
