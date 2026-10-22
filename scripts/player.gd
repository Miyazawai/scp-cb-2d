extends CharacterBody2D
## D-9341. No combat: movement, flashlight, blink, battery.

const Assets := preload("res://scripts/assets.gd")

signal died()

const WALK := 44.0
const RUN := 72.0
const FLASH_RANGE := 104.0
const FLASH_HALF_ANGLE := 26.0
const BLINK_INTERVAL := 20.0
const BLINK_TIME := 0.35
const BATTERY_DRAIN := 0.32
const OBSERVE_RANGE := 150.0
const STAMINA_MAX := 100.0
const STAMINA_DRAIN := 32.0
const STAMINA_REGEN := 24.0

var facing := Vector2.RIGHT
var move_dir := Vector2.DOWN
var eyes_open := true
var blink_timer := BLINK_INTERVAL
var blink_left := 0.0
var battery := 100.0
var has_nvg := false
var contamin_t := 0.0
var stamina := 100.0
var stamina_delay := 0.0
var light_on := true
var card_level := 0
var freeze := false
var use_mouse_aim := true
var lights: Array = []

var cone_light: PointLight2D = null
var glow_light: PointLight2D = null
var audio: Node = null

var _sprite: Sprite2D = null
var _frames := {}
var _anim := 0.0
var _step_t := 0.0
var _space_prev := false
var _f_prev := false

func _ready() -> void:
	_build_lights()
	_load_sprites()

func reset_state() -> void:
	battery = 100.0
	stamina = STAMINA_MAX
	stamina_delay = 0.0
	blink_timer = BLINK_INTERVAL
	blink_left = 0.0
	contamin_t = 0.0
	eyes_open = true
	light_on = true
	freeze = false
	velocity = Vector2.ZERO

# ---------------------------------------------------------------- visuals

func _load_sprites() -> void:
	var dirs := ["down", "up", "left", "right"]
	var found := false
	for d in dirs:
		var arr := []
		for i in 4:
			var t := Assets.tex("chars/player_%s_%d.png" % [d, i])
			if t == null:
				t = Assets.tex("chars/player_%s_0.png" % d)
			arr.append(t)
			if t != null:
				found = true
		_frames[d] = arr
	if not found:
		return
	_sprite = Sprite2D.new()
	_sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_sprite.centered = true
	_sprite.offset = Vector2(0, -12)
	_sprite.z_index = 3
	_sprite.texture = _frames["down"][0]
	add_child(_sprite)

func _build_lights() -> void:
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
	glow_light.texture_scale = 0.8
	glow_light.energy = 0.30
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

# ---------------------------------------------------------------- loop

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
	if contamin_t > 0.0:
		dir = -dir
	dir = dir.normalized()
	var want_sprint := Input.is_physical_key_pressed(KEY_SHIFT) and dir != Vector2.ZERO
	var sprint := want_sprint and stamina > 1.0
	velocity = dir * (RUN if sprint else WALK)
	move_and_slide()

	if want_sprint and sprint:
		stamina = maxf(0.0, stamina - STAMINA_DRAIN * delta)
		stamina_delay = 0.65
	elif stamina_delay > 0.0:
		stamina_delay -= delta
	else:
		stamina = minf(STAMINA_MAX, stamina + STAMINA_REGEN * delta)

	if dir != Vector2.ZERO:
		move_dir = dir

	# footsteps
	if dir != Vector2.ZERO:
		_step_t -= delta
		if _step_t <= 0.0:
			_step_t = 0.27 if sprint else 0.36
			if audio:
				audio.play("step_%d.wav" % randi_range(1, 3), -12.0, randf_range(0.94, 1.06))

func _process(delta: float) -> void:
	if freeze:
		_update_sprite(delta, false)
		return

	if use_mouse_aim:
		var to_mouse := get_global_mouse_position() - global_position
		if to_mouse.length() > 2.0:
			facing = facing.lerp(to_mouse.normalized(), clampf(delta * 14.0, 0.0, 1.0)).normalized()

	var f := Input.is_physical_key_pressed(KEY_F)
	if f and not _f_prev:
		if battery > 0.0:
			light_on = not light_on
			if audio:
				audio.play("flashlight_click.wav", -6.0)
	_f_prev = f

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

	if contamin_t > 0.0:
		contamin_t = maxf(0.0, contamin_t - delta)

	if light_on:
		battery = maxf(0.0, battery - BATTERY_DRAIN * delta)
		stamina = minf(STAMINA_MAX, stamina + STAMINA_REGEN * 0.4 * delta)
		if battery <= 0.0:
			light_on = false

	var lit := light_on and battery > 0.0
	cone_light.rotation = facing.angle()
	cone_light.enabled = lit and eyes_open
	glow_light.enabled = lit and eyes_open
	var low := battery < 25.0 and battery > 0.0
	cone_light.energy = 0.55 if (lit and low and randf() < 0.08) else 1.35

	_update_sprite(delta, velocity.length() > 1.0)
	queue_redraw()

func _update_sprite(delta: float, moving: bool) -> void:
	if _sprite == null:
		return
	var d := "down"
	if absf(move_dir.x) > absf(move_dir.y):
		d = "right" if move_dir.x > 0 else "left"
	else:
		d = "down" if move_dir.y > 0 else "up"
	var arr: Array = _frames.get(d, [])
	var idx := 0
	if moving:
		_anim += delta
		idx = int(_anim * 7.0) % 4
	else:
		_anim = 0.0
		idx = 0
	if arr.size() > 0 and arr[idx % arr.size()] != null:
		_sprite.texture = arr[idx % arr.size()]

func _do_blink() -> void:
	blink_timer = BLINK_INTERVAL
	blink_left = BLINK_TIME
	eyes_open = false
	if audio:
		audio.play("blink.wav", -10.0)

func blink_ratio() -> float:
	return clampf(blink_timer / BLINK_INTERVAL, 0.0, 1.0)

func stamina_ratio() -> float:
	return clampf(stamina / STAMINA_MAX, 0.0, 1.0)

func battery_ratio() -> float:
	return clampf(battery / 100.0, 0.0, 1.0)

func _is_lit(p: Vector2) -> bool:
	for l in lights:
		if p.distance_to(l["pos"]) < float(l["radius"]):
			return true
	return false

func can_see(target: Vector2) -> bool:
	# Looking at it means pointing the beam at it. Ambient light alone does not
	# count: being in a lit room must not make you safe with your back turned.
	if freeze or not eyes_open:
		return false
	if not light_on or battery <= 0.0:
		return false
	var to_target := target - global_position
	var dist := to_target.length()
	if dist > FLASH_RANGE:
		return false
	if absf(angle_difference(facing.angle(), to_target.angle())) > deg_to_rad(FLASH_HALF_ANGLE):
		return false
	var space := get_world_2d().direct_space_state
	var q := PhysicsRayQueryParameters2D.create(global_position, target, 1)
	return space.intersect_ray(q).is_empty()

func contaminate(secs: float) -> void:
	if contamin_t <= 0.0:
		contamin_t = secs

func die() -> void:
	if freeze:
		return
	freeze = true
	died.emit()

func _draw() -> void:
	if _sprite != null:
		return
	draw_rect(Rect2(-5, -6, 10, 12), Color("c4692a"))
	draw_rect(Rect2(-5, -6, 10, 3), Color("e08a3c"))
	draw_rect(Rect2(-3, -10, 6, 5), Color("2b2622"))
	var tip := facing * 9.0
	draw_circle(tip, 1.2, Color("ffe4b0"))
