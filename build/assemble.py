"""Ensamblado final de 'La Escena 1: El Traslado', configuracion de camaras narrativas,
limpieza de datablocks, guardado de escena .blend y exportacion GLB lista para motor de juego.
"""
import bpy, math
from mathutils import Vector
from common import coll

def setup_cameras():
    cn = 'Camaras'
    c_coll = coll(cn)
    
    # 1. Camara Principal (Cinematica Master - Plano General Medio)
    # Encuadra camion 3/4 trasero, compuerta abierta con el cautivo central,
    # camino con huellas de barro y niebla rasante, bosque y destello militar distante.
    cam1 = bpy.data.cameras.get('CAM_Principal') or bpy.data.cameras.new('CAM_Principal')
    cam1.lens = 32
    cam1.sensor_width = 36
    cam1.clip_end = 450
    cam1.dof.use_dof = True
    cam1.dof.aperture_fstop = 3.5
    o1 = bpy.data.objects.get('CAM_Principal')
    if o1 is None:
        o1 = bpy.data.objects.new('CAM_Principal', cam1)
        c_coll.objects.link(o1)
    o1.location = (2.85, -8.6, 1.48)
    tgt1 = Vector((0.02, -2.90, 1.35))
    d1 = tgt1 - o1.location
    o1.rotation_euler = d1.to_track_quat('-Z', 'Y').to_euler()
    cam1.dof.focus_distance = d1.length

    # 2. Camara Hero / Cautivo Central (Encuadre Cinematografico Medio Completo)
    # Muestra cabeza encapuchada con saco de arpillera, soga al cuello, camisa arrugada,
    # manos atadas a la espalda con soga gruesa, compuerta, zapatilla Flecha y linterna.
    cam2 = bpy.data.cameras.get('CAM_Tailgate_Hero') or bpy.data.cameras.new('CAM_Tailgate_Hero')
    cam2.lens = 40
    cam2.sensor_width = 36
    cam2.clip_end = 150
    cam2.dof.use_dof = True
    cam2.dof.aperture_fstop = 2.4
    o2 = bpy.data.objects.get('CAM_Tailgate_Hero')
    if o2 is None:
        o2 = bpy.data.objects.new('CAM_Tailgate_Hero', cam2)
        c_coll.objects.link(o2)
    o2.location = (0.85, -5.45, 1.62)
    tgt2 = Vector((0.02, -2.85, 1.55))
    d2 = tgt2 - o2.location
    o2.rotation_euler = d2.to_track_quat('-Z', 'Y').to_euler()
    cam2.dof.focus_distance = d2.length

    # 3. Camara Interior / Perspectiva Subjetiva Narrativa (Claustrofobia en la caja)
    # Gran angular desde el fondo mirando hacia los cautivos, radio militar, cajones y el exterior.
    cam3 = bpy.data.cameras.get('CAM_Interior_Narrativa') or bpy.data.cameras.new('CAM_Interior_Narrativa')
    cam3.lens = 20
    cam3.sensor_width = 36
    cam3.clip_end = 200
    cam3.dof.use_dof = True
    cam3.dof.aperture_fstop = 2.8
    o3 = bpy.data.objects.get('CAM_Interior_Narrativa')
    if o3 is None:
        o3 = bpy.data.objects.new('CAM_Interior_Narrativa', cam3)
        c_coll.objects.link(o3)
    o3.location = (-0.68, 0.40, 2.05)
    tgt3 = Vector((0.05, -1.90, 1.45))
    d3 = tgt3 - o3.location
    o3.rotation_euler = d3.to_track_quat('-Z', 'Y').to_euler()
    cam3.dof.focus_distance = d3.length

    # 4. Camara de Inspeccion 3D (Props Clave: Zapatilla Flecha, Libreta y Linterna en L)
    cam4 = bpy.data.cameras.get('CAM_Inspeccion_Props') or bpy.data.cameras.new('CAM_Inspeccion_Props')
    cam4.lens = 42
    cam4.sensor_width = 36
    cam4.clip_end = 50
    cam4.dof.use_dof = True
    cam4.dof.aperture_fstop = 2.8
    o4 = bpy.data.objects.get('CAM_Inspeccion_Props')
    if o4 is None:
        o4 = bpy.data.objects.new('CAM_Inspeccion_Props', cam4)
        c_coll.objects.link(o4)
    o4.location = (0.58, -3.42, 1.65)
    tgt4 = Vector((0.42, -2.60, 1.26))
    d4 = tgt4 - o4.location
    o4.rotation_euler = d4.to_track_quat('-Z', 'Y').to_euler()
    cam4.dof.focus_distance = d4.length

    bpy.context.scene.camera = o1
    return [o1, o2, o3, o4]

def cleanup_duplicate_lights():
    to_rem = [o for o in bpy.data.objects if o.name.endswith('.001') and 'LUZ_' in o.name]
    for o in to_rem:
        bpy.data.objects.remove(o, do_unlink=True)

def save_and_export():
    cleanup_duplicate_lights()
    setup_cameras()
    
    blend_path = r'd:\jeugosnacho\escena1_el_traslado.blend'
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print("SAVED_BLEND:", blend_path)
    
    # Exportar GLB optimizado para motores de juego (Unity, Unreal Engine, Godot, Web)
    glb_path = r'd:\jeugosnacho\escena1_el_traslado.glb'
    try:
        bpy.ops.export_scene.gltf(
            filepath=glb_path,
            export_format='GLB',
            use_selection=False,
            export_apply=False,
            export_cameras=True,
            export_lights=True,
            export_materials='EXPORT',
            export_image_format='AUTO'
        )
        print("EXPORTED_GLB:", glb_path)
    except Exception as e:
        print("GLB_EXPORT_ERROR:", e)

def build():
    save_and_export()
    return 'ok'
