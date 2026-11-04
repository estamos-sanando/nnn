"""Props e items interactivos (interior de la caja de carga y suelo exterior inmediato):
- Mantas militares de lana (dobladas y arrugadas)
- Cajones de madera verde oliva (municion y herramientas) con herrajes oxidados y manijas de soga
- Herramientas sueltas (llaves fijas oxidadas, martillo, destornillador)
- Radio militar portatil de campaña años 70 con microtelefono y antena
- Linterna militar en L (estilo Fulton MX-991/U verde oliva) encendida con filamento tenue
- Libreta de bolsillo gastada (tapa oscura de cuero/lona y esquinas dobladas)
- Zapatilla de lona y goma estilo 'Flecha' años 70 muy gastada (lista para inspeccion 3D)
- Detalle de suelo exterior (cajon en el barro, cuña de madera, llave oxidada, piedras y ramas)
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Euler, noise
from common import *

CN = 'Props_Interactivos'
FLOOR_Z = 1.25


# ----------------------------------------------------------------------------
# Materiales PBR de props
# ----------------------------------------------------------------------------
def prop_mats():
    M = {}
    # Lana militar verde grisaceo oscuro con franja tejida
    mb = MB('MAT_Manta_Lana_Militar')
    vec = mb.tc('Object')
    w1 = mb.wave(180.0, 0.4, 0.0, vec=vec, direction='X')
    w2 = mb.wave(180.0, 0.4, 0.0, vec=vec, direction='Y')
    fuzz = mb.noise(240.0, 4, 0.7, vec=vec)
    dirt = mb.noise(6.0, 6, 0.65, vec=vec)
    base_c = mb.mixc(mb.noise(3.5, 5, 0.6, vec=vec), srgb('#272e24'), srgb('#394033'))
    # franja oscura clasica de manta de cuartel
    _, yy, _ = mb.sep(vec)
    stripe = mb.maprange(mb.math('ABSOLUTE', mb.math('SUBTRACT', yy, 0.16)), 0.018, 0.024, 1.0, 0.0)
    base_c = mb.mixc(mb.math('MULTIPLY', stripe, 0.7), base_c, srgb('#141712'))
    base_c = mb.mixc(mb.maprange(dirt, 0.42, 0.80, 0.0, 0.65), base_c, srgb('#18130d'))
    h = mb.math('ADD', mb.math('MULTIPLY', mb.math('ADD', w1, w2), 0.35), mb.math('MULTIPLY', fuzz, 0.65))
    mb.set(Base_Color=base_c, Roughness=0.96, Normal=mb.bump(h, 0.85, 0.005))
    try:
        mb.set(Sheen_Weight=0.35, Sheen_Roughness=0.6)
    except Exception:
        pass
    M['blanket'] = mb.done()
    M['blanket'].use_backface_culling = False

    # Madera pintada verde militar muy gastada para cajones
    M['crate_wood'] = weathered('MAT_Madera_Cajon_Militar', srgb('#26301d'), srgb('#39442a'),
                                rough=0.84, metal=0.0, scale=6.0, rust=0.0, mud_h=0.22, mud=0.55,
                                bump=0.75, grime=0.6, wear=0.55, wear_col=srgb('#594832'), seed=31)
    M['rust_iron'] = weathered('MAT_Herraje_Oxidado', srgb('#1c1612'), srgb('#332419'),
                               rough=0.68, metal=0.82, scale=12.0, rust=0.72, bump=0.7, grime=0.5, seed=32)
    M['tool_steel'] = weathered('MAT_Acero_Herramienta', srgb('#2b2926'), srgb('#47433d'),
                                rough=0.48, metal=0.90, scale=16.0, rust=0.58, bump=0.55, grime=0.5, seed=33)
    M['tool_wood'] = weathered('MAT_Mango_Madera', srgb('#3d2816'), srgb('#634427'),
                               rough=0.68, metal=0.0, scale=14.0, bump=0.5, grime=0.55, seed=34)
    M['amber_grip'] = weathered('MAT_Mango_Ambar_70s', srgb('#5e340e'), srgb('#8a5219'),
                                rough=0.35, metal=0.0, scale=18.0, bump=0.35, grime=0.45, seed=35)
    M['olive_metal'] = weathered('MAT_Metal_Oliva_Equipo', srgb('#2d3620'), srgb('#424c2e'),
                                 rough=0.58, metal=0.35, scale=14.0, rust=0.32, bump=0.4, grime=0.5,
                                 wear=0.45, wear_col=srgb('#636159'), seed=36)
    M['bakelite'] = weathered('MAT_Baquelita_Negra', srgb('#0d0d0c'), srgb('#1c1b19'),
                              rough=0.38, metal=0.05, scale=20.0, bump=0.25, grime=0.35, seed=37)
    M['brass'] = weathered('MAT_Bronce_Gastado', srgb('#594622'), srgb('#826936'),
                           rough=0.44, metal=0.88, scale=18.0, rust=0.25, bump=0.35, grime=0.45, seed=38)
    M['radio_dial'] = emit_mat('MAT_Dial_Radio_Tenue', srgb('#8fb870'), 0.45)
    M['flash_bulb'] = emit_mat('MAT_Bulbo_Linterna', srgb('#ffbe73'), 12.0)

    # Libreta de campo
    M['nb_cover'] = cloth_mat('MAT_Tapa_Libreta', srgb('#1a1612'), srgb('#2b231b'),
                              rough=0.82, weave=220.0, scale=14.0, bump=0.65, dirt=0.65, seed=39)
    mb_p = MB('MAT_Papel_Libreta')
    np = mb_p.noise(24.0, 4, 0.55)
    pcol = mb_p.mixc(np, srgb('#9e8f6e'), srgb('#bfb18e'))
    pcol = mb_p.mixc(mb_p.maprange(mb_p.noise(80.0, 3, 0.5), 0.45, 0.85, 0.0, 0.4), pcol, srgb('#594b34'))
    mb_p.set(Base_Color=pcol, Roughness=0.92, Normal=mb_p.bump(np, 0.35, 0.002))
    M['nb_paper'] = mb_p.done()

    # Zapatilla 'Flecha' (lona cruda muy sucia, goma blanquecina amarillenta con barro, banda negra)
    M['flecha_canvas'] = cloth_mat('MAT_Flecha_Lona', srgb('#8f846c'), srgb('#6b614c'),
                                   rough=0.93, weave=260.0, scale=16.0, bump=0.8, dirt=0.82, sheen=0.2, seed=40)
    M['flecha_canvas'].use_backface_culling = False
    M['flecha_rubber'] = weathered('MAT_Flecha_Goma_Blanca', srgb('#8c826d'), srgb('#aba089'),
                                   rough=0.72, metal=0.0, scale=18.0, mud_h=0.03, mud=0.65,
                                   bump=0.5, grime=0.72, seed=41)
    M['flecha_sole'] = weathered('MAT_Flecha_Suela_Goma', srgb('#2e2318'), srgb('#473727'),
                                 rough=0.85, metal=0.0, scale=22.0, bump=0.8, grime=0.65, seed=42)
    M['flecha_accent'] = weathered('MAT_Flecha_Banda_Oscura', srgb('#141821'), srgb('#222836'),
                                   rough=0.7, metal=0.0, scale=20.0, bump=0.35, grime=0.5, seed=43)
    M['flecha_lace'] = cloth_mat('MAT_Flecha_Cordones', srgb('#998e75'), srgb('#665c47'),
                                 rough=0.94, weave=300.0, scale=22.0, bump=0.7, dirt=0.85, seed=44)

    M['rope'] = bpy.data.materials.get('MAT_Soga')
    if M['rope'] is None:
        import truck
        M['rope'] = truck.rope_mat('MAT_Soga')
    M['stencil'] = bpy.data.materials.get('MAT_Estarcido_Blanco') or emit_mat('MAT_Estarcido_Blanco', srgb('#aba58c'), 0.0)
    return M


def place_local(bm, loc, rot=(0, 0, 0)):
    M_ = Matrix.Translation(loc) @ rot_matrix(rot)
    xf(bm, M_)


# ----------------------------------------------------------------------------
# 1. Mantas militares de lana (dobladas y arrugadas)
# ----------------------------------------------------------------------------
def make_crumpled_blanket(name, loc, yaw, sx, sy, amp, seed, mat, parent):
    bm = new_bm()
    nx, ny = 26, 26
    off = Vector((seed * 5.1, seed * 3.7, seed * 1.9))
    grid = []
    for j in range(ny + 1):
        row = []
        v = j / ny - 0.5
        for i in range(nx + 1):
            u = i / nx - 0.5
            x = u * sx
            y = v * sy
            # pliegues suaves tipo tela pesada + bordes caidos al piso
            edge = max(0.0, 1.0 - max(abs(u), abs(v)) * 1.85)
            fold1 = math.sin(u * 9.5 + noise.noise(Vector((u * 3, v * 3, seed))) * 2.5) * 0.5 + 0.5
            fold2 = noise.noise(Vector((x * 4.2, y * 4.2, 0.0)) + off) * 0.5 + 0.5
            z = 0.008 + edge * amp * (0.45 * fold1 + 0.55 * fold2)
            # arruga lateral
            x += noise.noise(Vector((u * 5, v * 5, seed + 4))) * 0.035
            y += noise.noise(Vector((u * 5, v * 5, seed + 9))) * 0.035
            row.append(bm.verts.new((x, y, z)))
        grid.append(row)
    for j in range(ny):
        for i in range(nx):
            f = bm.faces.new([grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]])
            f.smooth = True
    # dar espesor real a la manta de lana
    res = bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.011)
    for f in bm.faces:
        f.smooth = True
    place_local(bm, loc, (0, 0, yaw))
    return obj_from_bm(name, bm, mat, CN, smooth=True, parent=parent)


def make_folded_blanket(name, loc, yaw, mat, parent):
    bm = new_bm()
    # 4 capas apiladas con dobleces redondeados en los extremos
    layers = 4
    w, l, th = 0.46, 0.60, 0.020
    for k in range(layers):
        zc = 0.012 + k * (th + 0.002)
        box(bm, (w - k * 0.008, l - k * 0.01, th), (0, 0, zc), rot=(0, 0, (k % 2 - 0.5) * 0.04), bevel=0.008)
        if k < layers - 1:
            side = 1 if k % 2 == 0 else -1
            cyl(bm, th * 0.62, th * 0.62, l - 0.02, (side * (w * 0.48), 0, zc + th * 0.5), (math.pi / 2, 0, 0), sides=10)
    noise_displace(bm, 8.0, 0.005, seed=77)
    place_local(bm, loc, (0, 0, yaw))
    return obj_from_bm(name, bm, mat, CN, smooth=True, parent=parent)


# ----------------------------------------------------------------------------
# 2. Cajones de municion y herramientas (madera verde + herrajes oxidados + soga)
# ----------------------------------------------------------------------------
def make_crate(name, size, loc, rot, lid_ajar, M, rng, parent):
    sx, sy, sz = size
    bw, bi, br, bs = new_bm(), new_bm(), new_bm(), new_bm()
    # cuerpo de listones horizontales
    nslats = 3
    sh = (sz - 0.04) / nslats
    for r in range(nslats):
        zc = 0.02 + sh * (r + 0.5)
        box(bw, (sx, 0.022, sh - 0.005), (0, -sy / 2 + 0.011, zc), bevel=0.002)
        box(bw, (sx, 0.022, sh - 0.005), (0, sy / 2 - 0.011, zc), bevel=0.002)
        box(bw, (0.022, sy - 0.04, sh - 0.005), (-sx / 2 + 0.011, 0, zc), bevel=0.002)
        box(bw, (0.022, sy - 0.04, sh - 0.005), (sx / 2 - 0.011, 0, zc), bevel=0.002)
    box(bw, (sx - 0.02, sy - 0.02, 0.022), (0, 0, 0.012))  # fondo
    # refuerzos verticales en las esquinas
    for ex in (-1, 1):
        for ey in (-1, 1):
            box(bw, (0.042, 0.032, sz - 0.03), (ex * (sx / 2 - 0.018), ey * (sy / 2 + 0.006), (sz - 0.02) / 2), bevel=0.002)
            # cantoneras de hierro oxidado
            box(bi, (0.052, 0.045, 0.045), (ex * (sx / 2 - 0.012), ey * (sy / 2 - 0.005), sz - 0.045), bevel=0.002)
            box(bi, (0.052, 0.045, 0.045), (ex * (sx / 2 - 0.012), ey * (sy / 2 - 0.005), 0.026), bevel=0.002)
    # tapa de listones
    lid_bm = new_bm()
    lid_i = new_bm()
    for k in range(3):
        yy = -sy / 2 + (sy / 3) * (k + 0.5)
        box(lid_bm, (sx + 0.016, sy / 3 - 0.005, 0.024), (0, yy, 0.012), bevel=0.003)
    for ex in (-1, 1):
        box(lid_bm, (0.05, sy + 0.01, 0.016), (ex * (sx * 0.34), 0, 0.030), bevel=0.002)
    # cierres metalicos delanteros (aldabas oxidadas) y bisagras traseras
    for ex in (-1, 1):
        lx = ex * sx * 0.28
        box(bi, (0.034, 0.014, 0.055), (lx, -sy / 2 - 0.012, sz - 0.055), bevel=0.002)
        cyl(bi, 0.010, 0.010, 0.024, (lx, -sy / 2 - 0.018, sz - 0.068), (0, math.pi / 2, 0), sides=8)
        box(lid_i, (0.030, 0.016, 0.045), (lx, -sy / 2 - 0.012, -0.008), bevel=0.002)
        # bisagra trasera
        box(bi, (0.036, 0.012, 0.05), (lx, sy / 2 + 0.010, sz - 0.045), bevel=0.002)
    M_lid = Matrix.Translation((0, 0, sz - 0.015)) @ rot_matrix((0, 0, lid_ajar))
    merge_bm(bw, lid_bm, M_lid)
    merge_bm(bi, lid_i, M_lid)

    # manijas de soga gruesa en ambos extremos
    for ex in (-1, 1):
        hx = ex * (sx / 2 + 0.012)
        box(bw, (0.024, 0.16, 0.038), (hx, 0, sz * 0.58), bevel=0.003)
        pts = [Vector((hx, -0.055, sz * 0.58)),
               Vector((hx + ex * 0.035, -0.045, sz * 0.50)),
               Vector((hx + ex * 0.048, 0.0, sz * 0.44)),
               Vector((hx + ex * 0.035, 0.045, sz * 0.50)),
               Vector((hx, 0.055, sz * 0.58))]
        tube(br, pts, 0.0095, sides=6)

    # marcas estarcidas desgastadas en el frente
    for ks, (ox, wz) in enumerate([(-0.10, 0.09), (0.04, 0.12), (-0.04, 0.06)]):
        box(bs, (wz, 0.003, 0.018), (ox, -sy / 2 - 0.002, sz * 0.52 - ks * 0.032))

    out = new_bm()
    for b, mi in ((bw, 0), (bi, 1), (br, 2), (bs, 3)):
        merge_bm(out, b, None, mi)
    place_local(out, loc, rot)
    return obj_from_bm(name, out, [M['crate_wood'], M['rust_iron'], M['rope'], M['stencil']], CN, smooth=False, parent=parent)


# ----------------------------------------------------------------------------
# 3. Herramientas sueltas (llaves fijas oxidadas, martillo, destornillador)
# ----------------------------------------------------------------------------
def wrench_bm(bm, length=0.22, scale=1.0):
    """llave combinada/fija oxidada sobre el plano XY"""
    s = scale
    hl = length * 0.5 * s
    # cuerpo plano con nervio
    box(bm, (length * 0.72 * s, 0.018 * s, 0.006 * s), (0, 0, 0.005 * s), bevel=0.0015 * s)
    box(bm, (length * 0.55 * s, 0.009 * s, 0.009 * s), (0, 0, 0.006 * s))
    # boca abierta en -X (dos mordazas en C inclinadas 15 grados)
    c1 = Vector((-hl, 0.003 * s, 0.006 * s))
    cyl(bm, 0.022 * s, 0.022 * s, 0.008 * s, c1 + Vector((0.010 * s, 0, 0)), (0, 0, 0), sides=12)
    for js in (-1, 1):
        box(bm, (0.026 * s, 0.008 * s, 0.008 * s), c1 + Vector((-0.008 * s, js * 0.012 * s, 0)), rot=(0, 0, 0.22))
    # ojo estriado cerrado en +X
    c2 = Vector((hl, 0, 0.007 * s))
    pts_ring = []
    for k in range(16):
        a = 2 * math.pi * k / 16
        pts_ring.append(c2 + Vector((math.cos(a) * 0.017 * s, math.sin(a) * 0.017 * s, 0)))
    pts_ring.append(pts_ring[0])
    tube(bm, pts_ring, 0.0055 * s, sides=6, caps=False)


def make_tools(M, parent):
    objs = []
    # 2 llaves oxidadas en la caja
    for idx, (loc, yaw, ln, sc) in enumerate([((-0.10, -0.58, FLOOR_Z), 0.52, 0.24, 1.0),
                                              ((0.10, -2.18, FLOOR_Z), -1.05, 0.20, 0.88)]):
        b = new_bm()
        wrench_bm(b, ln, sc)
        place_local(b, loc, (0, 0, yaw))
        objs.append(obj_from_bm('PROP_Llave_Oxidada_%d' % (idx + 1), b, M['rust_iron'], CN, smooth=True, parent=parent))

    # Martillo (mango de madera torneada + cabeza de acero forjado oxidado)
    bh, bm_w = new_bm(), new_bm()
    # mango a lo largo de X
    limb(bm_w, (-0.15, 0, 0.016), (0.14, 0, 0.018), 0.015, 0.012, sides=10, bulge=0.003, segs=5, flat=0.75)
    # cabeza transversal en Y (en X = +0.13)
    box(bh, (0.032, 0.072, 0.028), (0.13, -0.008, 0.018), bevel=0.004)
    cyl(bh, 0.015, 0.017, 0.036, (0.13, -0.052, 0.018), (math.pi / 2, 0, 0), sides=12)   # boca golpeadora
    # uña / pena trasera curvada
    for sgn in (-1, 1):
        box(bh, (0.011, 0.042, 0.010), (0.13 + sgn * 0.008, 0.042, 0.015), rot=(-0.28, 0, 0), bevel=0.002)
    ham = new_bm()
    merge_bm(ham, bm_w, None, 0)
    merge_bm(ham, bh, None, 1)
    place_local(ham, (-0.04, -1.24, FLOOR_Z), (0.04, 0, 0.88))
    objs.append(obj_from_bm('PROP_Martillo', ham, [M['tool_wood'], M['tool_steel']], CN, smooth=True, parent=parent))

    # Destornillador años 70 (mango acanalado ambar oscuro + virola + vastago plano)
    bg, bs = new_bm(), new_bm()
    limb(bg, (-0.11, 0, 0.015), (-0.015, 0, 0.015), 0.015, 0.013, sides=10, bulge=0.003, segs=4)
    cyl(bs, 0.013, 0.011, 0.014, (-0.010, 0, 0.015), (0, math.pi / 2, 0), sides=10)       # virola
    cyl(bs, 0.0035, 0.0035, 0.115, (0.052, 0, 0.015), (0, math.pi / 2, 0), sides=8)       # vastago
    box(bs, (0.018, 0.008, 0.002), (0.112, 0, 0.015))                                      # punta plana
    sd = new_bm()
    merge_bm(sd, bg, None, 0)
    merge_bm(sd, bs, None, 1)
    place_local(sd, (0.17, -2.26, FLOOR_Z), (0, 0, -1.18))
    objs.append(obj_from_bm('PROP_Destornillador', sd, [M['amber_grip'], M['tool_steel']], CN, smooth=True, parent=parent))
    return objs


# ----------------------------------------------------------------------------
# 4. Radio militar portatil años 70 (estilo AN/PRC-77 / receptor de campaña)
# ----------------------------------------------------------------------------
def make_field_radio(M, parent):
    body, blk, brs, dial = new_bm(), new_bm(), new_bm(), new_bm()
    # carcasa verde oliva acostada sobre su base trasera (frente hacia arriba/adelante)
    sx, sy, sz = 0.27, 0.22, 0.105
    box(body, (sx, sy, sz), (0, 0, sz / 2), bevel=0.008)
    box(body, (sx + 0.008, 0.032, sz + 0.008), (0, -sy / 2 + 0.02, sz / 2), bevel=0.004)  # bisel frontal
    # asas protectoras metalicas en el panel frontal (-Y) y superior (+Z)
    for ex in (-1, 1):
        tube(brs, [Vector((ex * 0.105, -sy / 2, 0.02)),
                   Vector((ex * 0.105, -sy / 2 - 0.028, 0.025)),
                   Vector((ex * 0.105, -sy / 2 - 0.028, sz - 0.02)),
                   Vector((ex * 0.105, -sy / 2, sz - 0.015))], 0.0045, sides=6)
    # visor de sintonia iluminado tenue + diales de baquelita en la cara superior/frontal
    box(blk, (0.095, 0.042, 0.008), (-0.035, -0.04, sz + 0.002), bevel=0.002)
    box(dial, (0.078, 0.026, 0.005), (-0.035, -0.04, sz + 0.005))
    # perillas rotativas moleteadas
    for (kx, ky, r_) in [(-0.085, 0.035, 0.018), (-0.025, 0.035, 0.018), (0.045, 0.035, 0.014), (0.085, -0.035, 0.016)]:
        cyl(blk, r_, r_ * 0.9, 0.018, (kx, ky, sz + 0.009), (0, 0, 0), sides=14)
        box(brs, (0.003, r_ * 1.5, 0.004), (kx, ky, sz + 0.019), rot=(0, 0, kx * 8))
    # rejilla de parlante
    for kg in range(6):
        box(blk, (0.055, 0.004, 0.004), (0.065, -0.065 + kg * 0.010, sz + 0.003))
    # base de antena flexible + antena latigo plegada/inclinada
    cyl(blk, 0.016, 0.012, 0.038, (-0.105, 0.065, sz + 0.018), (0.2, -0.3, 0), sides=10)
    tube(brs, [Vector((-0.105, 0.065, sz + 0.034)),
               Vector((-0.22, 0.14, sz + 0.10)),
               Vector((-0.38, 0.24, sz + 0.15)),
               Vector((-0.52, 0.31, sz + 0.17))], [0.0045, 0.0035, 0.0025, 0.0018], sides=6)
    # microtelefono militar H-189 apoyado al costado con cable espiralado
    hs_c = Vector((0.20, -0.03, 0.024))
    limb(blk, hs_c + Vector((-0.03, -0.075, 0)), hs_c + Vector((0.03, 0.075, 0.004)), 0.013, 0.013, sides=8, segs=3)
    cyl(blk, 0.026, 0.022, 0.024, hs_c + Vector((-0.032, -0.082, 0.004)), (0.3, 0.2, 0), sides=12)
    cyl(blk, 0.026, 0.022, 0.024, hs_c + Vector((0.032, 0.082, 0.006)), (-0.3, 0.2, 0), sides=12)
    coil_pts = []
    p_a = Vector((0.095, -0.07, sz * 0.6))
    p_b = hs_c + Vector((-0.032, -0.095, 0.004))
    for ic in range(28):
        t = ic / 27
        c_ = p_a.lerp(p_b, t)
        c_.z = max(0.010, c_.z * (1 - t) + 0.012 * t) + math.sin(ic * 1.7) * 0.009
        c_.x += math.cos(ic * 1.7) * 0.009
        coil_pts.append(c_)
    tube(blk, coil_pts, 0.004, sides=5)

    out = new_bm()
    for b, mi in ((body, 0), (blk, 1), (brs, 2), (dial, 3)):
        merge_bm(out, b, None, mi)
    place_local(out, (0.28, -1.10, FLOOR_Z), (0, 0, -0.45))
    return obj_from_bm('PROP_Radio_Campo_1970s', out, [M['olive_metal'], M['bakelite'], M['brass'], M['radio_dial']],
                       CN, smooth=True, parent=parent)


# ----------------------------------------------------------------------------
# 5. Linterna militar en L (Fulton MX-991/U verde oliva) + haz rasante tenue
# ----------------------------------------------------------------------------
def make_l_flashlight(M, parent):
    body, brs, bulb = new_bm(), new_bm(), new_bm()
    # tubo cilindrico acostado en el piso a lo largo de X, cabezal en L apuntando a +Y
    r_tube = 0.023
    z0 = r_tube + 0.002
    cyl(body, r_tube, r_tube, 0.165, (0, 0, z0), (0, math.pi / 2, 0), sides=18)
    # anillos acanalados antideslizantes
    for kx in range(-5, 4):
        cyl(body, r_tube + 0.0018, r_tube + 0.0018, 0.006, (kx * 0.012, 0, z0), (0, math.pi / 2, 0), sides=18)
    # tapa trasera con argolla metalica
    cyl(body, r_tube + 0.003, r_tube + 0.002, 0.024, (-0.090, 0, z0), (0, math.pi / 2, 0), sides=16)
    pts_ring = [Vector((-0.106 - 0.012 * math.sin(a), 0.012 * math.cos(a), z0)) for a in [2 * math.pi * i / 12 for i in range(13)]]
    tube(brs, pts_ring, 0.0022, sides=5, caps=False)
    # caja de interruptor lateral y clip de cinturon
    box(brs, (0.042, 0.014, 0.010), (0.015, -r_tube - 0.004, z0 + 0.006), bevel=0.002)
    box(brs, (0.095, 0.012, 0.003), (-0.015, 0, z0 + r_tube + 0.004))
    # codo en L (90 grados en X = +0.085, proyectando lente hacia +Y)
    sphere(body, r_tube * 1.12, (0.085, 0, z0), seg=14, rings=10)
    cyl(body, 0.028, 0.025, 0.036, (0.085, 0.020, z0), (math.pi / 2, 0, 0), sides=8)  # cuello octogonal antirrolido
    cyl(brs, 0.030, 0.029, 0.016, (0.085, 0.042, z0), (math.pi / 2, 0, 0), sides=20)  # aro metalico del lente
    cyl(bulb, 0.024, 0.024, 0.004, (0.085, 0.048, z0), (math.pi / 2, 0, 0), sides=18) # lente calido encendido tenue

    out = new_bm()
    for b, mi in ((body, 0), (brs, 1), (bulb, 2)):
        merge_bm(out, b, None, mi)
    loc = Vector((0.68, -2.78, FLOOR_Z))
    yaw = 2.38   # apunta directamente hacia la zapatilla Flecha y la libreta en la compuerta
    place_local(out, loc, (0, 0, yaw))
    o = obj_from_bm('PROP_Linterna_Militar_L', out, [M['olive_metal'], M['brass'], M['flash_bulb']], CN, smooth=True, parent=parent)

    # Luz spot rasante de filamento gastado (diegetica, calida y de bajo contraste)
    ld = bpy.data.lights.get('LUZ_Linterna_Piso') or bpy.data.lights.new('LUZ_Linterna_Piso', 'SPOT')
    ld.color = (1.0, 0.78, 0.45)
    ld.energy = 24.0
    ld.spot_size = math.radians(72)
    ld.spot_blend = 0.55
    ld.shadow_soft_size = 0.025
    try:
        ld.volume_factor = 0.45
    except Exception:
        pass
    lo = bpy.data.objects.get('LUZ_Linterna_Piso')
    if lo is None:
        lo = bpy.data.objects.new('LUZ_Linterna_Piso', ld)
        coll(CN).objects.link(lo)
    lens_local = Matrix.Translation(loc) @ rot_matrix((0, 0, yaw)) @ Vector((0.085, 0.056, z0 + 0.006))
    beam_dir = (rot_matrix((0, 0, yaw)) @ Vector((0.0, 1.0, 0.04))).normalized()
    lo.location = lens_local
    lo.rotation_euler = beam_dir.to_track_quat('-Z', 'Y').to_euler()
    lo.parent = parent
    return o


# ----------------------------------------------------------------------------
# 6. Libreta de bolsillo gastada (tapa oscura y esquinas dobladas)
# ----------------------------------------------------------------------------
def make_notebook(M, parent):
    cov, pap, band = new_bm(), new_bm(), new_bm()
    w, l, h = 0.105, 0.155, 0.018
    # contratapa
    box(cov, (w, l, 0.003), (0, 0, 0.002), bevel=0.001)
    # lomo redondeado en -X
    cyl(cov, h * 0.52, h * 0.52, l, (-w / 2 + 0.002, 0, h * 0.52), (math.pi / 2, 0, 0), sides=12)
    # bloque de hojas amarillentas ligeramente abanicadas y esquina doblada
    for kp in range(5):
        zp = 0.005 + kp * 0.0024
        box(pap, (w - 0.008, l - 0.008, 0.0018), (0.002, 0, zp), rot=(0.006 * kp, -0.012 * kp, 0.01 * (kp - 2)))
    # tapa superior ligeramente entreabierta y con esquina doblada (dog-eared)
    nx, ny = 8, 10
    gv = []
    for j in range(ny + 1):
        row = []
        v = j / ny - 0.5
        for i in range(nx + 1):
            u = i / nx - 0.5
            x = u * w
            y = v * l
            z = h + 0.003 + (u + 0.5) * 0.007  # levemente levantada hacia el borde derecho
            # esquina delantera derecha doblada/arrugada hacia arriba
            if u > 0.15 and v < -0.18:
                fold = (u - 0.15) * (-0.18 - v) * 2.8
                z += fold * 0.045
                x -= fold * 0.012
            z += noise.noise(Vector((x * 30, y * 30, 3.1))) * 0.0012
            row.append(cov.verts.new((x, y, z)))
        gv.append(row)
    for j in range(ny):
        for i in range(nx):
            f = cov.faces.new([gv[j][i], gv[j][i + 1], gv[j + 1][i + 1], gv[j + 1][i]])
            f.smooth = True
    bmesh.ops.solidify(cov, geom=cov.faces[:], thickness=0.0022)
    # elastico / cinta gastada cruzando la libreta
    box(band, (0.010, l + 0.003, h + 0.008), (w * 0.24, 0, h * 0.55), bevel=0.001)

    out = new_bm()
    for b, mi in ((cov, 0), (pap, 1), (band, 2)):
        merge_bm(out, b, None, mi)
    place_local(out, (0.22, -2.55, FLOOR_Z), (0, 0, -0.42))
    return obj_from_bm('PROP_Libreta_Bolsillo', out, [M['nb_cover'], M['nb_paper'], M['bakelite']], CN, smooth=True, parent=parent)


# ----------------------------------------------------------------------------
# 7. Zapatilla de lona y goma estilo 'Flecha' años 70 (objeto hero de inspeccion)
# ----------------------------------------------------------------------------
def make_flecha_sneaker(M, parent):
    sole, rub, canv, acc, metal, lace, dark = [new_bm() for _ in range(7)]
    # Perfil de planta de zapatilla a lo largo de Y (-0.135 talon .. +0.145 puntera)
    def half_w(y):
        t = (y + 0.135) / 0.280  # 0 talon -> 1 puntera
        if t < 0.0 or t > 1.0:
            return 0.01
        # talon redondeado, arco levemente entallado, metatarso ancho, puntera conica redondeada
        if t < 0.15:
            return 0.034 * math.sqrt(max(0.05, t / 0.15))
        if t < 0.45:
            return 0.034 - 0.003 * math.sin(math.pi * (t - 0.15) / 0.30)
        if t < 0.72:
            return 0.034 + 0.012 * math.sin(math.pi * (t - 0.45) / 0.54)
        u = (1.0 - t) / 0.28
        return 0.046 * (max(0.02, u) ** 0.58)

    ny = 28
    ys = [-0.135 + 0.280 * i / ny for i in range(ny + 1)]

    # 1) Suela inferior marron caramelo/goma gastada + banda perimetral (foxing) blanco-sucia
    perim_bot, perim_mid, perim_top = [], [], []
    n_ang = 36
    # construir contorno cerrado suave alrededor del zapato
    outline = []
    for k in range(n_ang):
        a = 2 * math.pi * k / n_ang
        y = 0.005 + 0.140 * math.sin(a)
        hw = half_w(y)
        # ligera asimetria anatomica (arco interno en +X)
        asym = -0.004 * math.exp(-((y + 0.01) / 0.05) ** 2)
        x = math.cos(a) * hw + asym
        outline.append((x, y))

    for (x, y) in outline:
        perim_bot.append(sole.verts.new((x * 0.98, y * 0.99, 0.002)))
        perim_mid.append(sole.verts.new((x * 1.02, y * 1.005, 0.011)))
    for k in range(n_ang):
        kn = (k + 1) % n_ang
        sole.faces.new([perim_bot[k], perim_bot[kn], perim_mid[kn], perim_mid[k]])
    sole.faces.new(perim_bot[::-1])
    sole.faces.new(perim_mid)

    # banda de goma blanca sucia (foxing) alrededor de toda la suela + puntera de goma
    rb_b, rb_t, st_b, st_t = [], [], [], []
    for (x, y) in outline:
        rb_b.append(rub.verts.new((x * 1.025, y * 1.008, 0.009)))
        rb_t.append(rub.verts.new((x * 1.01, y * 1.002, 0.027)))
        st_b.append(acc.verts.new((x * 1.030, y * 1.010, 0.021)))
        st_t.append(acc.verts.new((x * 1.026, y * 1.008, 0.0245)))
    for k in range(n_ang):
        kn = (k + 1) % n_ang
        f1 = rub.faces.new([rb_b[k], rb_b[kn], rb_t[kn], rb_t[k]]); f1.smooth = True
        f2 = acc.faces.new([st_b[k], st_b[kn], st_t[kn], st_t[k]]); f2.smooth = True

    # Puntera de goma clasica (y > 0.072)
    nt_u, nt_v = 10, 14
    tc_grid = []
    for i in range(nt_u + 1):
        y = 0.072 + (0.145 - 0.072) * (i / nt_u)
        hw = half_w(y) * 1.01
        ty = (y - 0.072) / (0.145 - 0.072)
        zh = 0.048 * (1.0 - ty ** 1.7) + 0.020
        row = []
        for j in range(nt_v + 1):
            th = math.pi * j / nt_v
            x = math.cos(th) * hw - 0.002
            z = 0.024 + max(0.0, math.sin(th)) * (zh - 0.024)
            row.append(rub.verts.new((x, y, z)))
        tc_grid.append(row)
    for i in range(nt_u):
        for j in range(nt_v):
            f = rub.faces.new([tc_grid[i][j], tc_grid[i + 1][j], tc_grid[i + 1][j + 1], tc_grid[i][j + 1]])
            f.smooth = True

    # Capellada de lona gastada y arrugada (con abertura del cuello del tobillo y abertura de ojales)
    nu_y, nu_a = 18, 22
    ug = []
    for i in range(nu_y + 1):
        y = -0.132 + (0.082 - (-0.132)) * (i / nu_y)
        hw = half_w(y) * 0.99
        asym = -0.004 * math.exp(-((y + 0.01) / 0.05) ** 2)
        # perfil de altura de caña baja
        if y < -0.035:
            z_top = 0.082 + 0.010 * math.exp(-((y + 0.125) / 0.025) ** 2) - 0.010 * math.exp(-((y + 0.075) / 0.035) ** 2)
        else:
            z_top = 0.076 - 0.028 * ((y + 0.035) / 0.117) ** 1.15
        row = []
        for j in range(nu_a + 1):
            # th va desde el borde de lengüeta derecho (0.28) pasando por la suela/talon hasta borde izquierdo (2*pi - 0.28)
            gap = 0.34 if y > -0.045 else 0.52   # abertura mas ancha en el cuello del tobillo
            th = (math.pi * 0.5 + gap) + (2 * math.pi - 2 * gap) * (j / nu_a)
            cx_ = math.cos(th) * hw + asym
            sz_ = (math.sin(th) * 0.5 + 0.5)  # 1 arriba, 0 abajo
            cz_ = 0.023 + sz_ * (z_top - 0.023)
            # hundimiento natural de lona gastada y blanda
            wrinkle = noise.noise(Vector((cx_ * 38, y * 38, cz_ * 38 + 2.1))) * 0.0032
            row.append(canv.verts.new((cx_ + wrinkle * 0.5, y, cz_ + wrinkle)))
        ug.append(row)
    for i in range(nu_y):
        y_mid = -0.132 + (0.082 - (-0.132)) * ((i + 0.5) / nu_y)
        for j in range(nu_a):
            # no cerrar la planta inferior (solo los laterales y talon): descartar caras bien abajo salvo en talon
            z_avg = 0.25 * (ug[i][j].co.z + ug[i][j + 1].co.z + ug[i + 1][j + 1].co.z + ug[i + 1][j].co.z)
            if z_avg < 0.027 and y_mid > -0.115:
                continue
            f = canv.faces.new([ug[i][j], ug[i + 1][j], ug[i + 1][j + 1], ug[i][j + 1]])
            f.smooth = True
    bmesh.ops.solidify(canv, geom=canv.faces[:], thickness=0.0028)

    # Lengüeta de lona caida hacia adentro + interior oscuro
    for kt in range(7):
        yt = -0.045 + kt * 0.020
        zt = 0.068 - kt * 0.0035 + math.sin(kt * 0.9) * 0.002
        box(canv, (0.030, 0.022, 0.0028), (-0.002, yt, zt), rot=(0.22, 0.06, 0))
    sphere(dark, 0.032, (-0.002, -0.075, 0.046), (0.85, 1.45, 0.75), seg=12, rings=8)

    # Detalle iconico chevron 'Flecha' en ambos laterales y parchecito de talon
    for sx in (-1, 1):
        px = sx * 0.037 - 0.002
        box(acc, (0.003, 0.042, 0.009), (px, -0.015, 0.044), rot=(0.32, 0, 0))
        box(acc, (0.003, 0.036, 0.009), (px, -0.015, 0.034), rot=(-0.28, 0, 0))
    box(acc, (0.026, 0.004, 0.014), (-0.002, -0.138, 0.018))

    # 5 pares de ojalillos metalicos + cordones cruzados y punta deshilachada suelta sobre el tablon
    eyelets_l, eyelets_r = [], []
    for ke in range(5):
        ye = -0.030 + ke * 0.022
        ze = 0.073 - ke * 0.0052
        pl = Vector((-0.017, ye, ze))
        pr = Vector((0.013, ye, ze))
        eyelets_l.append(pl); eyelets_r.append(pr)
        for pe in (pl, pr):
            cyl(metal, 0.0042, 0.0042, 0.003, pe, (0, 0.5 * (-1 if pe.x < 0 else 1), 0), sides=10)
    for ke in range(4):
        p1, p2 = eyelets_l[ke], eyelets_r[ke + 1]
        mid1 = p1.lerp(p2, 0.5) + Vector((0, 0, 0.004))
        tube(lace, [p1, mid1, p2], 0.0022, sides=5)
        q1, q2 = eyelets_r[ke], eyelets_l[ke + 1]
        mid2 = q1.lerp(q2, 0.5) + Vector((0, 0, 0.0055))
        tube(lace, [q1, mid2, q2], 0.0022, sides=5)
    # cabos de cordon desatados cayendo sobre el piso de madera
    tube(lace, [eyelets_l[0], Vector((-0.032, -0.042, 0.055)), Vector((-0.052, -0.055, 0.022)),
                Vector((-0.078, -0.040, 0.004)), Vector((-0.105, -0.018, 0.003))], 0.0021, sides=5)
    tube(lace, [eyelets_r[0], Vector((0.028, -0.038, 0.052)), Vector((0.046, -0.048, 0.018)),
                Vector((0.068, -0.065, 0.003))], 0.0021, sides=5)

    out = new_bm()
    for b, mi in ((sole, 0), (rub, 1), (canv, 2), (acc, 3), (metal, 4), (lace, 5), (dark, 6)):
        merge_bm(out, b, None, mi)
    # posicionada en el piso de la caja / compuerta trasera, al costado del cautivo central para inspeccion 3D directa y clara
    place_local(out, (0.42, -2.62, FLOOR_Z), (-0.02, 0.14, -0.65))
    mats = [M['flecha_sole'], M['flecha_rubber'], M['flecha_canvas'], M['flecha_accent'],
            M['rust_iron'], M['flecha_lace'], bpy.data.materials.get('MAT_Interior_Capucha') or M['bakelite']]
    return obj_from_bm('PROP_Zapatilla_Flecha_70s', out, mats, CN, smooth=True, parent=parent)


# ----------------------------------------------------------------------------
# 8. Detalle exterior en el barro inmediato al camion
# ----------------------------------------------------------------------------
def build_exterior_scatter(M, rng):
    import env
    objs = []
    # Cajon militar apoyado y levemente hundido en el barro al costado trasero derecho del camion
    ux, uy = 1.65, -3.75
    wx = env.cx(uy) + ux
    hz, _ = env.terrain_h(ux, uy)
    objs.append(make_crate('PROP_Exterior_Cajon_Barro', (0.62, 0.38, 0.30),
                           (wx, uy, hz - 0.025), (0.05, -0.07, -0.42), 0.06, M, rng, None))

    # Llave oxidada y cuña de madera caidas en el barro junto al cajon exterior
    bw = new_bm()
    wrench_bm(bw, 0.25, 1.05)
    hx2, _ = env.terrain_h(1.28, -3.95)
    place_local(bw, (env.cx(-3.95) + 1.28, -3.95, hx2 + 0.004), (0.04, -0.05, 1.15))
    objs.append(obj_from_bm('PROP_Exterior_Llave_Barro', bw, M['rust_iron'], CN, smooth=True))

    # Cuña de rueda de madera astillada y cantimplora/jarro abollado en el suelo
    b_chock = new_bm()
    hx3, _ = env.terrain_h(-1.25, -3.55)
    box(b_chock, (0.18, 0.26, 0.11), (0, 0, 0.055), rot=(0.22, 0, 0), bevel=0.008)
    place_local(b_chock, (env.cx(-3.55) - 1.25, -3.55, hx3 - 0.015), (0, 0, 0.38))
    objs.append(obj_from_bm('PROP_Exterior_Cuna_Madera', b_chock, M['crate_wood'], CN, smooth=False))

    # Piedras con barro y ramas secas caidas a lo largo del camino inmediato
    b_rocks = new_bm()
    b_twigs = new_bm()
    for _ in range(42):
        ry = rng.uniform(-11.0, 4.0)
        ru = rng.choice([-1, 1]) * rng.uniform(0.35, 3.6)
        if abs(abs(ru) - 0.90) < 0.22:
            continue
        rx = env.cx(ry) + ru
        rh, _ = env.terrain_h(ru, ry)
        rs = rng.uniform(0.025, 0.075)
        ico(b_rocks, rs, (rx, ry, rh + rs * 0.35), (rng.uniform(0.8, 1.4), rng.uniform(0.8, 1.4), rng.uniform(0.45, 0.75)),
            sub=1, rnd=0.32, seed=rng.randint(0, 9999))
    for _ in range(18):
        ry = rng.uniform(-10.0, 2.0)
        ru = rng.choice([-1, 1]) * rng.uniform(1.4, 3.8)
        rx = env.cx(ry) + ru
        rh, _ = env.terrain_h(ru, ry)
        ang = rng.uniform(0, 2 * math.pi)
        ln = rng.uniform(0.35, 0.85)
        p0 = Vector((rx, ry, rh + 0.012))
        p1 = p0 + Vector((math.cos(ang) * ln * 0.5, math.sin(ang) * ln * 0.5, 0.018))
        p2 = p0 + Vector((math.cos(ang + 0.25) * ln, math.sin(ang + 0.25) * ln, 0.008))
        tube(b_twigs, [p0, p1, p2], [0.012, 0.008, 0.004], sides=5)
    objs.append(obj_from_bm('PROP_Exterior_Piedras_Barro', b_rocks, M['flecha_sole'], CN, smooth=True))
    objs.append(obj_from_bm('PROP_Exterior_Ramas_Secas', b_twigs, M['tool_wood'], CN, smooth=False))
    return objs


def build():
    clear_collection(CN)
    rng = random.Random(1978)
    M = prop_mats()
    root = bpy.data.objects.get('TRUCK_Root')
    anchor = bpy.data.objects.new('PROPS_Interior_Anchor', None)
    coll(CN).objects.link(anchor)
    anchor.parent = root

    # Mantas de lana en la caja
    make_crumpled_blanket('PROP_Manta_Arrugada_Trasera', (-0.48, -2.50, FLOOR_Z), 0.35, 0.62, 0.58, 0.085, 11, M['blanket'], anchor)
    make_crumpled_blanket('PROP_Manta_Arrugada_Centro', (0.04, -1.78, FLOOR_Z), -0.60, 0.68, 0.55, 0.075, 23, M['blanket'], anchor)
    make_folded_blanket('PROP_Manta_Doblada_Frente', (-0.44, 0.20, FLOOR_Z), 0.18, M['blanket'], anchor)

    # Cajones de municion y herramientas en la caja
    make_crate('PROP_Cajon_Municion_1', (0.64, 0.38, 0.30), (0.24, 0.20, FLOOR_Z), (0, 0, 0.20), 0.0, M, rng, anchor)
    make_crate('PROP_Cajon_Herramientas_2', (0.52, 0.32, 0.25), (-0.34, -0.26, FLOOR_Z), (0, 0, -0.34), 0.09, M, rng, anchor)

    # Herramientas sueltas, radio años 70, linterna en L, libreta y zapatilla Flecha
    make_tools(M, anchor)
    make_field_radio(M, anchor)
    make_l_flashlight(M, anchor)
    make_notebook(M, anchor)
    make_flecha_sneaker(M, anchor)

    # Props de suelo exterior
    build_exterior_scatter(M, rng)
    return 'ok'

