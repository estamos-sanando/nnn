"""Cielo nocturno, niebla volumetrica, luz de luna, camara y ajustes de render (EEVEE)."""
import bpy, math
from mathutils import Vector
from common import *

MOON_DIR = Vector((0.6, -0.45, 0.62)).normalized()
GLOW_DIR = Vector((-0.30, 0.95, 0.0)).normalized()   # hacia la instalacion militar


def build_world():
    w = bpy.data.worlds.get('Cielo_Nocturno') or bpy.data.worlds.new('Cielo_Nocturno')
    try:
        w.use_nodes = True
    except Exception:
        pass
    nt = w.node_tree
    nt.nodes.clear()
    N = nt.nodes
    L = nt.links.new
    out = N.new('ShaderNodeOutputWorld')
    bg = N.new('ShaderNodeBackground')
    L(bg.outputs['Background'], out.inputs['Surface'])

    tc = N.new('ShaderNodeTexCoord')
    vn = N.new('ShaderNodeVectorMath'); vn.operation = 'NORMALIZE'
    L(tc.outputs['Object'], vn.inputs[0])
    sep = N.new('ShaderNodeSeparateXYZ')
    L(vn.outputs['Vector'], sep.inputs['Vector'])

    def math_(op, a, b=None, clamp=False):
        n = N.new('ShaderNodeMath'); n.operation = op; n.use_clamp = clamp
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, bpy.types.NodeSocket):
                L(v, n.inputs[i])
            else:
                n.inputs[i].default_value = v
        return n.outputs['Value']

    z = sep.outputs['Z']
    # proyeccion plana de nubes: uv = xy / (z + 0.25)
    den = math_('ADD', math_('MAXIMUM', z, 0.0), 0.25)
    cx_ = math_('DIVIDE', sep.outputs['X'], den)
    cy_ = math_('DIVIDE', sep.outputs['Y'], den)
    comb = N.new('ShaderNodeCombineXYZ')
    L(cx_, comb.inputs['X']); L(cy_, comb.inputs['Y'])
    comb.inputs['Z'].default_value = 0.0
    mp = N.new('ShaderNodeMapping')
    L(comb.outputs['Vector'], mp.inputs['Vector'])
    mp.inputs['Scale'].default_value = (1.4, 1.4, 1.4)
    mp.name = 'CloudMapping'
    n1 = N.new('ShaderNodeTexNoise'); n1.noise_dimensions = '3D'
    n1.inputs['Scale'].default_value = 1.2; n1.inputs['Detail'].default_value = 8; n1.inputs['Roughness'].default_value = 0.62
    n1.inputs['Distortion'].default_value = 0.6
    L(mp.outputs['Vector'], n1.inputs['Vector'])
    n2 = N.new('ShaderNodeTexNoise'); n2.noise_dimensions = '3D'
    n2.inputs['Scale'].default_value = 5.0; n2.inputs['Detail'].default_value = 6
    L(mp.outputs['Vector'], n2.inputs['Vector'])
    cl = math_('ADD', n1.outputs['Fac'], math_('MULTIPLY', math_('SUBTRACT', n2.outputs['Fac'], 0.5), 0.25))
    ramp = N.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.38
    ramp.color_ramp.elements[1].position = 0.62
    L(cl, ramp.inputs['Fac'])
    cover = ramp.outputs['Color']   # 0 = claro de cielo, 1 = nube densa

    # color del cielo: cielo despejado muy oscuro azul / nubes gris azulado tenues
    sky_hi = N.new('ShaderNodeRGB'); sky_hi.outputs[0].default_value = srgb('#0a1220')
    cloud_c = N.new('ShaderNodeRGB'); cloud_c.outputs[0].default_value = srgb('#1c2430')
    # horizonte algo mas claro
    hz = math_('POWER', math_('SUBTRACT', 1.0, math_('MAXIMUM', z, 0.0)), 3.0)
    mix_c = N.new('ShaderNodeMix'); mix_c.data_type = 'RGBA'
    A = [i for i in mix_c.inputs if i.name == 'A' and i.type == 'RGBA'][0]
    Bc = [i for i in mix_c.inputs if i.name == 'B' and i.type == 'RGBA'][0]
    L(cover, mix_c.inputs[0])
    L(sky_hi.outputs[0], A); L(cloud_c.outputs[0], Bc)
    sky = [o for o in mix_c.outputs if o.type == 'RGBA'][0]

    # luna difusa tras las nubes: parche suave en la direccion de la luna
    md = N.new('ShaderNodeVectorMath'); md.operation = 'DOT_PRODUCT'
    L(vn.outputs['Vector'], md.inputs[0]); md.inputs[1].default_value = tuple(MOON_DIR)
    moon = math_('POWER', math_('MAXIMUM', md.outputs['Value'], 0.0), 60.0)
    moon_c = N.new('ShaderNodeMix'); moon_c.data_type = 'RGBA'
    A2 = [i for i in moon_c.inputs if i.name == 'A' and i.type == 'RGBA'][0]
    B2 = [i for i in moon_c.inputs if i.name == 'B' and i.type == 'RGBA'][0]
    L(math_('MULTIPLY', moon, math_('SUBTRACT', 1.0, math_('MULTIPLY', cover, 0.7)), True), moon_c.inputs[0])
    L(sky, A2); B2.default_value = srgb('#6f86a8')
    sky2 = [o for o in moon_c.outputs if o.type == 'RGBA'][0]

    # resplandor calido de la instalacion en el horizonte
    gd = N.new('ShaderNodeVectorMath'); gd.operation = 'DOT_PRODUCT'
    L(vn.outputs['Vector'], gd.inputs[0]); gd.inputs[1].default_value = tuple(GLOW_DIR)
    glow = math_('MULTIPLY', math_('POWER', math_('MAXIMUM', gd.outputs['Value'], 0.0), 45.0), hz)
    gc = N.new('ShaderNodeMix'); gc.data_type = 'RGBA'
    A3 = [i for i in gc.inputs if i.name == 'A' and i.type == 'RGBA'][0]
    B3 = [i for i in gc.inputs if i.name == 'B' and i.type == 'RGBA'][0]
    L(math_('MULTIPLY', glow, 0.6, True), gc.inputs[0])
    L(sky2, A3); B3.default_value = srgb('#7a3a14')
    final = [o for o in gc.outputs if o.type == 'RGBA'][0]
    # bajo el horizonte: suelo muy oscuro
    L(final, bg.inputs['Color'])
    bg.inputs['Strength'].default_value = 0.8

    # niebla de volumen global (bruma baja)
    vol = N.new('ShaderNodeVolumeScatter')
    vol.inputs['Density'].default_value = 0.0035
    vol.inputs['Anisotropy'].default_value = 0.35
    vol.inputs['Color'].default_value = srgb('#8a97a8')
    # (el volumen global del mundo se evita: en EEVEE se extiende al infinito y apaga el cielo;
    #  la bruma se resuelve con el volumen FX_NieblaRasante que cubre toda la escena)
    bpy.context.scene.world = w
    return w


