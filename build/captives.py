"""Cinco cautivos encapuchados (capucha de arpillera), manos atadas, posturas humanas organicas realistas.
Elimina por completo las esferas de articulacion visibles (munecos de madera) y crea siluetas anatomicas continuas
con pliegues de ropa civil de los anos 70, capuchas de arpillera con orejas dobladas y sogas de canamo ajustadas.
"""
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
    wx_ = mb.wave(260.0, 0.35, 0.0, vec=vec, direction='X', profile='SIN')
    wz_ = mb.wave(260.0, 0.35, 0.0, vec=vec, direction='Z', profile='SIN')
    wy_ = mb.wave(260.0, 0.35, 0.0, vec=vec, direction='Y', profile='SIN')
    weave = mb.math('ADD', mb.math('MULTIPLY', wx_, wz_), mb.math('MULTIPLY', wy_, wz_))
    fib = mb.noise(380.0, 3, 0.6)
    lump = mb.noise(7.0, 6, 0.6)
    c1, c2 = srgb('#3b2c1b'), srgb('#6a5334')
    col = mb.mixc(mb.ramp(lump, [(0.3, (0, 0, 0, 1)), (0.7, (1, 1, 1, 1))]), c1, c2)
    col = mb.mixc(mb.maprange(weave, 0.1, 0.9, 0.55, 0.0), col, (0.01, 0.007, 0.004, 1))
    col = mb.mixc(mb.maprange(mb.noise(3.0, 5, 0.6), 0.4, 0.8, 0.0, 0.7), col, srgb('#17110a'))
    h = mb.math('ADD', mb.math('MULTIPLY', weave, 0.6), mb.math('MULTIPLY', fib, 0.5))
    mb.set(Base_Color=col, Roughness=0.98, Normal=mb.bump(h, 1.2, 0.004))
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


def smooth_organic_shoe(bm, dark_bm, heel_pos, toe_pos, tangent, sgn, mi=0):
    """Zapato o bota realista civil de los años 70: puntera redondeada, empeine y suela de caucho"""
    p0 = Vector(heel_pos)
    p1 = Vector(toe_pos)
    d = (p1 - p0).normalized()
    L = (p1 - p0).length
    right, up, _ = basis_from_dir(d, Vector((0, 0, 1)))
    
    # 5 anillos anatómicos del calzado
    rings = [
        (p0 + Vector((0, 0, 0.015)), d, 0.044, 0.052, 14, up),
        (p0 + d * (L * 0.35) + Vector((0, 0, 0.022)), d, 0.048, 0.048, 14, up),
        (p0 + d * (L * 0.70) + Vector((0, 0, 0.010)), d, 0.050, 0.038, 14, up),
        (p0 + d * (L * 0.90) + Vector((0, 0, 0.002)), d, 0.044, 0.028, 14, up),
        (p1, d, 0.032, 0.018, 14, up)
    ]
    loft(bm, rings, mat_index=mi, caps=(True, True))
    
    # Suela de caucho vulcanizado redondeada (sigue el contorno del pie)
    sole_pts = [p0 - up * 0.032, p0 + d * (L * 0.5) - up * 0.032, p1 - up * 0.032]
    tube(dark_bm, sole_pts, [0.048, 0.050, 0.038], sides=12, caps=True, mat_index=0)


