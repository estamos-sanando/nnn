"""Render cinematic shots from all 3 cameras for visual verification."""
import bpy, os, time

os.makedirs(r'd:\jeugosnacho\renders', exist_ok=True)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = 1280
sc.render.resolution_y = 720
sc.render.resolution_percentage = 100
sc.eevee.taa_render_samples = 24
sc.eevee.use_raytracing = True
sc.eevee.volumetric_tile_size = '4'
sc.eevee.volumetric_samples = 48
sc.render.image_settings.file_format = 'PNG'

shots = [
    ('CAM_Principal', r'd:\jeugosnacho\renders\shot1_cam_principal.png'),
    ('CAM_Tailgate_Hero', r'd:\jeugosnacho\renders\shot2_cautivo_hero.png'),
    ('CAM_Interior_Narrativa', r'd:\jeugosnacho\renders\shot3_interior_caja.png')
]

for cam_name, out_path in shots:
    t0 = time.time()
    cam_obj = bpy.data.objects.get(cam_name)
    if cam_obj:
        sc.camera = cam_obj
        sc.render.filepath = out_path
        bpy.ops.render.render(write_still=True)
        print("RENDERED:", cam_name, "in", round(time.time() - t0, 1), "s ->", out_path)

print("ALL_SHOTS_COMPLETED")