def mat_fog_volume():
    mb = MB('MAT_Niebla_Rasante')
    mb.nt.links.new  # noqa
    for l in list(mb.nt.links):
        mb.nt.links.remove(l)
    mb.nt.nodes.remove(mb.bsdf)
    vol = mb.node('ShaderNodeVolumeScatter')
    # coords: objeto cubo (-1..1 en z), niebla densa abajo
    x, y, z = mb.sep(mb.tc('Object'))
    zz = mb.math('MAXIMUM', z, 0.0)
    hf = mb.math('EXPONENT', mb.math('MULTIPLY', zz, -0.75))
    mp = mb.node('ShaderNodeMapping')
    mp.name = 'FogMapping'
    mb.nt.links.new(mb.tc('Object'), mp.inputs['Vector'])
    n = mb.noise(0.22, 5, 0.6, vec=mp.outputs['Vector'], dist=0.3)
    n_m = mb.maprange(n, 0.3, 0.75, 0.25, 1.4)
    dens = mb.math('ADD', mb.math('MULTIPLY', mb.math('MULTIPLY', hf, n_m), 0.20), 0.0065)
    mb.nt.links.new(dens, vol.inputs['Density'])
    vol.inputs['Anisotropy'].default_value = 0.25
    vol.inputs['Color'].default_value = srgb('#8fa0b2')
    mb.nt.links.new(vol.outputs['Volume'], mb.out.inputs['Volume'])
    return mb.done()


def build_fog():
    cn = 'Fx'
    for o in list(coll(cn).objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bm = new_bm()
    box(bm, (170, 190, 40.0), (0, 10, 19.0))
    o = obj_from_bm('FX_NieblaRasante', bm, mat_fog_volume(), cn, smooth=False)
    o.visible_shadow = False
    try:
        o.display_type = 'WIRE'
    except Exception:
        pass
    return o


def build_moon():
    ld = bpy.data.lights.get('LUZ_Luna') or bpy.data.lights.new('LUZ_Luna', 'SUN')
    ld.color = (0.55, 0.68, 1.0)
    ld.energy = 0.55
    ld.angle = math.radians(9)
    try:
        ld.volume_factor = 1.0
    except Exception:
        pass
    o = bpy.data.objects.get('LUZ_Luna')
    if o is None:
        o = bpy.data.objects.new('LUZ_Luna', ld)
        coll('Luces').objects.link(o)
    d = MOON_DIR
    o.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    o.location = (20, -20, 30)
    return o


def setup_render(res=(1920, 1080), samples=64):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    ev = sc.eevee
    ev.taa_render_samples = samples
    for k, v in (('use_raytracing', True), ('use_volumetric_shadows', True), ('volumetric_tile_size', '2'),
                 ('volumetric_samples', 96), ('volumetric_end', 140.0), ('volumetric_start', 0.1),
                 ('use_shadows', True), ('use_fast_gi', True)):
        try:
            setattr(ev, k, v)
        except Exception as e:
            print('eevee', k, e)
    vs = sc.view_settings
    try:
        vs.view_transform = 'AgX'
        vs.look = 'AgX - Medium Low Contrast'
    except Exception:
        pass
    vs.exposure = 1.2
    sc.render.film_transparent = False
    sc.render.fps = 24
    sc.frame_start, sc.frame_end = 1, 240


def build_camera():
    cn = 'Camaras'
    cam_d = bpy.data.cameras.get('CAM_Principal') or bpy.data.cameras.new('CAM_Principal')
    cam_d.lens = 32
    cam_d.sensor_width = 36
    cam_d.dof.use_dof = True
    cam_d.clip_end = 400
    o = bpy.data.objects.get('CAM_Principal')
    if o is None:
        o = bpy.data.objects.new('CAM_Principal', cam_d)
        coll(cn).objects.link(o)
    o.location = (3.4, -9.6, 1.55)
    tgt = Vector((-0.1, -3.0, 1.75))
    d = tgt - o.location
    o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    cam_d.dof.focus_distance = d.length
    cam_d.dof.aperture_fstop = 4.0
    bpy.context.scene.camera = o
    return o


def build():
    build_world()
    build_fog()
    build_moon()
    setup_render()
    build_camera()
    # eliminar cubo/luz/camara por defecto
    for n in ('Cube', 'Light', 'Camera'):
        ob = bpy.data.objects.get(n)
        if ob:
            bpy.data.objects.remove(ob, do_unlink=True)
