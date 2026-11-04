"""Helpers comunes para 'La Escena 1: El Traslado' (Blender 5.x, EEVEE).
Todas las mallas se construyen con vertices en coordenadas de mundo reales (metros),
objetos con transformacion identidad, para que los materiales procedurales
(coordenadas de objeto) y la exportacion sean predecibles.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Euler, noise

# ----------------------------------------------------------------------------
# Colecciones / objetos
# ----------------------------------------------------------------------------
def coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def clear_collection(name):
    c = bpy.data.collections.get(name)
    if not c:
        return
    for o in list(c.objects):
        bpy.data.objects.remove(o, do_unlink=True)


def obj_from_bm(name, bm, mat=None, cname='Scene', smooth=True, parent=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    o = bpy.data.objects.new(name, me)
    coll(cname).objects.link(o)
    if mat is not None:
        if isinstance(mat, (list, tuple)):
            for m in mat:
                me.materials.append(m)
        else:
            me.materials.append(mat)
    if parent is not None:
        o.parent = parent
    return o


def new_bm():
    return bmesh.new()


def xf(bm, matrix, verts=None):
    bmesh.ops.transform(bm, matrix=matrix, verts=verts if verts is not None else bm.verts[:])


def merge_bm(dst, src, matrix=None, mat_index=None):
    """copia src dentro de dst (opcionalmente transformado) y libera src"""
    vmap = {}
    for v in src.verts:
        p = v.co.copy()
        if matrix is not None:
            p = matrix @ p
        vmap[v] = dst.verts.new(p)
    for f in src.faces:
        try:
            nf = dst.faces.new([vmap[v] for v in f.verts])
            nf.smooth = f.smooth
            nf.material_index = f.material_index if mat_index is None else mat_index
        except ValueError:
            pass
    src.free()


# ----------------------------------------------------------------------------
# Primitivas bmesh (siempre en coordenadas finales)
# ----------------------------------------------------------------------------
def rot_matrix(rot=(0, 0, 0)):
    return Euler(rot, 'XYZ').to_matrix().to_4x4()


def box(bm, size, loc=(0, 0, 0), rot=(0, 0, 0), bevel=0.0, taper=None, smooth=False):
    """caja: size = (sx,sy,sz) dimensiones totales, centrada en loc"""
    b = bmesh.new()
    bmesh.ops.create_cube(b, size=1.0)
    xf(b, Matrix.Diagonal((size[0], size[1], size[2], 1.0)))
    if bevel > 0:
        try:
            bmesh.ops.bevel(b, geom=b.edges[:], offset=min(bevel, min(size) * 0.35), segments=1, affect='EDGES', clamp_overlap=True)
            for f in b.faces:
                f.smooth = True
        except Exception:
            pass
    elif smooth:
        for f in b.faces:
            f.smooth = True
    M = Matrix.Translation(loc) @ rot_matrix(rot)
    merge_bm(bm, b, M)


def cyl(bm, r1, r2, depth, loc=(0, 0, 0), rot=(0, 0, 0), sides=18, caps=True, r2_eq=False, smooth=True):
    b = bmesh.new()
    bmesh.ops.create_cone(b, cap_ends=caps, cap_tris=False, segments=sides,
                          radius1=r1, radius2=r2, depth=depth)
    if smooth:
        for f in b.faces:
            if len(f.verts) == 4:
                f.smooth = True
    M = Matrix.Translation(loc) @ rot_matrix(rot)
    merge_bm(bm, b, M)


def sphere(bm, r, loc=(0, 0, 0), scale=(1, 1, 1), rot=(0, 0, 0), seg=16, rings=12, smooth=True):
    b = bmesh.new()
    bmesh.ops.create_uvsphere(b, u_segments=seg, v_segments=rings, radius=r)
    if smooth:
        for f in b.faces:
            f.smooth = True
    xf(b, Matrix.Diagonal((scale[0], scale[1], scale[2], 1.0)))
    M = Matrix.Translation(loc) @ rot_matrix(rot)
    merge_bm(bm, b, M)


def ico(bm, r, loc=(0, 0, 0), scale=(1, 1, 1), sub=3, rnd=0.0, seed=0, smooth=True):
    b = bmesh.new()
    bmesh.ops.create_icosphere(b, subdivisions=sub, radius=r)
    if smooth:
        for f in b.faces:
            f.smooth = True
    if rnd > 0:
        rng = random.Random(seed)
        for v in b.verts:
            v.co *= 1.0 + rng.uniform(-rnd, rnd)
    xf(b, Matrix.Diagonal((scale[0], scale[1], scale[2], 1.0)))
    merge_bm(bm, b, Matrix.Translation(loc))


def basis_from_dir(d, up_hint=Vector((0, 0, 1))):
    d = Vector(d).normalized()
    if abs(d.dot(up_hint)) > 0.98:
        up_hint = Vector((0, 1, 0)) if abs(d.y) < 0.9 else Vector((1, 0, 0))
    right = d.cross(up_hint).normalized()
    up = right.cross(d).normalized()
    return right, up, d


def loft(bm, rings, closed=True, caps=(True, True), mat_index=0, smooth=True):
    """rings: lista de (centro, dir_tangente, ancho, alto, sides[, up_hint]) -> malla lofteada.
    Cada anillo es una elipse (ancho en 'right', alto en 'up'). Usa transporte paralelo de marcos
    (sin torsion) y genera las normales hacia afuera."""
    right_prev = None
    allrings = []
    for ring in rings:
        c, d, w, h = ring[0], Vector(ring[1]).normalized(), ring[2], ring[3]
        sides = ring[4] if len(ring) > 4 else 12
        up_hint = Vector(ring[5]) if len(ring) > 5 else Vector((0, 0, 1))
        if right_prev is None:
            right, up, _ = basis_from_dir(d, up_hint)
        else:
            right = right_prev - d * right_prev.dot(d)
            if right.length < 1e-6:
                right, up, _ = basis_from_dir(d, up_hint)
            else:
                right.normalize()
                up = right.cross(d).normalized()
        right_prev = right
        vs = []
        for i in range(sides):
            a = 2 * math.pi * i / sides
            p = Vector(c) + right * (math.cos(a) * w) + up * (math.sin(a) * h)
            vs.append(bm.verts.new(p))
        allrings.append(vs)
    for r in range(len(allrings) - 1):
        a, b = allrings[r], allrings[r + 1]
        n = len(a)
        if len(b) != n:
            continue
        for i in range(n):
            try:
                f = bm.faces.new([a[i], b[i], b[(i + 1) % n], a[(i + 1) % n]])
                f.smooth = smooth
                f.material_index = mat_index
            except ValueError:
                pass
    if caps[0]:
        try:
            f = bm.faces.new(allrings[0]); f.smooth = smooth; f.material_index = mat_index
        except ValueError:
            pass
    if caps[1]:
        try:
            f = bm.faces.new(allrings[-1][::-1]); f.smooth = smooth; f.material_index = mat_index
        except ValueError:
            pass
    return allrings


def tube(bm, pts, radii, sides=6, caps=True, mat_index=0):
    """tubo siguiendo una polilinea. radii: float o lista"""
    n = len(pts)
    if not isinstance(radii, (list, tuple)):
        radii = [radii] * n
    rings = []
    for i, p in enumerate(pts):
        if i == 0:
            d = Vector(pts[1]) - Vector(pts[0])
        elif i == n - 1:
            d = Vector(pts[-1]) - Vector(pts[-2])
        else:
            d = Vector(pts[i + 1]) - Vector(pts[i - 1])
        rings.append((p, d, radii[i], radii[i], sides))
    return loft(bm, rings, caps=(caps, caps), mat_index=mat_index)


def limb(bm, p0, p1, r0, r1, sides=10, bulge=0.0, segs=4, mat_index=0, flat=1.0):
    p0 = Vector(p0); p1 = Vector(p1)
    d = p1 - p0
    rings = []
    for i in range(segs + 1):
        t = i / segs
        r = r0 + (r1 - r0) * t + bulge * math.sin(math.pi * t)
        rings.append((p0 + d * t, d, r, r * flat, sides))
    return loft(bm, rings, mat_index=mat_index)


def plank(bm, p0, p1, width, thick, wobble=0.0, rng=None, splinter=0.0):
    """tablon desde p0 a p1 (eje largo), con ancho en X (o perpendicular) y espesor en Z"""
    rng = rng or random
    p0 = Vector(p0); p1 = Vector(p1)
    d = p1 - p0
    L = d.length
    right, up, _ = basis_from_dir(d, Vector((0, 0, 1)))
    # ancho a lo largo de 'right', espesor a lo largo de 'up'
    nseg = max(2, int(L / 0.35))
    rows = []
    for i in range(nseg + 1):
        t = i / nseg
        c = p0 + d * t
        off = Vector((0, 0, 0))
        if wobble:
            off = up * rng.uniform(-wobble, wobble) + right * rng.uniform(-wobble, wobble) * 0.5
        w = width * 0.5 * (1 + rng.uniform(-0.01, 0.01))
        th = thick * 0.5
        v = [bm.verts.new(c + off + right * (-w) + up * (-th)),
             bm.verts.new(c + off + right * (w) + up * (-th)),
             bm.verts.new(c + off + right * (w) + up * (th)),
             bm.verts.new(c + off + right * (-w) + up * (th))]
        rows.append(v)
    for r in range(nseg):
        a, b = rows[r], rows[r + 1]
        for i in range(4):
            try:
                bm.faces.new([a[i], a[(i + 1) % 4], b[(i + 1) % 4], b[i]])
            except ValueError:
                pass
    try:
        bm.faces.new(rows[0][::-1]); bm.faces.new(rows[-1])
    except ValueError:
        pass
    # astillas en los extremos
    if splinter > 0:
        for row in (rows[0], rows[-1]):
            for v in row:
                if rng.random() < 0.6:
                    v.co += d.normalized() * (rng.uniform(-splinter, splinter)) * (1 if row is rows[-1] else 1)


def noise_displace(bm, scale, amp, seed=0, along_normal=True, verts=None, axis=None):
    off = Vector((seed * 13.1, seed * 7.7, seed * 3.3))
    bm.normal_update()
    for v in (verts if verts is not None else bm.verts):
        n = noise.noise((v.co + off) * scale)
        n2 = noise.noise((v.co + off) * scale * 2.7 + Vector((5, 5, 5))) * 0.5
        d = (n + n2) * amp
        if along_normal:
            v.co += v.normal * d
        elif axis is not None:
            v.co += Vector(axis) * d


# ----------------------------------------------------------------------------
# Materiales procedurales PBR
# ----------------------------------------------------------------------------
def _setin(inp, v):
    if isinstance(v, bpy.types.NodeSocket):
        inp.node.id_data.links.new(v, inp)
    else:
        try:
            inp.default_value = v
        except TypeError:
            inp.default_value = (v[0], v[1], v[2], v[3] if len(v) > 3 else 1.0)


def rgba(c, a=1.0):
    return (c[0], c[1], c[2], a)


def srgb(hexstr):
    """hex '#rrggbb' -> color lineal"""
    h = hexstr.lstrip('#')
    r, g, b = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (f(r), f(g), f(b), 1.0)


class MB:
    def __init__(s, name):
        # se reutiliza el datablock si existe (para no dejar objetos sin material al reconstruir)
        s.m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        try:
            s.m.use_nodes = True
        except Exception:
            pass
        s.nt = s.m.node_tree
        s.nt.nodes.clear()
        s.out = s.nt.nodes.new('ShaderNodeOutputMaterial')
        s.bsdf = s.nt.nodes.new('ShaderNodeBsdfPrincipled')
        s.nt.links.new(s.bsdf.outputs['BSDF'], s.out.inputs['Surface'])
        s._tc = None

    def node(s, t, **props):
        n = s.nt.nodes.new(t)
        for k, v in props.items():
            setattr(n, k, v)
        return n

    def tc(s, kind='Object'):
        if s._tc is None:
            s._tc = s.node('ShaderNodeTexCoord')
        return s._tc.outputs[kind]

    def map(s, vec=None, scale=(1, 1, 1), loc=(0, 0, 0)):
        n = s.node('ShaderNodeMapping')
        _setin(n.inputs['Vector'], vec if vec is not None else s.tc())
        n.inputs['Scale'].default_value = scale
        n.inputs['Location'].default_value = loc
        return n.outputs['Vector']

    def noise(s, scale, detail=6.0, rough=0.55, vec=None, dist=0.0):
        n = s.node('ShaderNodeTexNoise')
        try:
            n.noise_dimensions = '3D'
        except Exception:
            pass
        _setin(n.inputs['Vector'], vec if vec is not None else s.tc())
        n.inputs['Scale'].default_value = scale
        n.inputs['Detail'].default_value = detail
        n.inputs['Roughness'].default_value = rough
        try:
            n.inputs['Distortion'].default_value = dist
        except Exception:
            pass
        return n.outputs['Fac']

    def vor(s, scale, rnd=1.0, vec=None, out='Distance', feature='F1'):
        n = s.node('ShaderNodeTexVoronoi')
        n.voronoi_dimensions = '3D'
        n.feature = feature
        _setin(n.inputs['Vector'], vec if vec is not None else s.tc())
        n.inputs['Scale'].default_value = scale
        n.inputs['Randomness'].default_value = rnd
        return n.outputs[out]

    def wave(s, scale, dist=0.0, detail=0.0, vec=None, direction='X', ptype='BANDS', profile='SAW'):
        n = s.node('ShaderNodeTexWave')
        n.wave_type = ptype
        n.bands_direction = direction
        n.wave_profile = profile
        _setin(n.inputs['Vector'], vec if vec is not None else s.tc())
        n.inputs['Scale'].default_value = scale
        n.inputs['Distortion'].default_value = dist
        n.inputs['Detail'].default_value = detail
        return n.outputs['Fac']

    def ramp(s, fac, stops, interp='LINEAR'):
        n = s.node('ShaderNodeValToRGB')
        n.color_ramp.interpolation = interp
        els = n.color_ramp.elements
        while len(els) > len(stops):
            els.remove(els[-1])
        while len(els) < len(stops):
            els.new(0.5)
        for e, (p, c) in zip(els, stops):
            e.position = p
            e.color = c if len(c) == 4 else (c[0], c[1], c[2], 1.0)
        _setin(n.inputs['Fac'], fac)
        return n.outputs['Color']

    def ramp_f(s, fac, a, b, pa=0.0, pb=1.0):
        """rampa en escala de grises -> devuelve color (usar .. R canal via math si hace falta)"""
        return s.ramp(fac, [(pa, (0, 0, 0, 1)), (pb, (1, 1, 1, 1))])

    def mixc(s, fac, a, b):
        n = s.node('ShaderNodeMix', data_type='RGBA')
        _setin(n.inputs['Factor'] if 'Factor' in n.inputs else n.inputs[0], fac)
        A = [i for i in n.inputs if i.name == 'A' and i.type == 'RGBA'][0]
        B = [i for i in n.inputs if i.name == 'B' and i.type == 'RGBA'][0]
        _setin(A, a); _setin(B, b)
        return [o for o in n.outputs if o.type == 'RGBA'][0]

    def mixf(s, fac, a, b):
        n = s.node('ShaderNodeMix', data_type='FLOAT')
        _setin(n.inputs['Factor'], fac)
        A = [i for i in n.inputs if i.name == 'A' and i.type == 'VALUE'][0]
        B = [i for i in n.inputs if i.name == 'B' and i.type == 'VALUE'][0]
        _setin(A, a); _setin(B, b)
        return [o for o in n.outputs if o.type == 'VALUE'][0]

    def math(s, op, a, b=None, clamp=False, c=None):
        n = s.node('ShaderNodeMath', operation=op)
        n.use_clamp = clamp
        _setin(n.inputs[0], a)
        if b is not None:
            _setin(n.inputs[1], b)
        if c is not None:
            _setin(n.inputs[2], c)
        return n.outputs['Value']

    def maprange(s, v, fmin, fmax, tmin=0.0, tmax=1.0, clamp=True):
        n = s.node('ShaderNodeMapRange')
        n.clamp = clamp
        _setin(n.inputs['Value'], v)
        _setin(n.inputs['From Min'], fmin); _setin(n.inputs['From Max'], fmax)
        _setin(n.inputs['To Min'], tmin); _setin(n.inputs['To Max'], tmax)
        return n.outputs['Result']

    def sep(s, vec=None):
        n = s.node('ShaderNodeSeparateXYZ')
        _setin(n.inputs['Vector'], vec if vec is not None else s.tc())
        return n.outputs['X'], n.outputs['Y'], n.outputs['Z']

    def attr(s, name):
        n = s.node('ShaderNodeAttribute')
        n.attribute_name = name
        return n.outputs['Fac']

    def bump(s, height, strength=0.5, dist=0.02, normal=None, invert=False):
        n = s.node('ShaderNodeBump', invert=invert)
        _setin(n.inputs['Strength'], strength)
        _setin(n.inputs['Distance'], dist)
        _setin(n.inputs['Height'], height)
        if normal is not None:
            _setin(n.inputs['Normal'], normal)
        return n.outputs['Normal']

    def set(s, **kw):
        b = s.bsdf
        for k, v in kw.items():
            name = k.replace('_', ' ')
            _setin(b.inputs[name], v)
        return s

    def done(s):
        return s.m


def _mudmask(mb, mud_h, amount, scale=6.0):
    x, y, z = mb.sep()
    hf = mb.maprange(z, 0.0, mud_h, 1.0, 0.0)
    n = mb.noise(scale, 7, 0.6)
    n2 = mb.noise(scale * 9, 4, 0.5)
    v = mb.math('ADD', hf, mb.math('MULTIPLY', mb.math('SUBTRACT', n, 0.5), 0.9))
    v = mb.math('ADD', v, mb.math('MULTIPLY', mb.math('SUBTRACT', n2, 0.5), 0.35))
    v = mb.math('ADD', v, amount - 0.5)
    return mb.maprange(v, 0.45, 0.62, 0.0, 1.0)


def weathered(name, c1, c2, rough=0.6, metal=0.0, scale=3.0, rust=0.0, mud_h=0.0,
              mud=0.5, bump=0.4, grime=0.5, wear=0.0, wear_col=None, wet=0.0, seed=0):
    """Material generico desgastado: color base ruidoso, oxido, barro por altura, grime, bump."""
    mb = MB(name)
    vec = mb.map(scale=(1, 1, 1), loc=(seed * 3.7, seed * 1.3, seed * 2.1))
    n1 = mb.noise(scale, 8, 0.6, vec=vec)
    col = mb.mixc(mb.ramp(n1, [(0.3, (0, 0, 0, 1)), (0.7, (1, 1, 1, 1))]), c1, c2)
    # grime: vetas verticales oscuras
    vecs = mb.map(vec=vec, scale=(1.0, 1.0, 0.18))
    gr = mb.noise(scale * 2.3, 6, 0.6, vec=vecs)
    grm = mb.maprange(gr, 0.4, 0.75, 0.0, grime)
    col = mb.mixc(grm, col, (0.01, 0.01, 0.008, 1))
    rough_v = mb.mixf(n1, rough - 0.15, rough + 0.15)
    metal_v = metal
    rm = None
    if rust > 0:
        rn = mb.noise(scale * 1.6, 8, 0.65, vec=mb.map(vec=vec, loc=(10, 3, 5)))
        rn2 = mb.noise(scale * 14, 5, 0.5, vec=vec)
        rv = mb.math('ADD', rn, mb.math('MULTIPLY', mb.math('SUBTRACT', rn2, 0.5), 0.35))
        rm = mb.maprange(rv, 0.70 - rust * 0.22, 0.82 - rust * 0.22, 0.0, 1.0)
        rcol = mb.ramp(rn2, [(0.25, srgb('#261108')), (0.55, srgb('#47200c')), (0.85, srgb('#6b3113'))])
        col = mb.mixc(rm, col, rcol)
        rough_v = mb.mixf(rm, rough_v, 0.88)
        metal_v = mb.mixf(rm, metal, metal * 0.15)
    if wear > 0:
        # desgaste (pintura levantada -> metal pelado) por voronoi fino
        vd = mb.vor(scale * 8, 1.0, vec=vec)
        wn = mb.noise(scale * 2.0, 5, 0.5, vec=vec)
        wm = mb.maprange(mb.math('ADD', mb.math('SUBTRACT', 1.0, vd), mb.math('MULTIPLY', wn, 0.6)),
                         1.35 - wear * 0.5, 1.5 - wear * 0.4, 0.0, 1.0)
        col = mb.mixc(wm, col, wear_col or (0.05, 0.045, 0.04, 1))
    height = mb.noise(scale * 20, 6, 0.6, vec=vec)
    nrm = mb.bump(height, bump, 0.01)
    if mud_h > 0:
        mm = _mudmask(mb, mud_h, mud)
        mcol = mb.mixc(mb.noise(40, 4, 0.5), srgb('#2a1c10'), srgb('#4b3722'))
        col = mb.mixc(mm, col, mcol)
        rough_v = mb.mixf(mm, rough_v, 0.42 - wet * 0.1)
        metal_v = mb.mixf(mm, metal_v, 0.0)
        mh = mb.noise(60, 5, 0.6)
        nrm = mb.bump(mb.math('ADD', height, mb.math('MULTIPLY', mh, mm)), bump + 0.4, 0.015)
    mb.set(Base_Color=col, Roughness=rough_v, Metallic=metal_v, Normal=nrm)
    return mb.done()


def cloth_mat(name, c1, c2, rough=0.9, weave=300.0, scale=6.0, bump=0.5, mud_h=0.0, mud=0.4, dirt=0.4, sheen=0.0, seed=0):
    mb = MB(name)
    vec = mb.map(loc=(seed * 3.1, seed * 1.1, seed * 2.9))
    n1 = mb.noise(scale, 7, 0.6, vec=vec)
    col = mb.mixc(mb.ramp(n1, [(0.25, (0, 0, 0, 1)), (0.75, (1, 1, 1, 1))]), c1, c2)
    fib = mb.noise(weave, 2, 0.5, vec=vec)
    wv = mb.math('MULTIPLY',
                 mb.wave(weave * 0.3, 0.2, 0.0, vec=vec, direction='X'),
                 mb.wave(weave * 0.3, 0.2, 0.0, vec=mb.map(vec=vec, scale=(1, 1, 1)), direction='Y'))
    h = mb.math('ADD', mb.math('MULTIPLY', fib, 0.7), mb.math('MULTIPLY', wv, 0.3))
    dn = mb.noise(scale * 0.7, 6, 0.65, vec=vec)
    dm = mb.maprange(dn, 0.35, 0.8, 0.0, dirt)
    col = mb.mixc(dm, col, (0.02, 0.016, 0.012, 1))
    col = mb.mixc(mb.maprange(fib, 0.3, 0.7, 0.0, 0.25), col, (0.0, 0.0, 0.0, 1))
    nrm = mb.bump(h, bump, 0.004)
    rough_v = rough
    if mud_h > 0:
        mm = _mudmask(mb, mud_h, mud)
        col = mb.mixc(mm, col, mb.mixc(mb.noise(30, 4, 0.5), srgb('#2a1c10'), srgb('#4b3722')))
        rough_v = mb.mixf(mm, rough, 0.5)
    mb.set(Base_Color=col, Roughness=rough_v, Normal=nrm)
    if sheen:
        try:
            mb.set(Sheen_Weight=sheen, Sheen_Roughness=0.5)
        except Exception:
            pass
    return mb.done()


def emit_mat(name, color, strength):
    mb = MB(name)
    mb.set(Base_Color=color, Emission_Color=color, Emission_Strength=strength, Roughness=0.4)
    return mb.done()


def black_mat(name='Negro', rough=0.9):
    mb = MB(name)
    mb.set(Base_Color=(0.004, 0.004, 0.004, 1), Roughness=rough)
    return mb.done()


def mat_get(name, builder):
    m = bpy.data.materials.get(name)
    if m is None:
        m = builder()
    return m


RNG = random.Random(1976)
