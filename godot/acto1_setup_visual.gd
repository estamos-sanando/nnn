# ==============================================================================
# ACTO I: EL TRASLADO / CAMIÓN MILITAR (1976)
# Script de Configuración Visual, Iluminación y Shaders PBR (Godot 4.x)
# Rol: Technical Artist & Lead Graphics Programmer
# ==============================================================================
# Este script interviene EXCLUSIVAMENTE sobre la calidad visual, la iluminación,
# el WorldEnvironment y los materiales PBR, sin alterar nodos de gameplay,
# colisiones ni mecánicas existentes.
# ==============================================================================

extends Node3D

@export_group("Entorno y Cielo")
@export var hdri_texture: Texture2D ## Asignar moonlit_night.hdr o equivalente
@export var sky_rotation_deg: float = 45.0

@export_group("Iluminación Cinemática")
@export var moon_color: Color = Color("#8faac9")
@export var moon_energy: float = 0.38
@export var flashlight_color: Color = Color("#c99a4e")
@export var flashlight_energy: float = 9.5

func _ready() -> void:
	setup_world_environment()
	setup_moonlight()
	setup_flashlight()
	calibrate_pbr_materials()

# ------------------------------------------------------------------------------
# 1. WorldEnvironment & Volumetric Fog
# ------------------------------------------------------------------------------
func setup_world_environment() -> void:
	var world_env: WorldEnvironment = get_node_or_null("WorldEnvironment")
	if not world_env:
		world_env = WorldEnvironment.new()
		world_env.name = "WorldEnvironment"
		add_child(world_env)
	
	var env: Environment = world_env.environment
	if not env:
		env = Environment.new()
		world_env.environment = env
	
	# Modo de cielo HDRI
	env.background_mode = Environment.BG_SKY
	var sky: Sky = Sky.new()
	var sky_mat: PanoramaSkyMaterial = PanoramaSkyMaterial.new()
	if hdri_texture:
		sky_mat.panorama = hdri_texture
	sky_mat.filter = true
	sky.sky_material = sky_mat
	env.sky = sky
	env.sky_rotation = Vector3(0, deg_to_rad(sky_rotation_deg), 0)
	
	# Luz ambiental sutil para penumbra testimonial
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_sky_contribution = 0.35
	env.ambient_light_color = Color("#0a0e14")
	
	# Niebla volumétrica baja a ras de suelo (#0a0d12)
	env.volumetric_fog_enabled = true
	env.volumetric_fog_density = 0.024
	env.volumetric_fog_albedo = Color("#0a0d12")
	env.volumetric_fog_emission = Color("#06080b")
	env.volumetric_fog_emission_energy = 0.1
	env.volumetric_fog_length = 80.0
	env.volumetric_fog_ambient_inject = 0.15
	
	# Ambient Occlusion (SSAO) para contacto de figuras y pliegues
	env.ssao_enabled = true
	env.ssao_radius = 1.3
	env.ssao_intensity = 2.2
	env.ssao_power = 1.5
	env.ssao_detail = 0.5
	
	# Tonemapper cinematográfico ACES
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.tonemap_exposure = 1.15
	
	# Glow / Bloom sutil para filamentos y luces lejanas
	env.glow_enabled = true
	env.glow_intensity = 0.35
	env.glow_bloom = 0.20
	env.glow_blend_mode = Environment.GLOW_BLEND_MODE_SOFTLIGHT
	
	# Color Grading testimonial (desaturación y contraste)
	env.adjustment_enabled = true
	env.adjustment_saturation = 0.84
	env.adjustment_contrast = 1.08

# ------------------------------------------------------------------------------
# 2. Luz de Luna (DirectionalLight3D)
# ------------------------------------------------------------------------------
func setup_moonlight() -> void:
	var moon: DirectionalLight3D = get_node_or_null("DirectionalLight3D")
	if not moon:
		moon = DirectionalLight3D.new()
		moon.name = "DirectionalLight3D"
		add_child(moon)
	
	moon.light_color = moon_color
	moon.light_energy = moon_energy
	moon.rotation_degrees = Vector3(-48.0, 35.0, 0.0)
	
	# Sombras suaves filtradas (PCF)
	moon.shadow_enabled = true
	moon.shadow_bias = 0.002
	moon.shadow_blur = 1.8

# ------------------------------------------------------------------------------
# 3. Linterna Militar en L en la Compuerta (SpotLight3D)
# ------------------------------------------------------------------------------
func setup_flashlight() -> void:
	var spot: SpotLight3D = get_node_or_null("SpotLight_Linterna")
	if not spot:
		spot = SpotLight3D.new()
		spot.name = "SpotLight_Linterna"
		add_child(spot)
	
	spot.light_color = flashlight_color
	spot.light_energy = flashlight_energy
	spot.spot_range = 9.5
	spot.spot_angle = 34.0
	spot.spot_angle_attenuation = 1.8
	# Atenuación física cuadrática real
	spot.spot_attenuation = 2.0
	spot.shadow_enabled = true
	spot.shadow_bias = 0.003
	spot.position = Vector3(0.68, 1.34, 2.78)

# ------------------------------------------------------------------------------
# 4. Calibración de Materiales PBR en Mallas Existentes
# ------------------------------------------------------------------------------
func calibrate_pbr_materials() -> void:
	var meshes: Array[Node] = find_children("*", "MeshInstance3D", true)
	for m_node in meshes:
		var mi := m_node as MeshInstance3D
		if not mi or not mi.mesh:
			continue
		
		for surface_idx in range(mi.mesh.get_surface_count()):
			var mat = mi.get_surface_override_material(surface_idx)
			if not mat:
				mat = mi.mesh.surface_get_material(surface_idx)
			
			if mat is StandardMaterial3D:
				var m_name: String = mat.resource_name
				var node_name: String = mi.name
				
				# A. Capuchas de arpillera (Burlap)
				if m_name.contains("Arpillera") or m_name.contains("Capucha") or node_name.contains("Capucha"):
					mat.roughness = 0.98
					mat.metallic = 0.0
					mat.albedo_color = Color("#4a3b2b")
				
				# B. Caja y tablones de madera
				elif m_name.contains("Madera") or m_name.contains("Tablon") or node_name.contains("Tablon"):
					mat.roughness = 0.86
					mat.metallic = 0.04
					mat.albedo_color = Color("#383125")
				
				# C. Chasis, herrajes y parantes de hierro oxidado
				elif m_name.contains("Herraje") or m_name.contains("Hierro") or m_name.contains("Pintura_Oliva") or node_name.contains("Chasis"):
					mat.roughness = 0.65
					mat.metallic = 0.72
					mat.albedo_color = Color("#2e3623")
				
				# D. Barro y camino de tierra húmedo con charcos reflectantes
				elif m_name.contains("Terreno") or m_name.contains("Barro") or node_name.contains("Terreno"):
					mat.roughness = 0.70
					mat.metallic = 0.06
					mat.albedo_color = Color("#1c1813")
				
				# E. Toldo de lona
				elif m_name.contains("Lona") or node_name.contains("Toldo"):
					mat.roughness = 0.92
					mat.metallic = 0.0
					mat.albedo_color = Color("#3d382c")
