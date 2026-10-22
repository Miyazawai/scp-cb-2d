shader_type canvas_item;
// Cheap film grain + a very slight horizontal scanline. Pure shader, no textures.

uniform float grain_amount : hint_range(0.0, 0.35) = 0.022;
uniform float scanline_amount : hint_range(0.0, 0.3) = 0.03;
uniform vec2 viewport_size = vec2(480.0, 270.0);

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123);
}

void fragment() {
	vec2 px = floor(UV * viewport_size);
	float n = hash(px + vec2(TIME * 61.7, TIME * 37.3));
	float scan = step(0.5, fract(px.y * 0.5)) * scanline_amount;
	COLOR = vec4(vec3(0.45), grain_amount + scan);
}