# ----------------------------------------------------------------------------
# Un cautivo orgánico
# ----------------------------------------------------------------------------
def make_captive(name, origin, yaw, cfg, M, rng, parent):
    lean = cfg.get('lean', 0.3)
    bow = cfg.get('bow', 0.4)
    roll = cfg.get('roll', 0.0)
    rolled = cfg.get('rolled', False)

    shirt, trou, skin, shoe, hood, rope, dark, thread = [new_bm() for _ in range(8)]
    P0 = Vector((0, 0, 0.12))
    u = Vector((math.sin(lean), 0, math.cos(lean)))          # eje del torso
    f = Vector((math.cos(lean), 0, -math.sin(lean)))         # adelante del torso
    Y = Vector((0, 1, 0))

    # ---------------- 1. Torso Humano Continuo (Hombros Caidos Naturales) ----------------
    # 9 anillos que construyen pelvis, cintura, caja toracica, pectorales y hombros continuos
    spine = [
        (0.00, 0.180, 0.115),   # pelvis / cadera
        (0.09, 0.165, 0.105),   # cintura
        (0.20, 0.178, 0.115),   # abdomen inferior
        (0.32, 0.198, 0.122),   # costillas / torax
        (0.42, 0.215, 0.125),   # pecho / pectorales
        (0.50, 0.235, 0.118),   # hombros anchos caidos (sin esferas separadas)
        (0.56, 0.155, 0.095),   # clavicula / base de cuello
        (0.61, 0.082, 0.075),   # cuello medio
        (0.65, 0.065, 0.062)    # cuello superior
    ]
    rings = []
    for t, w, h in spine:
        curve = f * (0.075 * (t / 0.65) ** 2) * (1 if lean > -0.5 else 0)
        rings.append((P0 + u * t + curve, u, w, h, 18, Vector((1, 0, 0))))
    loft(shirt, rings, mat_index=0)

    # Cuello de camisa y tapeta
    neck_center = P0 + u * 0.58 + f * 0.06
    torus_ring(shirt, neck_center, u, 0.095, 0.088, 0.018, up_hint=(1, 0, 0), major=20, minor=6)
    if rolled:
        for bt in (0.22, 0.32, 0.42):
            p_pl = P0 + u * bt + f * (0.125 + 0.07 * (bt / 0.65) ** 2)
            box(shirt, (0.010, 0.034, 0.07), p_pl, rot=(0, -lean, 0))

    # ---------------- 2. Brazos y Mangas Continuas (Sin Bolas de Articulacion) ----------------
    wr, el = {}, {}
    for sgn in (-1, 1):
        # Origen del hombro que nace de la carne del torso superior
        S = P0 + u * 0.50 + f * 0.02 + Y * (sgn * 0.220)
        W = P0 + u * 0.14 - f * 0.165 + Y * (sgn * 0.045)
        
        def fit(A, B, Lc, hint):
            d = B - A
            dist = min(d.length, Lc * 2 - 0.01)
            h = math.sqrt(max(Lc * Lc - (dist / 2) ** 2, 0.0))
            return A + d.normalized() * (dist / 2) + hint.normalized() * h
            
        E = fit(S, W, 0.28, -f * 0.65 + Y * sgn * 0.75 - u * 0.08)
        el[sgn], wr[sgn] = E, W

        mid_upper = S.lerp(E, 0.5) + f * 0.01
        
        if rolled:
            # Manga remangada: continua hasta bajo el codo con dobladillo
            Ecuff = E + (W - E) * 0.25
            arm_pts = [S, mid_upper, E, Ecuff]
            arm_radii = [0.072, 0.060, 0.055, 0.058]
            tube(shirt, arm_pts, arm_radii, sides=16, caps=False)
            torus_ring(shirt, Ecuff, (W - E), 0.060, 0.060, 0.018, up_hint=(0, 0, 1), major=18, minor=6)
            # Antebrazo desnudo de piel
            fore_pts = [Ecuff, Ecuff.lerp(W, 0.5), W]
            tube(skin, fore_pts, [0.045, 0.038, 0.033], sides=16, caps=False)
        else:
            # Manga completa continua hasta la muneca
            mid_fore = E.lerp(W, 0.5) - f * 0.01
            arm_pts = [S, mid_upper, E, mid_fore, W]
            arm_radii = [0.072, 0.060, 0.054, 0.046, 0.038]
            tube(shirt, arm_pts, arm_radii, sides=16, caps=False)

        # Mano crispadita atada
        hdir = (W - E).normalized()
        palm = W + hdir * 0.045 - u * 0.01
        sphere(skin, 0.036, palm, (0.9, 0.75, 1.1), seg=12, rings=8)
        for fd_i in range(4):
            fp = palm + hdir * 0.026 + Y * (sgn * (-0.012 + fd_i * 0.008)) - f * 0.008
            sphere(skin, 0.010, fp, (1.3, 0.8, 0.9), seg=8, rings=6)

    # Soga gruesa que ciñe ambas muñecas
    wm = (wr[-1] + wr[1]) * 0.5
    arm_ax = ((wr[-1] - el[-1]).normalized() + (wr[1] - el[1]).normalized()).normalized()
    if arm_ax.length < 0.1:
        arm_ax = -u
    for k in range(5):
        off_c = wm + arm_ax * (-0.018 + k * 0.009)
        torus_ring(rope, off_c, arm_ax, 0.080 + 0.002 * (k % 2), 0.040, 0.0095, up_hint=f, major=22, minor=6)
    for sgn in (-1, 1):
        torus_ring(rope, wr[sgn], wr[sgn] - el[sgn], 0.035, 0.035, 0.0085, up_hint=f, major=14, minor=5)
    knot = wm - f * 0.040
    sphere(rope, 0.021, knot, seg=10, rings=8)
    tube(rope, [knot, knot + Vector((-0.03 * f.x, 0.025, -0.08)), knot + Vector((-0.02 * f.x, 0.045, -0.16))], 0.0075, sides=6)
    tube(rope, [knot, knot + Vector((-0.03 * f.x, -0.03, -0.07)), knot + Vector((-0.05 * f.x, -0.055, -0.14))], 0.0075, sides=6)

    # ---------------- 3. Piernas y Pantalones Continuos (Sin Bolas de Rodilla) ----------------
    for sgn, key in ((1, 'l'), (-1, 'r')):
        hip = P0 + Vector((-0.02, sgn * 0.105, -0.02))
        td = Vector(cfg['thigh_' + key]).normalized()
        sd = Vector(cfg['shin_' + key]).normalized()
        knee = hip + td * 0.44
        ankle = knee + sd * 0.42

        # Puntos de la pierna continua: cadera -> muslo -> pliegue de rodilla -> pantorrilla -> tobillo
        mid_thigh = hip.lerp(knee, 0.45) + Vector((0, 0, 0.018))
        knee_fold = knee + (td - sd).normalized() * 0.014
        mid_shin = knee.lerp(ankle, 0.50) + Vector((0, 0, 0.012))
        
        leg_pts = [hip, mid_thigh, knee_fold, mid_shin, ankle]
        leg_radii = [0.106, 0.094, 0.078, 0.072, 0.064]
        tube(trou, leg_pts, leg_radii, sides=18, caps=False)

        # Calzado o pie
        phi = cfg['foot_' + key]
        fd = Vector((math.cos(phi), 0, math.sin(phi)))
        toe = ankle + fd * 0.22 + Vector((0, 0, -0.048))
        heel = ankle + Vector((-0.040, 0, -0.048))
        bare = cfg.get('sock_' + key, False)
        
        if bare:
            # Pie descalzo con media sucia
            tube(skin, [heel, heel.lerp(toe, 0.5), toe], [0.044, 0.040, 0.028], sides=12, caps=True)
        else:
            # Zapato con silueta realista (NO caja plana)
            smooth_organic_shoe(shoe, dark, heel, toe, fd, sgn, mi=0)

    # Cinturón con presillas
    belt_c = P0 + u * 0.112
    torus_ring(shoe, belt_c, u, 0.165, 0.112, 0.015, up_hint=(1, 0, 0), major=24, minor=5)
    buckle_p = belt_c + f * 0.118
    box(thread, (0.014, 0.048, 0.038), buckle_p, rot=(0, -lean, 0), bevel=0.003)
    box(dark, (0.016, 0.028, 0.022), buckle_p + f * 0.002, rot=(0, -lean, 0))

    # ---------------- 4. Capucha de Arpillera Auténtica con Orejas Dobladas ----------------
    Rh = rotY(lean + bow) @ rotX(roll)
    neck_base = P0 + u * 0.58 + f * 0.06
    ax = Rh @ Vector((0, 0, 1))
    fw = Rh @ Vector((1, 0, 0))
    lr_ax = Rh @ Vector((0, 1, 0))
    Hc = neck_base + ax * 0.13 + fw * 0.02

    # Perfil continuo y voluminoso del saco
    prof = [
        (0.160, 0.018, 0.018),   # punta superior
        (0.145, 0.065, 0.075),
        (0.125, 0.105, 0.115),   # coronilla
        (0.080, 0.116, 0.130),   # sienes / frente
        (0.035, 0.118, 0.132),   # pomulos
        (0.000, 0.115, 0.130),   # nariz
        (-0.04, 0.110, 0.125),   # boca / menton
        (-0.08, 0.100, 0.115),   # mandibula
        (-0.11, 0.085, 0.095),   # cuello alto (estrangulado por la soga)
        (-0.14, 0.080, 0.090),   # zona de la soga
        (-0.17, 0.125, 0.118),   # faldon que abre hacia los hombros
        (-0.21, 0.175, 0.145),   # caída sobre clavículas
        (-0.25, 0.210, 0.165)    # faldon inferior sobre el pecho
    ]
    sides = 28
    hring = []
    for (t, w, h) in prof:
        wob = 1.0 + 0.03 * (noise.noise(Vector((t * 7, 0.3, 2.0))))
        c = Hc + ax * t
        if t < -0.15:
            c = c + fw * (-0.01)
        hring.append((c, ax, w * wob, h * wob, sides, fw))
    rings = loft(hood, hring, mat_index=0, caps=(True, False))

    # Cabeza interior oscura (fondo para los ojos)
    sphere(dark, 0.10, Hc + fw * 0.005, (1.15, 1.0, 1.25), seg=14, rings=10)

    # Formar las dos esquinas plegadas tipo "orejas" de bolsa de arpillera de 50kg
    for v in hood.verts:
        rel = v.co - Hc
        up_proj = rel.dot(ax)
        lr_proj = rel.dot(lr_ax)
        if up_proj > 0.065 and abs(lr_proj) > 0.035:
            sgn = 1.0 if lr_proj > 0 else -1.0
            # Jalar las esquinas hacia arriba y hacia afuera
            v.co += lr_ax * (0.032 * sgn) + ax * 0.038

    # Ojos cortados a cuchillo (aberturas toscas irregulares)
    eye_w = []
    for sgn in (-1, 1):
        ep = Hc + fw * 0.122 + Rh @ Vector((0, sgn * 0.038, 0.018))
        eye_w.append((ep, sgn))
    to_del = []
    for fcs in hood.faces:
        c = fcs.calc_center_median()
        for ep, _sgn in eye_w:
            d = c - ep
            dd = math.sqrt((d.dot(lr_ax) / 1.75) ** 2 + (d.dot(ax) / 0.95) ** 2 + (d.dot(fw) * 0.35) ** 2)
            if dd < rng.uniform(0.018, 0.028):
                to_del.append(fcs)
                break
    bmesh.ops.delete(hood, geom=list(set(to_del)), context='FACES')

    # Hebras deshilachadas sutiles en los ojos
    for ep, sgn in eye_w:
        for kf in range(5):
            ang = 2 * math.pi * kf / 5 + rng.uniform(-0.3, 0.3)
            p_st = ep + lr_ax * (math.cos(ang) * 0.022) + ax * (math.sin(ang) * 0.012) + fw * 0.004
            p_en = p_st + lr_ax * rng.uniform(-0.006, 0.006) - ax * rng.uniform(0.006, 0.016)
            tube(hood, [p_st, p_en], 0.0016, sides=4, caps=False)

    # Soga en el cuello que ciñe la tela con fuerza
    nc = Hc + ax * -0.128
    for ks in range(3):
        torus_ring(rope, nc - ax * (ks * 0.010), ax, 0.084 + ks * 0.002, 0.092 + ks * 0.002, 0.010, up_hint=fw, major=24, minor=6)
    kp = nc + fw * 0.098 + lr_ax * 0.016
    sphere(rope, 0.020, kp, seg=10, rings=8)
    tube(rope, [kp, kp + fw * 0.02 + Vector((0.0, 0.02, -0.06)), kp + Vector((0.03, 0.035, -0.13))], 0.007, sides=6)
    tube(rope, [kp, kp + fw * 0.01 + Vector((0.0, -0.025, -0.05)), kp + Vector((0.02, -0.05, -0.115))], 0.007, sides=6)

    # ---------------- 5. Ensamblado con Suavizado Total ----------------
    out = new_bm()
    parts = [(shirt, 0), (trou, 1), (skin, 2), (shoe, 3), (hood, 4), (rope, 5), (dark, 6), (thread, 7)]
    for b, mi in parts[:2]:
        noise_displace(b, 16.0, 0.004, seed=rng.randint(0, 99))
    for b, mi in parts:
        for f in b.faces:
            f.smooth = True
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
    shirt_central = cloth_mat('MAT_Camisa_Crema', srgb('#8a826e'), srgb('#726c58'), rough=0.92, weave=140.0, scale=5.0, bump=0.8,
                              dirt=0.8, sheen=0.1, seed=11)
    trou_dark = cm('MAT_Pantalon_Oscuro', '#181b20', '#22252c', seed=12)
    sw_blue = cm('MAT_Pulover_Gris', '#3e4852', '#303840', seed=13)
    trou_brown = cm('MAT_Pantalon_Marron', '#34281e', '#241a12', seed=14)
    sh_beige = cm('MAT_Camisa_Beige', '#7a6c52', '#5e523c', seed=15)
    trou_navy = cm('MAT_Pantalon_Azul', '#181e2b', '#202636', seed=16)
    sw_green = cm('MAT_Pulover_Verde', '#283226', '#1c261a', seed=17)
    jeans = cm('MAT_Jean_Gastado', '#263040', '#323c4e', seed=18)
    sh_vest = cm('MAT_Camiseta_Sucia', '#98907a', '#7a725c', seed=19)
    trou_grey = cm('MAT_Pantalon_Gris', '#3c3a36', '#2c2a26', seed=20)

    DIR = lambda x, y, z: Vector((x, y, z))
    cfgs = []
    # 0: Cautivo Hero (sentado al borde de la compuerta, rodillas flexionadas 90 grados, piernas colgando hacia abajo con caida natural)
    c0 = dict(lean=0.38, bow=0.48, roll=0.05, rolled=True,
              thigh_l=DIR(1.0, 0.12, -0.02), thigh_r=DIR(1.0, -0.12, -0.04),
              shin_l=DIR(0.04, 0.02, -1.0), shin_r=DIR(-0.02, -0.02, -1.0),
              foot_l=-0.48, foot_r=-0.58,
              shirt_mat=shirt_central, trousers_mat=trou_dark, shoe_mat=shoe_dark)
    cfgs.append(('CAUTIVO_Central', Vector((0.02, -2.72, FLOOR_Z)), -math.pi / 2 + 0.12, c0))
    
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
