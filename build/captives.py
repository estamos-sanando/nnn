"""Cinco cautivos encapuchados (capucha de arpilleria), manos atadas, posturas agotadas."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Euler, noise
from common import *

CN = 'Cautivos'
FLOOR_Z = 1.25


# ----------------------------------------------------------------------------
# Materiales
# ----------------------------------------------------------------------------
def burlap_mat():
    mb = MB('MAT_Arpillera_Capucha')
    vec = mb.tc('Object')
    # trama de arpillera: dos ondas cruzadas + fibras
    wx_ = mb.wave(260.0, 0.35, 0.0, vec=vec, direction='X', profile='SIN')
    wz_ = mb.wave(260.0, 0.35, 0.0, vec=vec, direction='Z', profile='SIN')
    wy_ = mb.wave(260.0, 0.35, 0.0, vec=vec, direction='Y', profile='SIN')
    weave = mb.math('ADD', mb.math('MULTIPLY', wx_, wz_), mb.math('MULTIPLY', wy_, wz_))
    fib = mb.noise(380.0, 3, 0.6)
    lump = mb.noise(7.0, 6, 0.6)
    c1, c2 = srgb('#3b2c1b'), srgb('#6a5334')
    col = mb.mixc(mb.ramp(lump, [(0.3, (0, 0, 0, 1)), (0.7, (1, 1, 1, 1))]), c1, c2)
    col = mb.mixc(mb.maprange(weave, 0.1, 0.9, 0.55, 0.0), col, (0.01, 0.007, 0.004, 1))
    col = mb.mixc(mb.maprange(mb.noise(3.0, 5, 0.6), 0.4, 0.8, 0.0, 0.7), col, srgb('#17110a'))   # mugre
    h = mb.math('ADD', mb.math('MULTIPLY', weave, 0.6), mb.math('MULTIPLY', fib, 0.5))
    mb.set(Base_Color=col, Roughness=0.97, Normal=mb.bump(h, 1.2, 0.004))
    try:
        mb.set(Sheen_Weight=0.2)
    except Exception:
        pass
    mb.m.use_backface_culling = False
    return mb.done()


def skin_mat():
    mb = MB('MAT_Piel_Sucia')
    n = mb.noise(30.0, 4, 0.5)
    col = mb.mixc(mb.noise(4, 4, 0.5), srgb('#8a6a52'), srgb('#6e5240'))
    col = mb.mixc(mb.maprange(n, 0.4, 0.8, 0.0, 0.6), col, srgb('#2c2016'))
    mb.set(Base_Color=col, Roughness=0.6, Subsurface_Weight=0.15, Normal=mb.bump(n, 0.3, 0.003))
    return mb.done()


def leather_mat(name='MAT_Cuero_Gastado', c1='#1a120c', c2='#33261b'):
    return weathered(name, srgb(c1), srgb(c2), rough=0.55, metal=0.0, scale=10.0, mud_h=0.12, mud=0.7, bump=0.5, grime=0.5)


def black_inner():
    mb = MB('MAT_Interior_Capucha')
    mb.set(Base_Color=(0.0, 0.0, 0.0, 1), Roughness=1.0)
    return mb.done()


def thread_mat():
    mb = MB('MAT_Hilo_Costura')
    n = mb.noise(40.0, 3, 0.5)
    mb.set(Base_Color=mb.mixc(n, srgb('#140e08'), srgb('#7a6644')), Roughness=0.92)
    return mb.done()


def belt_buckle_mat():
    return weathered('MAT_Hebilla_Metal', srgb('#3b3730'), srgb('#666055'), rough=0.42, metal=0.9, rust=0.25, scale=8.0)


# ----------------------------------------------------------------------------
# Utilidades de cuerpo
# ----------------------------------------------------------------------------
def torus_ring(bm, center, d, w, h, r, up_hint=(1, 0, 0), major=24, minor=6, mat_index=0):
    """toroide elíptico alrededor del eje d (para sogas atadas)"""
    right, up, dn = basis_from_dir(Vector(d), Vector(up_hint))
    vs = []
    for i in range(major):
        a = 2 * math.pi * i / major
        pc = Vector(center) + right * math.cos(a) * w + up * math.sin(a) * h
        radial = (right * math.cos(a) * h + up * math.sin(a) * w).normalized()
        ring = []
        for j in range(minor):
            b = 2 * math.pi * j / minor
            ring.append(bm.verts.new(pc + radial * math.cos(b) * r + dn * math.sin(b) * r))
        vs.append(ring)
    for i in range(major):
        A, B = vs[i], vs[(i + 1) % major]
        for j in range(minor):
            try:
                f = bm.faces.new([A[j], B[j], B[(j + 1) % minor], A[(j + 1) % minor]])
                f.smooth = True
                f.material_index = mat_index
            except ValueError:
                pass


def recalc(bm):
    try:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    except Exception:
        pass


def rotY(a):
    return Matrix.Rotation(a, 3, 'Y')


def rotX(a):
    return Matrix.Rotation(a, 3, 'X')


def spherep(bm, p, r, scale=(1, 1, 1), seg=10, rings=6):
    sphere(bm, r, p, scale, seg=seg, rings=rings)


# ----------------------------------------------------------------------------
# Un cautivo
# ----------------------------------------------------------------------------
def make_captive(name, origin, yaw, cfg, M, rng, parent):
    """cfg: lean, bow, roll, thigh (l,r dirs), shin (l,r dirs), foot phi (l,r), shirt, trousers, rolled, sock_left,
    shivers"""
    lean = cfg.get('lean', 0.3)
    bow = cfg.get('bow', 0.4)
    roll = cfg.get('roll', 0.0)
    rolled = cfg.get('rolled', False)

    shirt, trou, skin, shoe, hood, rope, dark, thread = [new_bm() for _ in range(8)]
    P0 = Vector((0, 0, 0.12))
    u = Vector((math.sin(lean), 0, math.cos(lean)))          # eje del torso
    f = Vector((math.cos(lean), 0, -math.sin(lean)))         # adelante del torso
    Y = Vector((0, 1, 0))

    # ---------------- torso ----------------
    spine = [(0.0, 0.17, 0.105), (0.10, 0.155, 0.10), (0.24, 0.175, 0.115), (0.38, 0.195, 0.12),
             (0.47, 0.20, 0.10), (0.53, 0.12, 0.07), (0.57, 0.055, 0.055)]
    rings = []
    for t, w, h in spine:
        # leve encorvado: la columna se curva hacia adelante en la parte alta
        curve = f * (0.07 * (t / 0.55) ** 2) * (1 if lean > -0.5 else 0)
        rings.append((P0 + u * t + curve, u, w, h, 16, Vector((1, 0, 0))))
    loft(shirt, rings, mat_index=0)
    # hombros
    N = P0 + u * 0.50 + f * 0.05
    sh = {}
    for sgn in (-1, 1):
        S = N + Y * sgn * 0.205 + Vector((0, 0, -0.02))
        sh[sgn] = S
        spherep(shirt, S, 0.065, (1.0, 1.0, 1.0))

    # cuello de camisa arrugado y tapeta frontal
    torus_ring(shirt, P0 + u * 0.53 + f * 0.055, u, 0.095, 0.088, 0.018, up_hint=(1, 0, 0), major=18, minor=5)
    if rolled:
        for bt in (0.20, 0.29, 0.38, 0.46):
            p_pl = P0 + u * bt + f * (0.118 + 0.07 * (bt / 0.55) ** 2)
            box(shirt, (0.008, 0.032, 0.07), p_pl, rot=(0, -lean, 0))
            spherep(dark, p_pl + f * 0.006, 0.006, seg=6, rings=4)

    # ---------------- brazos atados a la espalda ----------------
    wr, el = {}, {}
    for sgn in (-1, 1):
        S = sh[sgn]
        W = P0 + u * 0.15 - f * 0.165 + Y * sgn * 0.046
        def fit(A, B, Lc, hint):
            d = B - A
            dist = min(d.length, Lc * 2 - 0.01)
            h = math.sqrt(max(Lc * Lc - (dist / 2) ** 2, 0.0))
            return A + d.normalized() * (dist / 2) + hint.normalized() * h
        E = fit(S, W, 0.28, -f * 0.65 + Y * sgn * 0.78 - u * 0.08)
        el[sgn], wr[sgn] = E, W
        # manga / brazo
        limb(shirt, S, E, 0.060, 0.049, sides=10, segs=3, mat_index=0)
        spherep(shirt, E, 0.051)
        if rolled:
            # manga arremangada: doble vuelta gruesa bajo el codo y antebrazo desnudo
            Ecuff = E + (W - E) * 0.26
            limb(shirt, E, Ecuff, 0.052, 0.058, sides=10, segs=2, mat_index=0)
            torus_ring(shirt, Ecuff, (W - E), 0.055, 0.055, 0.017, up_hint=(0, 0, 1), major=16, minor=6)
            torus_ring(shirt, Ecuff - (W - E).normalized() * 0.022, (W - E), 0.054, 0.054, 0.014, up_hint=(0, 0, 1), major=16, minor=5)
            limb(skin, Ecuff, W, 0.041, 0.031, sides=10, segs=3)
        else:
            limb(shirt, E, W + (E - W).normalized() * 0.02, 0.049, 0.037, sides=10, segs=3, mat_index=0)
        # mano crispada y dedos cerrados tras la espalda
        hdir = (W - E).normalized()
        palm = W + hdir * 0.045 - u * 0.01
        spherep(skin, palm, 0.038, (0.85, 0.72, 1.15), seg=10, rings=6)
        for fd_i in range(4):
            fp = palm + hdir * 0.028 + Y * (sgn * (-0.012 + fd_i * 0.008)) - f * 0.008
            spherep(skin, fp, 0.011, (1.4, 0.8, 0.9), seg=6, rings=4)
    # soga gruesa atando AMBAS muñecas juntas (bobina eliptica + cruce en ocho + nudo)
    wm = (wr[-1] + wr[1]) * 0.5
    arm_ax = ((wr[-1] - el[-1]).normalized() + (wr[1] - el[1]).normalized()).normalized()
    if arm_ax.length < 0.1:
        arm_ax = -u
    for k in range(5):
        off_c = wm + arm_ax * (-0.018 + k * 0.010)
        # eje d = arm_ax, up_hint = f -> right = Y (abarca ambas muñecas: 0.082m), up = f (0.040m)
        torus_ring(rope, off_c, arm_ax, 0.082 + 0.002 * (k % 2), 0.040, 0.0095, up_hint=f, major=22, minor=6)
    # vueltas individuales y cruce entre muñecas
    for sgn in (-1, 1):
        torus_ring(rope, wr[sgn], wr[sgn] - el[sgn], 0.036, 0.036, 0.0085, up_hint=f, major=14, minor=5)
    tube(rope, [wr[-1] - f * 0.032, wm + arm_ax * 0.01, wr[1] + f * 0.030], 0.0085, sides=5)
    tube(rope, [wr[-1] + f * 0.030, wm - arm_ax * 0.01, wr[1] - f * 0.032], 0.0085, sides=5)
    # nudo y colas colgando
    knot = wm - f * 0.042
    spherep(rope, knot, 0.021, seg=8, rings=6)
    tube(rope, [knot, knot + Vector((-0.03 * f.x, 0.025, -0.08)), knot + Vector((-0.02 * f.x, 0.045, -0.17))], 0.0075, sides=5)
    tube(rope, [knot, knot + Vector((-0.03 * f.x, -0.03, -0.07)), knot + Vector((-0.05 * f.x, -0.055, -0.14))], 0.0075, sides=5)

    # ---------------- piernas ----------------
    shoe_info = []
    for sgn, key in ((1, 'l'), (-1, 'r')):
        hip = P0 + Vector((0.0, sgn * 0.095, -0.02))
        td = Vector(cfg['thigh_' + key]).normalized()
        sd = Vector(cfg['shin_' + key]).normalized()
        knee = hip + td * 0.46
        ankle = knee + sd * 0.43
        limb(trou, hip, knee, 0.088, 0.066, sides=10, segs=3, bulge=0.004)
        spherep(trou, hip, 0.09)
        spherep(trou, knee, 0.068)
        limb(trou, knee, ankle, 0.062, 0.046, sides=10, segs=3)
        phi = cfg['foot_' + key]
        fd = Vector((math.cos(phi), 0, math.sin(phi)))
        # pie
        toe = ankle + fd * 0.215 + Vector((0, 0, -0.045))
        heel = ankle + Vector((-0.045, 0, -0.045)) * 1
        bare = (cfg.get('sock_' + key, False))
        shoe_info.append((ankle, toe, fd, bare, sgn))
        tgt = skin if bare else shoe
        mi = 0
        foot_rings = [(heel, fd, 0.043, 0.050, 10), (heel * 0.6 + toe * 0.4, fd, 0.047, 0.056, 10),
                      (heel * 0.3 + toe * 0.7, fd, 0.049, 0.040, 10), (toe, fd, 0.042, 0.028, 10)]
        # direccion de la serie: tangente del pie
        d_ = (toe - heel)
        rr = [(heel + Vector((0, sgn * 0.0, 0.015)), d_, 0.044, 0.052, 10, Vector((0, 0, 1))),
              (heel + d_ * 0.35 + Vector((0, 0, 0.02)), d_, 0.048, 0.055, 10, Vector((0, 0, 1))),
              (heel + d_ * 0.72 + Vector((0, 0, 0.005)), d_, 0.050, 0.038, 10, Vector((0, 0, 1))),
              (toe, d_, 0.040, 0.026, 10, Vector((0, 0, 1)))]
        loft(tgt, [(Vector(a) + Vector((0, sgn * 0.0, 0)), b, c_, d2, e, g) for (a, b, c_, d2, e, g) in rr], mat_index=0)
        if not bare:
            # suela
            box(dark, (0.30, 0.095, 0.014), ankle + fd * 0.10 + Vector((0, 0, -0.085)), rot=(0, -phi, 0), bevel=0.004)

    # ---------------- cinturon con hebilla y presillas ----------------
    belt_c = P0 + u * 0.112
    torus_ring(shoe, belt_c, u, 0.162, 0.109, 0.014, up_hint=(1, 0, 0), major=24, minor=5)
    buckle_p = belt_c + f * 0.116
    box(thread, (0.014, 0.048, 0.038), buckle_p, rot=(0, -lean, 0), bevel=0.003)
    box(dark, (0.016, 0.028, 0.022), buckle_p + f * 0.002, rot=(0, -lean, 0))
    for sgn in (-1, 1):
        box(trou, (0.016, 0.014, 0.042), belt_c + Y * (sgn * 0.11) + f * 0.075, rot=(0, -lean, 0))

    # ---------------- capucha ----------------
    Rh = rotY(lean + bow) @ rotX(roll)
    # centro de la cabeza: sobre el cuello, inclinado hacia adelante
    neck_base = P0 + u * 0.57 + f * 0.06
    ax = Rh @ Vector((0, 0, 1))
    fw = Rh @ Vector((1, 0, 0))
    Hc = neck_base + ax * 0.13 + fw * 0.02
    tube(skin, [neck_base - u * 0.03, neck_base + ax * 0.06], 0.045, sides=8)
    prof = [(0.150, 0.012, 0.012), (0.138, 0.060, 0.070), (0.115, 0.095, 0.110), (0.075, 0.108, 0.125), (0.035, 0.112, 0.127),
            (0.0, 0.110, 0.126), (-0.04, 0.104, 0.119), (-0.075, 0.093, 0.104), (-0.105, 0.080, 0.090), (-0.125, 0.074, 0.083),
            (-0.15, 0.080, 0.090), (-0.18, 0.115, 0.108), (-0.215, 0.158, 0.130), (-0.25, 0.198, 0.150), (-0.285, 0.215, 0.165)]
    sides = 32
    hring = []
    for (t, w, h) in prof:
        wob = 1.0 + 0.04 * (noise.noise(Vector((t * 9, 0.3, 2.0))))
        c = Hc + ax * t
        if t < -0.15:
            c = c + (-ax * 0.0) + fw * (-0.01)
        hring.append((c, ax, w * wob * 1.03, h * wob * 1.03, sides, fw))
    rings = loft(hood, hring, mat_index=0, caps=(True, False))
    # cabeza interior oscura (se ve a traves de los orificios)
    spherep(dark, Hc + fw * 0.005, 0.1, (1.15, 1.0, 1.25), seg=14, rings=10)
    # deformar: arrugas + ondas de caida de la tela
    off = Vector((rng.uniform(0, 50), 3.0, 8.0))
    for v in hood.verts:
        v.co += Vector((noise.noise((v.co + off) * 9.0), noise.noise((v.co + off) * 9.0 + Vector((7, 0, 0))),
                        noise.noise((v.co + off) * 9.0 + Vector((0, 7, 0))))) * 0.006
    # punta del saco arriba (pliegue caido)
    tip_idx = rings[0]
    for v in tip_idx:
        v.co += fw * 0.045 - ax * 0.035
    # Orejas/esquinas plegadas de bolsa de arpillera (como en la referencia)
    lr_ax = Rh @ Vector((0, 1, 0))
    for v in hood.verts:
        rel = v.co - Hc
        up_proj = rel.dot(ax)
        lr_proj = rel.dot(lr_ax)
        if up_proj > 0.07 and abs(lr_proj) > 0.038:
            sgn = 1.0 if lr_proj > 0 else -1.0
            v.co += lr_ax * (0.024 * sgn) + ax * 0.026
    # ojos cortados toscamente a cuchillo/tijera: aberturas oscuras irregulares + hebras sueltas
    eye_w = []
    for sgn in (-1, 1):
        ep = Hc + fw * 0.118 + Rh @ Vector((0, sgn * 0.037, 0.018))
        eye_w.append((ep, sgn))
    to_del = []
    for fcs in hood.faces:
        c = fcs.calc_center_median()
        for ep, _sgn in eye_w:
            d = c - ep
            dd = math.sqrt((d.dot(Rh @ Vector((0, 1, 0))) / 1.75) ** 2 + (d.dot(ax) / 0.95) ** 2 + (d.dot(fw) * 0.35) ** 2)
            if dd < rng.uniform(0.019, 0.029):
                to_del.append(fcs)
                break
    bmesh.ops.delete(hood, geom=list(set(to_del)), context='FACES')
    # hebras deshilachadas alrededor de los cortes de los ojos
    lr_ax = Rh @ Vector((0, 1, 0))
    for ep, sgn in eye_w:
        for kf in range(7):
            ang = 2 * math.pi * kf / 7 + rng.uniform(-0.3, 0.3)
            p_st = ep + lr_ax * (math.cos(ang) * 0.024) + ax * (math.sin(ang) * 0.013) + fw * 0.004
            p_en = p_st + lr_ax * rng.uniform(-0.008, 0.008) - ax * rng.uniform(0.008, 0.020) + fw * 0.005
            tube(hood, [p_st, p_en], 0.0014, sides=3, caps=False)
    # borde inferior deshilachado
    rim_idx = rings[-1]
    for v in rim_idx:
        v.co += Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) * 0.012 - ax * rng.uniform(0, 0.03)
    for v in rim_idx:
        if rng.random() < 0.45:
            d0 = v.co.copy()
            ln = rng.uniform(0.03, 0.085)
            tube(hood, [d0, d0 - ax * ln * 0.5 + Vector((rng.uniform(-0.01, 0.01), rng.uniform(-0.01, 0.01), -0.01)), d0 - ax * ln + Vector((rng.uniform(-0.02, 0.02), rng.uniform(-0.02, 0.02), -0.02))], 0.0016, sides=3, caps=False)
    # soga en el cuello + nudo + colas
    nc = Hc + ax * -0.125
    torus_ring(rope, nc, ax, 0.083, 0.094, 0.0105, up_hint=fw, major=26, minor=6)
    torus_ring(rope, nc - ax * 0.012, ax, 0.085, 0.096, 0.0085, up_hint=fw, major=24, minor=5)
    kp = nc + fw * 0.097 + lr_ax * 0.018
    spherep(rope, kp, 0.019, seg=8, rings=5)
    tube(rope, [kp, kp + fw * 0.02 + Vector((0.0, 0.02, -0.06)), kp + Vector((0.03, 0.035, -0.13))], 0.007, sides=5)
    tube(rope, [kp, kp + fw * 0.01 + Vector((0.0, -0.025, -0.05)), kp + Vector((0.02, -0.05, -0.115))], 0.007, sides=5)
    # costuras visibles en ambos laterales del saco, corona superior y zurcido frontal
    for seam_i in (1, sides // 2 - 1, sides // 2 + 1, sides - 1):
        for rg in rings[1:12]:
            v = rg[seam_i % sides]
            base = v.co.copy()
            n_ = (base - Hc).normalized()
            tube(thread, [base + n_ * 0.001 - ax * 0.006, base + n_ * 0.004 + lr_ax * 0.006, base + n_ * 0.001 + ax * 0.006], 0.0022, sides=4)
    # zurcido tosco diagonal en el frente/mejilla de la capucha
    mend_c = Hc + fw * 0.116 + lr_ax * (-0.042 if rng.random() < 0.6 else 0.042) - ax * 0.032
    for km in range(6):
        mp0 = mend_c + ax * (km * 0.011 - 0.025) + lr_ax * (km * 0.004)
        tube(thread, [mp0 - lr_ax * 0.010 + fw * 0.002, mp0 + fw * 0.006, mp0 + lr_ax * 0.010 + fw * 0.002], 0.0022, sides=4)
    for rg in [rings[1], rings[2]]:
        for k in range(0, sides, 2):
            v = rg[k]
            n_ = (v.co - Hc).normalized()
            box(thread, (0.008, 0.0035, 0.0035), v.co + n_ * 0.002)

    # ---------------- ensamblar ----------------
    out = new_bm()
    parts = [(shirt, 0), (trou, 1), (skin, 2), (shoe, 3), (hood, 4), (rope, 5), (dark, 6), (thread, 7)]
    # pliegues en la ropa
    for b, mi in parts[:2]:
        noise_displace(b, 18.0, 0.0045, seed=rng.randint(0, 99))
    for b, mi in parts:
        recalc(b) if mi not in (4,) else None
        merge_bm(out, b, None, mi)
    M_ = Matrix.Translation(origin) @ Matrix.Rotation(yaw, 4, 'Z')
    xf(out, M_)
    mats = [cfg['shirt_mat'], cfg['trousers_mat'], M['skin'], cfg['shoe_mat'], M['hood'], M['rope'], M['dark'], M['thread']]
    o = obj_from_bm(name, out, mats, CN, smooth=True, parent=parent)
    return o


def build():
    clear_collection(CN)
    rng = random.Random(1977)
    root = bpy.data.objects.get('TRUCK_Root')
    anchor = bpy.data.objects.new('CAUTIVOS_Anchor', None)
    coll(CN).objects.link(anchor)
    anchor.parent = root
    M = {'skin': skin_mat(), 'hood': burlap_mat(), 'rope': bpy.data.materials.get('MAT_Soga') or None,
         'dark': black_inner(), 'thread': thread_mat()}
    if M['rope'] is None:
        import truck
        M['rope'] = truck.rope_mat('MAT_Soga')
    shoe_dark = leather_mat('MAT_Zapato_Cuero', '#120c08', '#2a1e14')
    shoe_brown = leather_mat('MAT_Zapato_Marron', '#2a1a0e', '#4a3320')
    cm = lambda n, a, b, **k: cloth_mat(n, srgb(a), srgb(b), rough=0.92, weave=120.0, scale=5.0, bump=0.8, dirt=0.65, mud_h=0.0, **k)
    shirt_central = cloth_mat('MAT_Camisa_Crema', srgb('#b7ae92'), srgb('#9a9078'), rough=0.9, weave=140.0, scale=5.0, bump=0.8,
                              dirt=0.8, sheen=0.2, seed=11)
    trou_dark = cm('MAT_Pantalon_Oscuro', '#1d1c1b', '#2a2724', seed=12)
    sw_blue = cm('MAT_Pulover_Gris', '#4a5560', '#3a434c', seed=13)
    trou_brown = cm('MAT_Pantalon_Marron', '#3b2e22', '#2a2018', seed=14)
    sh_beige = cm('MAT_Camisa_Beige', '#8a7a5e', '#6e6048', seed=15)
    trou_navy = cm('MAT_Pantalon_Azul', '#1c2230', '#272e3f', seed=16)
    sw_green = cm('MAT_Pulover_Verde', '#2f3a2c', '#233020', seed=17)
    jeans = cm('MAT_Jean_Gastado', '#2c3646', '#3a475a', seed=18)
    sh_vest = cm('MAT_Camiseta_Sucia', '#b8b09a', '#968e78', seed=19)
    trou_grey = cm('MAT_Pantalon_Gris', '#4a4742', '#38362f', seed=20)

    DIR = lambda x, y, z: Vector((x, y, z))
    cfgs = []
    # 0: central, sentado justo en el borde de la compuerta abierta, piernas colgando, mira hacia atras (-Y)
    c0 = dict(lean=0.40, bow=0.46, roll=0.07, rolled=True,
              thigh_l=DIR(1.0, 0.17, -0.02), thigh_r=DIR(1.0, -0.18, -0.05),
              shin_l=DIR(0.08, 0.03, -1.0), shin_r=DIR(-0.04, -0.04, -1.0),
              foot_l=-0.52, foot_r=-0.72,
              shirt_mat=shirt_central, trousers_mat=trou_dark, shoe_mat=shoe_dark)
    cfgs.append(('CAUTIVO_Central', Vector((0.02, -2.90, FLOOR_Z)), -math.pi / 2 + 0.14, c0))
    # 1: pared izquierda, atras, piernas extendidas
    c1 = dict(lean=-0.05, bow=0.62, roll=-0.12, rolled=False,
              thigh_l=DIR(0.97, 0.22, 0.02), thigh_r=DIR(0.96, -0.1, 0.08),
              shin_l=DIR(0.96, 0.16, 0.18), shin_r=DIR(0.95, -0.12, 0.28),
              foot_l=0.35, foot_r=0.55,
              shirt_mat=sw_blue, trousers_mat=trou_brown, shoe_mat=shoe_brown)
    cfgs.append(('CAUTIVO_Fondo_1', Vector((-0.74, -2.00, FLOOR_Z)), 0.0, c1))
    # 2: pared izquierda, rodillas flexionadas, encorvado
    c2 = dict(lean=0.42, bow=0.45, roll=0.1, rolled=False,
              thigh_l=DIR(0.62, 0.18, 0.78), thigh_r=DIR(0.60, -0.08, 0.80),
              shin_l=DIR(0.35, 0.08, -0.93), shin_r=DIR(0.45, -0.1, -0.88),
              foot_l=0.05, foot_r=0.1, sock_r=True,
              shirt_mat=sh_beige, trousers_mat=trou_navy, shoe_mat=shoe_dark)
    cfgs.append(('CAUTIVO_Fondo_2', Vector((-0.72, -0.85, FLOOR_Z)), 0.0, c2))
    # 3: pared derecha, tembloroso, piernas extendidas
    c3 = dict(lean=0.0, bow=0.5, roll=0.22, rolled=False,
              thigh_l=DIR(0.98, 0.1, 0.03), thigh_r=DIR(0.95, -0.28, 0.02),
              shin_l=DIR(0.94, 0.14, 0.3), shin_r=DIR(0.9, -0.3, 0.3),
              foot_l=0.6, foot_r=0.35,
              shirt_mat=sw_green, trousers_mat=jeans, shoe_mat=shoe_brown)
    cfgs.append(('CAUTIVO_Fondo_3', Vector((0.74, -1.55, FLOOR_Z)), math.pi, c3))
    # 4: pared derecha, una pierna flexionada
    c4 = dict(lean=0.18, bow=0.7, roll=-0.18, rolled=False,
              thigh_l=DIR(0.96, 0.2, 0.04), thigh_r=DIR(0.60, -0.2, 0.77),
              shin_l=DIR(0.95, 0.2, 0.2), shin_r=DIR(0.42, -0.1, -0.9),
              foot_l=0.5, foot_r=0.05, sock_l=True,
              shirt_mat=sh_vest, trousers_mat=trou_grey, shoe_mat=shoe_dark)
    cfgs.append(('CAUTIVO_Fondo_4', Vector((0.73, -0.2, FLOOR_Z)), math.pi, c4))
    for (name, org, yaw, cfg) in cfgs:
        make_captive(name, org, yaw, cfg, M, rng, anchor)
    return 'ok'

