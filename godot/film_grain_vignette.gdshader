// ==============================================================================
// Shader Post-Procesado Cinematográfico de Época 1970s (Godot 4.x)
// Film Grain Monocromático, Color Grading Testimonial y Vignette Óptico
// ==============================================================================
shader_type canvas_item;

uniform sampler2D screen_texture : hint_screen_texture, filter_linear_mipmap;
uniform float film_grain_strength : hint_range(0.0, 0.2) = 0.055;
uniform float vignette_intensity : hint_range(0.0, 1.0) = 0.75;
uniform float desaturation_amount : hint_range(0.0, 1.0) = 0.16;

float hash(vec2 p) {
	p = fract(p * vec2(123.34, 456.21));
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}

void fragment() {
	vec4 source = texture(screen_texture, SCREEN_UV);
	vec3 col = source.rgb;

	// 1. Color Grading Testimonial 70s
	float lum = dot(col, vec3(0.299, 0.587, 0.114));
	col = mix(col, vec3(lum), desaturation_amount);

	// Negros ligeramente lavados con tinte frio petroleo (#141b1f)
	vec3 slate_black = vec3(0.045, 0.062, 0.078);
	col += slate_black * (1.0 - smoothstep(0.0, 0.38, lum));

	// Medios tonos ligeramente teñidos hacia verde oliva (#1f2824)
	float mid_mask = smoothstep(0.06, 0.32, lum) * (1.0 - smoothstep(0.38, 0.82, lum));
	col += vec3(-0.012, 0.022, 0.008) * mid_mask;

	// 2. Granulado Fílmico Monocromático 16mm/35mm
	vec2 grain_coord = SCREEN_UV * (1.0 / SCREEN_PIXEL_SIZE) * 0.8 + vec2(TIME * 43.1, TIME * 67.9);
	float grain = hash(floor(grain_coord));
	float grain_weight = (1.0 - smoothstep(0.08, 0.92, lum)) * film_grain_strength;
	col += (grain - 0.5) * grain_weight;

	// 3. Vignette (encierro bajo la lona)
	vec2 uv = (SCREEN_UV - 0.5) * vec2(SCREEN_PIXEL_SIZE.y / SCREEN_PIXEL_SIZE.x, 1.0);
	float dist = length(uv);
	float vig = smoothstep(0.94, 0.38, dist);
	col *= mix(vec3(0.04, 0.05, 0.07), vec3(1.0), mix(1.0, vig, vignette_intensity));

	COLOR = vec4(col, source.a);
}
