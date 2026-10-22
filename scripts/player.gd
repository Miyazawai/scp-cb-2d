extends CharacterBody2D
## D-9341. No combat: movement, flashlight, blink, battery.

signal died()

const WALK := 46.0
const RUN := 74.0
const FLASH_RANGE := 104.0
const FLASH_HALF_ANGLE := 26.0
const BLINK_INTERVAL := 22.0
const BLINK_TIME := 0.35
const BATTERY_DRAIN := 0.45

var facing := Vector2.RIGHT
var eyes_open := true
var blink_timer := BLINK_INTERVAL
var blink_left := 0.0
var battery := 100.0
var light_on := true
var card_level := 0
var freeze := false
var use_mouse_aim := true

var cone_light: PointLight2D = null
var glow_light: PointLight2D = null
var lights: Array = []
var _space_prev := false

const OBSERVE_RANGE := 150.0

func _ready() -> void:
	cone_light = PointLight2D.new()
	cone_light.texture = _cone_texture(192, FLASH_HALF_ANGLE)
	cone_light.texture_scale = (FLASH_RANGE * 2.0) / 192.0
	cone_light.energy = 1.35
	cone_light.color = Color(1.0, 0.95, 0.86)
	cone_light.shadow_enabled = true
	cone_light.shadow_filter = Light2D.SHADOW_FILTER_PCF5
	cone_light.z_index = 5
	add_child(cone_light)

	glow_light = PointLight2D.new()
	var glow_tex := Image.create(64, 64, false, Image.FORMAT_RGBA8)
	for y in 64:
		for x in 64:
			var d := Vector2(x + 0.5 - 32, y + 0.5 - 32).length() / 32.0
			var a := 0.0
			if d <= 1.0:
				a = pow(clampf(1.0 - d, 0.0, 1.0), 2.0)
			glow_tex.set_pixel(x, y, Color(1, 1, 1, a))
	glow_light.texture = ImageTexture.create_from_image(glow_tex)
	glow_light.texture_scale = 0.9
	glow_light.energy = 0.32
	glow_light.color = Color(0.85, 0.88, 1.0)
	glow_light.z_index = 5
	add_child(glow_light)

func _cone_texture(px: int, half_angle_deg: float) -> ImageTexture:
	var img := Image.create(px, px, false, Image.FORMAT_RGBA8)
	var c := px * 0.5
	var half := deg_to_rad(half_angle_deg)
	for y in px:
		for x in px:
			var p := Vector2(x + 0.5 - c, y + 0.5 - c)
			var d := p.length() / c
			var ang := absf(p.angle())
			var a := 0.0
			if d <= 1.0 and ang <= half:
				var falloff := clampf(1.0 - pow(d, 1.5), 0.0, 1.0)
				var edge := clampf(1.0 - pow(ang / half, 3.0), 0.0, 1.0)
				a = falloff * edge
			img.set_pixel(x, y, Color(1, 1, 1, a))
	return ImageTexture.create_from_image(img)

func _physics_process(delta: float) -> void:
	if freeze:
		velocity = Vector2.ZERO
		move_and_slide()
		return
	var dir := Vector2.ZERO
	if Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_UP):
		dir.y -= 1.0
	if Input.is_physical_key_pressed(KEY_S) or Input.is_physical_key_pressed(KEY_DOWN):
		dir.y += 1.0
	if Input.is_physical_key_pressed(KEY_A) or Input.is_physical_key_pressed(KEY_LEFT):
		dir.x -= 1.0
	if Input.is_physical_key_pressed(KEY_D) or Input.is_physical_key_pressed(KEY_RIGHT):
		dir.x += 1.0
	dir = dir.normalized()
	var sprint := Input.is_physical_key_pressed(KEY_SHIFT) and battery > 0.0
	velocity = dir * (RUN if sprint else WALK)
	move_and_slide()

func _process(delta: float) -> void:
	if freeze:
		return

	if use_mouse_aim:
		var to_mouse := get_global_mouse_position() - global_position
		if to_mouse.length() > 2.0:
			facing = facing.lerp(to_mouse.normalized(), clampf(delta * 14.0, 0.0, 1.0)).normalized()

	if Input.is_physical_key_pressed(KEY_F) and not _f_prev:
		if battery > 0.0:
			light_on = not light_on
	_f_prev = Input.is_physical_key_pressed(KEY_F)

	var space := Input.is_physical_key_pressed(KEY_SPACE)
	if space and not _space_prev and blink_left <= 0.0 and blink_timer > 2.5:
		_do_blink()
	_space_prev = space

	blink_timer -= delta
	if blink_timer <= 0.0 and blink_left <= 0.0:
		_do_blink()

	if blink_left > 0.0:
		blink_left -= delta
		eyes_open = false
		if blink_left <= 0.0:
			eyes_open = true

	if light_on:
		battery = maxf(0.0, battery - BATTERY_DRAIN * delta)
		if battery <= 0.0:
			light_on = false

	var lit := light_on and battery > 0.0
	cone_light.rotation = facing.angle()
	cone_light.enabled = lit and eyes_open
	glow_light.enabled = lit and eyes_open
	var low := battery < 25.0 and battery > 0.0
	if lit and low and randf() < 0.08:
		cone_light.energy = 0.5
	else:
		cone_light.energy = 1.35

	queue_redraw()

func _do_blink() -> void:
	blink_timer = BLINK_INTERVAL
	blink_left = BLINK_TIME
	eyes_open = false

func blink_ratio() -> float:
	return clampf(blink_timer / BLINK_INTERVAL, 0.0, 1.0)

func battery_ratio() -> float:
	return clampf(battery / 100.0, 0.0, 1.0)

func _is_lit(p: Vector2) -> bool:
	for l in lights:
		if p.distance_to(l["pos"]) < float(l["radius"]):
			return true
	return false

func can_see(target: Vector2) -> bool:
	if freeze:
		return false
	if not eyes_open:
		return false
	var to_target := target - global_position
	var dist := to_target.length()
	if dist > OBSERVE_RANGE:
		return false

	var in_beam := false
	if light_on and battery > 0.0 and dist <= FLASH_RANGE:
		if absf(angle_difference(facing.angle(), to_target.angle())) <= deg_to_rad(FLASH_HALF_ANGLE):
			in_beam = true

	# "observed" must match what the player can actually SEE on screen:
	# inside the flashlight cone, or standing in the light of a ceiling lamp.
	if not in_beam and not _is_lit(target):
		return false

	var space := get_world_2d().direct_space_state
	var q := PhysicsRayQueryParameters2D.create(global_position, target, 1)
	var hit := space.intersect_ray(q)
	return hit.is_empty()

func die() -> void:
	if freeze:
		return
	freeze = true
	died.emit()

var _f_prev := false

func _draw() -> void:
	# simple pixel D-class
	draw_rect(Rect2(-5, -6, 10, 12), Color("c4692a"))
	draw_rect(Rect2(-5, -6, 10, 3), Color("d97c3a"))
	draw_rect(Rect2(-3, -10, 6, 5), Color("2b2622"))
	draw_rect(Rect2(-3, -8, 6, 1), Color("b4a898"))
	var tip := facing * 9.0
	draw_circle(tip, 1.2, Color("ffe4b0"))
