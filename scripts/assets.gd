extends Node
## Central asset access. Everything degrades gracefully: if a PNG/WAV has not
## been generated yet, the caller gets null and falls back to procedural art.
## Use: const Assets := preload("res://scripts/assets.gd")

const ART := "res://assets/art/"
const SFX := "res://assets/audio/"

static var _tex_cache := {}
static var _snd_cache := {}

static func tex(rel: String) -> Texture2D:
	if _tex_cache.has(rel):
		return _tex_cache[rel]
	var path := ART + rel
	var t: Texture2D = null
	if ResourceLoader.exists(path):
		t = load(path)
	_tex_cache[rel] = t
	return t

static func snd(rel: String) -> AudioStream:
	if _snd_cache.has(rel):
		return _snd_cache[rel]
	var path := SFX + rel
	var s: AudioStream = null
	if ResourceLoader.exists(path):
		s = load(path)
	_snd_cache[rel] = s
	return s

static func has_art(rel: String) -> bool:
	return ResourceLoader.exists(ART + rel)

## A cached 1x1 white texture, handy for tinted quads.
static var _white: Texture2D = null
static func white() -> Texture2D:
	if _white == null:
		var img := Image.create(1, 1, false, Image.FORMAT_RGBA8)
		img.set_pixel(0, 0, Color.WHITE)
		_white = ImageTexture.create_from_image(img)
	return _white
