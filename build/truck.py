"""Camion militar de traslado, estilo Unimog/Mercedes 1970s (verde oliva desgastado)."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, noise
from common import *

CN = 'Camion'

# --- dimensiones clave -------------------------------------------------------
FLOOR_Z = 1.25          # cara superior del piso de la caja
BED_Y0, BED_Y1 = -2.55, 0.50
BED_HX = 0.95           # semiancho interior
SIDE_TOP = 1.95         # tope de laterales
ARCH_Y = [-2.50, -1.70, -0.90, -0.10, 0.42]
AXLE_F, AXLE_R = 1.5, -1.3
WHEEL_X = 0.92
WHEEL_Z = 0.52
TIRE_R = 0.56


# ----------------------------------------------------------------------------
# Materiales
# ----------------------------------------------------------------------------
def mats():
    M = {}
    M['paint'] = weathered('MAT_Pintura_Oliva', srgb('#2f3720'), srgb('#464d2e'), rough=0.74, metal=0.15, scale=2.2,
                           rust=0.42, mud_h=1.08, mud=0.60, bump=0.38, grime=0.58, wear=0.45, seed=1)
    M['iron'] = weathered('MAT_Hierro_Oxidado', srgb('#141210'), srgb('#26201a'), rough=0.65, metal=0.82, scale=3.0,
                          rust=0.58, mud_h=0.85, mud=0.62, bump=0.6, grime=0.55, seed=2)
    M['black'] = weathered('MAT_Hierro_Negro', srgb('#0b0a09'), srgb('#171512'), rough=0.7, metal=0.6, scale=3.0,
                           rust=0.28, mud_h=0.85, mud=0.7, bump=0.4, seed=3)
    M['wood_y'] = wood_mat('MAT_Madera_Tablon_Y', 'y')
    M['wood_x'] = wood_mat('MAT_Madera_Tablon_X', 'x')
    M['rubber'] = weathered('MAT_Goma_Neumatico', srgb('#0b0b0a'), srgb('#1a1917'), rough=0.85, metal=0.0, scale=5.0,
                            mud_h=0.62, mud=0.78, bump=0.9, grime=0.35, wet=0.55, seed=4)
    M['canvas'] = cloth_mat('MAT_Lona_Toldo', srgb('#3a3e24'), srgb('#4f4329'), rough=0.94, weave=160.0, scale=2.0,
                            bump=0.75, dirt=0.72, seed=5)
    M['canvas'].use_backface_culling = False
    M['patch'] = cloth_mat('MAT_Lona_Parche', srgb('#4e5234'), srgb('#615739'), rough=0.92, weave=160.0, scale=3.0,
                           bump=0.65, dirt=0.55, seed=6)
    M['patch'].use_backface_culling = False
    M['rope'] = rope_mat('MAT_Soga')
    mb = MB('MAT_Vidrio_Sucio')
    mb.set(Base_Color=(0.012, 0.018, 0.018, 1), Roughness=0.22, Metallic=0.0)
    M['glass'] = mb.done()
    M['head'] = emit_mat('MAT_Faro_Calido', srgb('#ffd699'), 22.0)
    M['tail'] = emit_mat('MAT_Luz_Trasera', srgb('#d91809'), 2.2)
    mb = MB('MAT_Chapa_Patente')
    mb.set(Base_Color=srgb('#0d0d0c'), Roughness=0.6, Metallic=0.3)
    M['plate'] = mb.done()
    mb = MB('MAT_Estarcido_Blanco')
    mb.set(Base_Color=srgb('#afa98e'), Roughness=0.85)
    M['stencil'] = mb.done()
    return M


def wood_mat(name, axis):
    """tablon viejo: veta alargada segun eje, grisaceo, astillado, con barro abajo"""
    mb = MB(name)
    sc = (1.0, 0.05, 1.0) if axis == 'y' else (0.05, 1.0, 1.0)
    vec = mb.map(scale=sc)
    g1 = mb.noise(26.0, 5, 0.6, vec=vec, dist=0.4)
    g2 = mb.noise(90.0, 3, 0.5, vec=vec)
    dirty = mb.noise(2.5, 6, 0.6)
    col = mb.mixc(mb.ramp(g1, [(0.3, (0, 0, 0, 1)), (0.7, (1, 1, 1, 1))]), srgb('#2c2218'), srgb('#6a5a45'))
    col = mb.mixc(mb.maprange(dirty, 0.4, 0.8, 0.0, 0.8), col, srgb('#1b150f'))
    col = mb.mixc(mb.maprange(g2, 0.35, 0.65, 0.0, 0.3), col, (0.01, 0.008, 0.005, 1))
    # mugre/barro (por altura)
    x, y, z = mb.sep()
    mm = mb.maprange(mb.math('ADD', mb.math('SUBTRACT', 1.0, mb.math('MULTIPLY', z, 0.9)), mb.math('MULTIPLY', mb.noise(5, 6, 0.6), 0.5)), 0.5, 1.1, 0.0, 0.6)
    col = mb.mixc(mm, col, srgb('#2a1c10'))
    h = mb.math('ADD', g1, mb.math('MULTIPLY', g2, 0.5))
    mb.set(Base_Color=col, Roughness=0.88, Normal=mb.bump(h, 1.2, 0.02))
    return mb.done()


def rope_mat(name):
    mb = MB(name)
    sc = (1.0, 1.0, 1.0)
    n = mb.noise(120.0, 3, 0.5)
    w = mb.wave(220.0, 0.3, 0.0, direction='X')
    col = mb.mixc(mb.noise(8, 4, 0.5), srgb('#5a4a30'), srgb('#8a7752'))
    col = mb.mixc(mb.maprange(n, 0.3, 0.7, 0.0, 0.5), col, srgb('#1c150b'))
    mb.set(Base_Color=col, Roughness=0.95, Normal=mb.bump(mb.math('ADD', n, w), 0.8, 0.003))
    return mb.done()


# ----------------------------------------------------------------------------
# Rueda
# ----------------------------------------------------------------------------
def lathe(bm, prof, cx_, cy_, cz_, segs=48, lug=0.0, phase=0.0, sign=1.0, mat_index=0):
    rings = []
    for i in range(segs):
        a = 2 * math.pi * i / segs + phase
        ring = []
        for (r, ax, tag) in prof:
            rr = r + (lug if (tag and (i % 2 == 0)) else 0.0)
            ring.append(bm.verts.new((cx_ + sign * ax, cy_ + rr * math.cos(a), cz_ + rr * math.sin(a))))
        rings.append(ring)
    n = len(prof)
    for i in range(segs):
        A, B = rings[i], rings[(i + 1) % segs]
        for j in range(n - 1):
            try:
                f = bm.faces.new([A[j], B[j], B[j + 1], A[j + 1]] if sign > 0 else [A[j], A[j + 1], B[j + 1], B[j]])
                f.smooth = True
                f.material_index = mat_index
            except ValueError:
                pass


def wheel(bm_tire, bm_rim, bm_iron, x, y, rng):
    s = 1.0 if x > 0 else -1.0
    prof = [(0.34, -0.14, False), (0.40, -0.17, False), (0.50, -0.175, False), (0.545, -0.125, True),
            (0.56, -0.07, True), (0.56, 0.07, True), (0.545, 0.125, True), (0.50, 0.175, False),
            (0.40, 0.17, False), (0.34, 0.14, False)]
    lathe(bm_tire, prof, x, y, WHEEL_Z, 48, lug=0.028, phase=rng.uniform(0, 6.28), sign=s)
    rim = [(0.0, 0.10, False), (0.10, 0.11, False), (0.13, 0.085, False), (0.30, 0.10, False), (0.345, 0.15, False),
           (0.335, 0.0, False), (0.34, -0.14, False)]
    lathe(bm_rim, rim, x, y, WHEEL_Z, 32, sign=s)
    for k in range(8):
        a = 2 * math.pi * k / 8
        cyl(bm_iron, 0.022, 0.018, 0.04, (x + s * 0.115, y + 0.19 * math.cos(a), WHEEL_Z + 0.19 * math.sin(a)),
            (0, math.pi / 2, 0), sides=6)
    cyl(bm_iron, 0.06, 0.05, 0.05, (x + s * 0.125, y, WHEEL_Z), (0, math.pi / 2, 0), sides=12)


def fender(bm, x, y, rng, wide=0.46, R=0.66, out=1.0):
    """guardabarro en arco sobre la rueda"""
    segs = 18
    z0 = WHEEL_Z
    x0, x1 = x - wide / 2 * out - 0.03 * out, x + wide / 2 * out + 0.03 * out
    rows = []
    for i in range(segs + 1):
        a = math.radians(15 + 150 * i / segs)
        yy = y + R * math.cos(a) * 1.15
        zz = z0 + R * math.sin(a)
        rows.append((bm.verts.new((x0, yy, zz)), bm.verts.new((x1, yy, zz))))
    for i in range(segs):
        a, b = rows[i], rows[i + 1]
        try:
            f = bm.faces.new([a[0], a[1], b[1], b[0]]); f.smooth = True
        except ValueError:
            pass
    # labio exterior
    xo = x1 if out > 0 else x0
    top_out = []
    for i in range(segs + 1):
        a = math.radians(15 + 150 * i / segs)
        yy = y + R * math.cos(a) * 1.15
        zz = z0 + R * math.sin(a)
        top_out.append(bm.verts.new((xo, yy, zz - 0.08)))
    for i in range(segs):
        a, b = rows[i][1 if out > 0 else 0], rows[i + 1][1 if out > 0 else 0]
        try:
            f = bm.faces.new([a, top_out[i], top_out[i + 1], b]); f.smooth = True
        except ValueError:
            pass


# ----------------------------------------------------------------------------
# Canvas (toldo) - superficie parametrica
# ----------------------------------------------------------------------------
CS_PTS = []      # puntos base de la seccion
CS_N = []
CS_ARC = []      # longitud de arco acumulada
CS_KIND = []     # 0 drape izq, 1 arco, 2 drape der
RX, RZ, CZ = 1.04, 0.84, SIDE_TOP


def _build_section():
    global CS_PTS, CS_N, CS_ARC, CS_KIND
    CS_PTS, CS_N, CS_KIND = [], [], []
    nd, na = 7, 60
    for i in range(nd):
        t = i / nd
        CS_PTS.append(Vector((-1.075 + 0.035 * t, 0, 1.58 + (CZ - 1.58) * t)))
        CS_N.append(Vector((-1, 0, 0)))
        CS_KIND.append(0)
    for i in range(na + 1):
        th = math.pi - math.pi * i / na
        CS_PTS.append(Vector((RX * math.cos(th), 0, CZ + RZ * math.sin(th))))
        CS_N.append(Vector((math.cos(th) / RX, 0, math.sin(th) / RZ)).normalized())
        CS_KIND.append(1)
    for i in range(1, nd + 1):
        t = i / nd
        CS_PTS.append(Vector((1.04 + 0.035 * t, 0, CZ - (CZ - 1.58) * t)))
        CS_N.append(Vector((1, 0, 0)))
        CS_KIND.append(2)
    CS_ARC = [0.0]
    for i in range(1, len(CS_PTS)):
        CS_ARC.append(CS_ARC[-1] + (CS_PTS[i] - CS_PTS[i - 1]).length)


def sag_at(y):
    """cuanto cae la lona entre arcos"""
    ys = ARCH_Y
    if y <= ys[0]:
        return 0.025 * min(1.0, (ys[0] - y) / 0.2)
    if y >= ys[-1]:
        return 0.02 * min(1.0, (y - ys[-1]) / 0.1)
    for a, b in zip(ys[:-1], ys[1:]):
        if a <= y <= b:
            t = (y - a) / (b - a)
            return 0.095 * math.sin(math.pi * t) ** 1.4
    return 0.0


def canvas_point(j, y, seed=0.0):
    P = CS_PTS[j].copy()
    N = CS_N[j]
    kind = CS_KIND[j]
    sg = sag_at(y)
    ctr = Vector((0, 0, CZ))
    if kind == 1:
        rel = P - ctr
        w = max(0.0, rel.z / RZ) ** 0.7
        P = ctr + rel * (1 - sg / 0.9 * w)
    else:
        # drapes: se hamacan hacia adentro entre arcos y ondulan sueltos
        t = (CS_ARC[j] if kind == 0 else (CS_ARC[-1] - CS_ARC[j])) / 0.4
        P += N * (-sg * 0.8 * (1 - min(1.0, abs(t))) + 0.02 * noise.noise(Vector((y * 2.0, j * 0.3, 4.0 + seed))) * (1 - min(1.0, t)))
        if kind == 0:
            P.x -= 0.03 * (1 - min(1.0, t))
    P.y = y
    # arrugas
    q = Vector((P.x * 2.2, y * 2.6, P.z * 2.2 + seed))
    P += N * (noise.noise(q) * 0.022 + noise.noise(q * 3.1) * 0.007)
    return P


def canvas_mesh(rng, bm_c):
    ny = 120
    y0, y1 = -2.70, 0.56
    nj = len(CS_PTS)
    grid = []
    for k in range(ny + 1):
        y = y0 + (y1 - y0) * k / ny
        grid.append([bm_c.verts.new(canvas_point(j, y)) for j in range(nj)])
    # desgarros: elipses en (arco m, y)
    tears = [(1.5, -1.9, 0.30, 0.38), (3.3, -0.55, 0.22, 0.30), (4.4, -2.35, 0.34, 0.26),
             (2.5, 0.15, 0.18, 0.22), (0.35, -1.2, 0.14, 0.34), (5.4, -1.0, 0.20, 0.5), (3.9, -1.45, 0.12, 0.16)]
    tears = [(s, y, a, b) for (s, y, a, b) in tears]
    tot = CS_ARC[-1]
    faces = []
    for k in range(ny):
        for j in range(nj - 1):
            yc = y0 + (y1 - y0) * (k + 0.5) / ny
            sc = (CS_ARC[j] + CS_ARC[j + 1]) * 0.5
            rem = False
            for (ts, ty, ra, rb) in tears:
                d = ((sc - ts) / ra) ** 2 + ((yc - ty) / rb) ** 2
                if d < rng.uniform(0.55, 1.0):
                    rem = True
                    break
            # borde trasero deshilachado
            if not rem and yc < y0 + 0.14 and rng.random() < (y0 + 0.14 - yc) / 0.14 * 0.7:
                rem = True
            # dobladillo inferior desgastado
            if not rem and (j < 2 or j >= nj - 3) and rng.random() < 0.18:
                rem = True
            if rem:
                continue
            try:
                f = bm_c.faces.new([grid[k][j], grid[k][j + 1], grid[k + 1][j + 1], grid[k + 1][j]])
                f.smooth = True
                f.material_index = 0
            except ValueError:
                pass
    # deshilachado: mover vertices sueltos de bordes
    for v in bm_c.verts:
        if v.is_boundary:
            v.co += Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) * 0.012
    # eliminar vertices sin cara
    for v in list(bm_c.verts):
        if not v.link_faces:
            bm_c.verts.remove(v)
    # parches (cuadrados de lona cosidos encima)
    patches = [(1.2, -1.2, 0.5, 0.45), (3.9, -2.0, 0.55, 0.55), (4.8, -0.35, 0.45, 0.4), (2.1, -0.4, 0.4, 0.5), (0.2, -0.9, 0.3, 0.3),
               (5.3, -2.3, 0.3, 0.4)]
    for (s0, py, w, h) in patches:
        n1, n2 = 6, 6
        vv = []
        for a in range(n2 + 1):
            row = []
            for b in range(n1 + 1):
                s = s0 + w * (b / n1 - 0.5)
                y = py + h * (a / n2 - 0.5)
                # indice j mas cercano + interpolacion
                jj = min(range(nj), key=lambda q: abs(CS_ARC[q] - s))
                P = canvas_point(jj, y, 0.0)
                P += CS_N[jj] * 0.009
                row.append(bm_c.verts.new(P))
            vv.append(row)
        for a in range(n2):
            for b in range(n1):
                try:
                    f = bm_c.faces.new([vv[a][b], vv[a][b + 1], vv[a + 1][b + 1], vv[a + 1][b]])
                    f.smooth = True
                    f.material_index = 1
                except ValueError:
                    pass


def rear_curtain(rng, bm_c):
    """faldon trasero recogido: anillo de lona en el borde del arco, con pliegues y desgarros"""
    nj = len(CS_PTS)
    yb = -2.66
    rows = 9
    ctr = Vector((0.0, yb, CZ - 0.05))
    grid = []
    for r in range(rows):
        rho = 1.0 - r * (0.5 / (rows - 1)) * 1.0
        row = []
        for j in range(nj):
            P = CS_PTS[j].copy()
            P.y = yb
            Q = ctr + (P - ctr) * rho
            # los costados se recogen hacia afuera/arriba (atados), el techo cuelga
            fold = math.sin(j * 0.55 + r * 0.8) * 0.045 + noise.noise(Vector((j * 0.2, r * 0.7, 3.3))) * 0.06
            Q.y += fold - 0.0 * r
            if CS_KIND[j] != 1:
                Q.z += 0.12 * r / rows
            row.append(bm_c.verts.new(Q))
        grid.append(row)
    for r in range(rows - 1):
        for j in range(nj - 1):
            if rng.random() < 0.06 + 0.1 * (r / rows):
                continue
            # abertura central ancha abajo (se ve el exterior)
            xm = (grid[r][j].co.x + grid[r][j + 1].co.x) * 0.5
            zm = (grid[r][j].co.z + grid[r + 1][j].co.z) * 0.5
            if abs(xm) < 0.42 and zm < 2.55 and rng.random() < 0.8:
                continue
            try:
                f = bm_c.faces.new([grid[r][j], grid[r][j + 1], grid[r + 1][j + 1], grid[r + 1][j]])
                f.smooth = True
                f.material_index = 0
            except ValueError:
                pass
    for v in list(bm_c.verts):
        if not v.link_faces:
            bm_c.verts.remove(v)


# ----------------------------------------------------------------------------
# Principal
# ----------------------------------------------------------------------------
def build():
    clear_collection(CN)
    rng = random.Random(404)
    M = mats()
    _build_section()
    root = bpy.data.objects.get('TRUCK_Root')
    if root is None:
        root = bpy.data.objects.new('TRUCK_Root', None)
        coll(CN).objects.link(root)
    out = {}

    paint, iron, black = new_bm(), new_bm(), new_bm()
    wy, wx = new_bm(), new_bm()
    tire, rim = new_bm(), new_bm()
    glass, head, tail = new_bm(), new_bm(), new_bm()
    rope, plate, stencil = new_bm(), new_bm(), new_bm()

    # ---------------- chasis ----------------
    for sx in (-0.55, 0.55):
        box(iron, (0.10, 6.2, 0.18), (sx, 0.25, 0.80), bevel=0.01)
        box(iron, (0.18, 6.2, 0.04), (sx, 0.25, 0.90))
        box(iron, (0.18, 6.2, 0.04), (sx, 0.25, 0.71))
    for yy in (-2.5, -1.8, -0.9, 0.0, 0.7, 1.5, 2.3, 2.9):
        box(iron, (1.1, 0.08, 0.10), (0, yy, 0.82), bevel=0.01)
    # ejes, diferenciales, cardan
    for ya in (AXLE_F, AXLE_R):
        cyl(iron, 0.055, 0.055, 1.9, (0, ya, WHEEL_Z), (0, math.pi / 2, 0), sides=12)
        sphere(black, 0.16, (0, ya + 0.02, WHEEL_Z + 0.03), (1.0, 1.0, 0.9), seg=14, rings=8)
        for sx in (-0.52, 0.52):
            box(iron, (0.07, 1.1, 0.045), (sx, ya, 0.66), bevel=0.005)      # ballesta
            box(iron, (0.07, 0.8, 0.04), (sx, ya, 0.70))
            box(iron, (0.07, 0.08, 0.14), (sx, ya + 0.12, 0.76))
        # portal (Unimog)
        for sx in (-0.88, 0.88):
            cyl(black, 0.10, 0.10, 0.14, (sx * 0.98, ya, WHEEL_Z), (0, math.pi / 2, 0), sides=10)
    cyl(iron, 0.04, 0.04, 2.9, (0, 0.1, 0.58), (math.pi / 2, 0, 0), sides=8)
    # tanque combustible
    box(black, (0.38, 0.95, 0.30), (-0.78, -0.35, 0.88), bevel=0.03)
    # paragolpes
    box(iron, (2.0, 0.14, 0.22), (0, 3.28, 0.82), bevel=0.02)
    box(iron, (1.95, 0.12, 0.2), (0, -2.74, 0.83), bevel=0.02)
    cyl(iron, 0.04, 0.03, 0.2, (0, -2.84, 0.83), (math.pi / 2, 0, 0), sides=8)       # gancho remolque
    cyl(iron, 0.03, 0.03, 0.3, (0.55, 3.38, 0.78), (math.pi / 2, 0, 0), sides=8)
    for sx in (-1, 1):
        box(tail, (0.16, 0.05, 0.10), (sx * 0.78, -2.815, 0.89), bevel=0.01)
        box(iron, (0.2, 0.03, 0.14), (sx * 0.78, -2.805, 0.89))
    box(plate, (0.52, 0.02, 0.13), (0, -2.81, 0.78))

    # ---------------- ruedas ----------------
    for (x, y) in ((-WHEEL_X, AXLE_F), (WHEEL_X, AXLE_F), (-WHEEL_X, AXLE_R), (WHEEL_X, AXLE_R)):
        wheel(tire, rim, iron, x, y, rng)
    for sx in (-1, 1):
        fender(paint, sx * WHEEL_X, AXLE_F, rng, out=sx)
        # guardabarros traseros y baberos de goma con barro
        fender(iron, sx * WHEEL_X, AXLE_R, rng, wide=0.44, R=0.64, out=sx)
        box(tire, (0.42, 0.02, 0.34), (sx * WHEEL_X, AXLE_R - 0.72, 0.42), rot=(0.08, 0, 0))
        box(iron, (0.44, 0.03, 0.04), (sx * WHEEL_X, AXLE_R - 0.71, 0.58))
    # rueda de auxilio bajo la caja (lado derecho)
    cyl(tire, 0.48, 0.48, 0.24, (0.74, -0.32, 0.88), (0, 0, 0), sides=28)
    cyl(rim, 0.28, 0.28, 0.25, (0.74, -0.32, 0.88), (0, 0, 0), sides=20)
    box(iron, (0.06, 1.02, 0.05), (0.74, -0.32, 0.74))

    # ---------------- capot y cabina (estilo Unimog 416 / Mercedes 1970s) ----------------
    # capot inclinado
    box(paint, (1.36, 1.06, 0.50), (0, 2.58, 1.37), rot=(-0.10, 0, 0), bevel=0.07)
    box(paint, (1.14, 0.92, 0.05), (0, 2.56, 1.63), rot=(-0.10, 0, 0), bevel=0.03)
    box(paint, (0.12, 0.98, 0.04), (0, 2.56, 1.66), rot=(-0.10, 0, 0))
    for sx in (-1, 1):
        box(iron, (0.04, 0.8, 0.03), (sx * 0.68, 2.55, 1.38))
        # rejillas laterales de ventilacion
        for kv in range(5):
            box(black, (0.02, 0.03, 0.18), (sx * 0.685, 2.25 + kv * 0.06, 1.48))
    # parrilla frontal y faros con rejilla protectora
    box(paint, (1.38, 0.10, 0.48), (0, 3.09, 1.34), bevel=0.03)
    box(black, (0.82, 0.05, 0.34), (0, 3.13, 1.34))
    for k in range(5):
        box(iron, (0.80, 0.04, 0.018), (0, 3.145, 1.21 + k * 0.065))
    cyl(iron, 0.09, 0.09, 0.03, (0, 3.15, 1.35), (math.pi / 2, 0, 0), sides=16)  # aro central desgastado
    for sx in (-1, 1):
        cyl(iron, 0.135, 0.135, 0.12, (sx * 0.54, 3.08, 1.36), (math.pi / 2, 0, 0), sides=18)
        cyl(head, 0.10, 0.10, 0.05, (sx * 0.54, 3.14, 1.36), (math.pi / 2, 0, 0), sides=16)
        # rejilla protectora del faro
        for kg in (-0.05, 0.0, 0.05):
            box(iron, (0.01, 0.03, 0.22), (sx * 0.54 + kg, 3.17, 1.36))
        box(iron, (0.12, 0.09, 0.08), (sx * 0.63, 3.13, 1.56))      # luz de oscurecimiento tactico
    # cabina inferior + marco de parabrisas inclinado
    box(paint, (1.66, 1.52, 0.88), (0, 1.30, 1.44), bevel=0.07)
    box(paint, (1.62, 1.40, 0.64), (0, 1.25, 2.14), bevel=0.07)
    box(paint, (1.74, 1.56, 0.07), (0, 1.26, 2.46), bevel=0.025)                # techo
    cyl(paint, 0.30, 0.28, 0.05, (0.36, 1.32, 2.50), (0, 0, 0), sides=16)       # escotilla de techo Unimog
    box(paint, (1.72, 0.20, 0.035), (0, 2.04, 2.43), rot=(0.15, 0, 0), bevel=0.01)  # visera
    # parabrisas dividido y ventanillas
    for sx in (-1, 1):
        box(glass, (0.66, 0.025, 0.46), (sx * 0.38, 1.98, 2.08), rot=(-0.18, 0, 0))
        box(iron, (0.045, 0.04, 0.50), (sx * 0.74, 1.98, 2.08), rot=(-0.18, 0, 0))
        # limpiaparabrisas
        box(black, (0.28, 0.02, 0.015), (sx * 0.36, 2.02, 1.96), rot=(0, 0.35, 0))
        box(glass, (0.025, 0.58, 0.44), (sx * 0.815, 1.52, 2.06))
        box(glass, (0.025, 0.28, 0.36), (sx * 0.815, 0.80, 2.06))
        box(black, (0.03, 0.02, 0.9), (sx * 0.835, 1.12, 1.72))              # junta puerta
        box(black, (0.03, 0.02, 0.9), (sx * 0.835, 1.96, 1.72))
        box(iron, (0.05, 0.14, 0.03), (sx * 0.85, 1.1, 1.72))                # manija
        # espejo retrovisor tubular
        tube(iron, [Vector((sx * 0.84, 1.92, 1.92)), Vector((sx * 1.04, 1.95, 2.04)), Vector((sx * 1.08, 1.95, 2.22)), Vector((sx * 0.84, 1.92, 2.30))], 0.012, sides=6)
        box(black, (0.03, 0.13, 0.26), (sx * 1.09, 1.95, 2.13), bevel=0.006)
    box(iron, (0.045, 0.04, 0.50), (0, 1.98, 2.08), rot=(-0.18, 0, 0))
    # estribos
    for sx in (-1, 1):
        box(iron, (0.28, 0.5, 0.04), (sx * 0.92, 0.72, 0.80), bevel=0.005)
    # escape
    tube(iron, [Vector((0.98, 0.9, 0.62)), Vector((0.98, 0.52, 0.62)), Vector((0.98, 0.5, 1.3)), Vector((0.98, 0.5, 2.3)), Vector((0.95, 0.48, 2.52))], 0.05, sides=8)
    cyl(black, 0.065, 0.05, 0.12, (0.95, 0.48, 2.55), (0, 0, 0), sides=8)
    # jerrycan (bidon) lateral
    box(paint, (0.2, 0.52, 0.38), (-1.14, 0.06, 1.55), bevel=0.03)
    box(iron, (0.04, 0.5, 0.04), (-1.13, 0.06, 1.77))
    box(iron, (0.05, 0.08, 0.05), (-1.15, 0.28, 1.74))

    # ---------------- caja de carga ----------------
    # vigas bajo piso
    for sx in (-0.78, 0.78):
        box(iron, (0.1, 3.2, 0.12), (sx, (BED_Y0 + BED_Y1) / 2, 1.13), bevel=0.01)
    for yy in [BED_Y0 + 0.1 + i * 0.5 for i in range(7)]:
        box(iron, (1.95, 0.07, 0.09), (0, yy, 1.145), bevel=0.01)
    # piso: tablones a lo largo de Y
    nplank = 9
    pw = (2 * BED_HX) / nplank
    for i in range(nplank):
        x = -BED_HX + pw * (i + 0.5)
        # algunos tablones cortados en dos tramos (junta)
        if rng.random() < 0.5:
            cut = rng.uniform(-1.9, -0.3)
            plank(wy, (x, BED_Y0, FLOOR_Z - 0.025), (x, cut - 0.01, FLOOR_Z - 0.025), pw - 0.01, 0.05, 0.003, rng, 0.01)
            plank(wy, (x, cut + 0.01, FLOOR_Z - 0.025 + rng.uniform(-0.004, 0.004)), (x, BED_Y1, FLOOR_Z - 0.025), pw - 0.01, 0.05, 0.003, rng, 0.01)
        else:
            plank(wy, (x, BED_Y0, FLOOR_Z - 0.025), (x, BED_Y1, FLOOR_Z - 0.025), pw - 0.01, 0.05, 0.004, rng, 0.012)
    # chapa metalica abollada sobre el piso (zona delantera) - ver abolladuras por ruido
    sheet = new_bm()
    n = 14
    gv = []
    for a in range(n + 1):
        row = []
        for b in range(n + 1):
            x = -0.55 + 1.1 * b / n
            y = -0.35 + 0.9 * a / n
            z = FLOOR_Z + 0.012 + noise.noise(Vector((x * 3.0, y * 3.0, 1.0))) * 0.018
            row.append(sheet.verts.new((x, y, z)))
        gv.append(row)
    for a in range(n):
        for b in range(n):
            f = sheet.faces.new([gv[a][b], gv[a][b + 1], gv[a + 1][b + 1], gv[a + 1][b]]); f.smooth = True
    merge_bm(iron, sheet)

    # laterales: 3 hiladas de tablones, tramos escalonados
    row_h = 0.215
    for sx in (-1, 1):
        xo = sx * (BED_HX + 0.025)
        for r in range(3):
            zc = FLOOR_Z + row_h * (r + 0.5) + 0.004 * r
            y = BED_Y0
            # tramos desfasados por hilada
            cuts = sorted([BED_Y0 + rng.uniform(0.9, 2.2) for _ in range(rng.randint(1, 2))])
            pts = [BED_Y0] + cuts + [BED_Y1]
            for a_, b_ in zip(pts[:-1], pts[1:]):
                plank_side = (xo, a_ + 0.006, zc), (xo, b_ - 0.006, zc)
                # tablones de costado: ancho (altura) en Z, espesor en X -> usamos plank con 'ancho' en Z via up hint
                _side_plank(wy, plank_side[0], plank_side[1], row_h - 0.022, 0.05, rng)
        # postes de hierro
        for yy in (BED_Y0 + 0.02, -1.75, -0.95, -0.15, BED_Y1 - 0.02):
            box(iron, (0.05, 0.075, 0.82), (sx * (BED_HX + 0.065), yy, 1.56), bevel=0.006)
            box(iron, (0.06, 0.1, 0.05), (sx * (BED_HX + 0.065), yy, 1.2))
        box(iron, (0.07, 3.1, 0.06), (sx * (BED_HX + 0.065), (BED_Y0 + BED_Y1) / 2, SIDE_TOP + 0.01), bevel=0.008)
        box(iron, (0.05, 3.1, 0.05), (sx * (BED_HX + 0.065), (BED_Y0 + BED_Y1) / 2, 1.27), bevel=0.006)
        # enchufes de los arcos
        for ya in ARCH_Y:
            cyl(iron, 0.032, 0.026, 0.12, (sx * (BED_HX + 0.065), ya, SIDE_TOP + 0.08), (0, 0, 0), sides=8)
    # cabecera (frente de caja)
    for r in range(3):
        zc = FLOOR_Z + row_h * (r + 0.5) + 0.004 * r
        _front_plank(wx, (-BED_HX, BED_Y1 - 0.025, zc), (BED_HX, BED_Y1 - 0.025, zc), row_h - 0.012, 0.05, rng)
    box(iron, (2.1, 0.09, 0.06), (0, BED_Y1 - 0.03, SIDE_TOP + 0.01))

    # compuerta trasera abatida (horizontal), tablones a lo largo de X
    gate_y0, gate_y1 = BED_Y0 - 0.01, BED_Y0 - 0.74
    for r in range(3):
        yc = gate_y0 - 0.23 * (r + 0.5) - 0.0
        plank(wx, (-BED_HX - 0.02, yc, FLOOR_Z - 0.025), (BED_HX + 0.02, yc, FLOOR_Z - 0.025), 0.222, 0.05, 0.003, rng, 0.015)
    for sx in (-1, 1):
        box(iron, (0.06, 0.74, 0.07), (sx * (BED_HX + 0.03), (gate_y0 + gate_y1) / 2, FLOOR_Z - 0.07), bevel=0.008)
        box(iron, (0.06, 0.06, 0.1), (sx * (BED_HX + 0.03), gate_y0 + 0.01, FLOOR_Z - 0.08))
    box(iron, (1.95, 0.06, 0.07), (0, gate_y1 + 0.03, FLOOR_Z - 0.075), bevel=0.008)
    # cadenas de la compuerta
    for sx in (-1, 1):
        a = Vector((sx * (BED_HX + 0.02), gate_y1 + 0.05, FLOOR_Z - 0.03))
        b = Vector((sx * (BED_HX + 0.075), BED_Y0 + 0.06, 1.7))
        pts = [a.lerp(b, i / 12) + Vector((0, -0.05 * math.sin(math.pi * i / 12), -0.04 * math.sin(math.pi * i / 12))) for i in range(13)]
        for p in pts:
            sphere(iron, 0.017, p, (1, 1.6, 1), seg=6, rings=4)
        tube(iron, pts, 0.007, sides=4, caps=False)
    # astillas
    for _ in range(26):
        x = rng.uniform(-0.95, 0.95)
        y = rng.choice([gate_y1 - 0.01, BED_Y0 - 0.01])
        zc = FLOOR_Z - 0.03 + rng.uniform(-0.01, 0.01)
        cyl(wx, 0.012, 0.0, 0.09, (x, y - 0.04 * (1 if y < BED_Y0 - 0.5 else 0.3), zc), (math.pi / 2, 0, rng.uniform(-0.3, 0.3)), sides=4)

    # ---------------- arcos del toldo ----------------
    arch = new_bm()
    for ya in ARCH_Y:
        pts = []
        for i in range(25):
            th = math.pi - math.pi * i / 24
            pts.append(Vector(((RX - 0.015) * math.cos(th) * 0.98, ya, CZ + (RZ - 0.015) * math.sin(th))))
        pts = [Vector((-(BED_HX + 0.065), ya, SIDE_TOP + 0.06)), Vector((-(BED_HX + 0.065) + 0.0, ya, SIDE_TOP + 0.14))] + pts[1:-1] + \
              [Vector(((BED_HX + 0.065), ya, SIDE_TOP + 0.14)), Vector(((BED_HX + 0.065), ya, SIDE_TOP + 0.06))]
        tube(arch, pts, 0.017, sides=8)
    # largueros longitudinales (tablillas)
    for th_deg in (35, 90, 145):
        th = math.radians(th_deg)
        pts = [Vector(((RX - 0.015) * math.cos(th), ya, CZ + (RZ - 0.015) * math.sin(th))) for ya in ARCH_Y]
        tube(arch, pts, 0.012, sides=5, caps=False)

    # ---------------- lona ----------------
    bmc = new_bm()
    canvas_mesh(rng, bmc)
    rc = new_bm()
    rear_curtain(rng, rc)
    merge_bm(bmc, rc)
    # sogas de amarre del toldo
    for sx in (-1, 1):
        for yy in (-2.2, -1.5, -0.8, -0.1):
            P = canvas_point(1 if sx < 0 else len(CS_PTS) - 2, yy, 0.0)
            tube(rope, [P + Vector((0, 0, 0.02)), P + Vector((sx * 0.04, 0, -0.1)), Vector((sx * (BED_HX + 0.11), yy, 1.42))], 0.008, sides=5)
    # soga atando el faldon trasero
    for sx in (-1, 1):
        tube(rope, [Vector((sx * 0.95, -2.7, 2.45)), Vector((sx * 0.7, -2.74, 2.45)), Vector((sx * 0.65, -2.75, 2.55)), Vector((sx * 0.9, -2.7, 2.62))], 0.01, sides=5)

    # ---------------- estarcido militar ----------------
    # "E.A." sobre el costado del capo (se aproxima con cajas estilo esténcil)
    def letter_box(bmx, x, y, z, s=1.0):
        box(bmx, (0.02, 0.06 * s, 0.015 * s), (x, y, z))
    for k, (dy, dz, sy, sz) in enumerate([(0, 0, 0.02, 0.12), (0.04, 0.05, 0.08, 0.02), (0.04, 0, 0.06, 0.02), (0.04, -0.05, 0.08, 0.02),
                                          (0.14, -0.06, 0.03, 0.03)]):
        box(stencil, (0.01, sy, sz), (0.83, 1.6 + dy, 1.42 + dz))

    # ---------------- crear objetos ----------------
    def mk(name, bm, mat, smooth=True):
        o = obj_from_bm(name, bm, mat, CN, smooth=smooth, parent=root)
        return o
    out['paint'] = mk('CAMION_Carroceria', paint, M['paint'], False)
    out['iron'] = mk('CAMION_Chasis_Hierro', iron, M['iron'], False)
    out['black'] = mk('CAMION_Mecanica_Negra', black, M['black'])
    out['wy'] = mk('CAMION_Caja_Tablones', wy, M['wood_y'], False)
    out['wx'] = mk('CAMION_Compuerta_Tablones', wx, M['wood_x'], False)
    out['tire'] = mk('CAMION_Neumaticos', tire, M['rubber'])
    out['rim'] = mk('CAMION_Llantas', rim, M['paint'])
    out['glass'] = mk('CAMION_Vidrios', glass, M['glass'], False)
    out['head'] = mk('CAMION_Faros', head, M['head'], False)
    out['tail'] = mk('CAMION_LucesTraseras', tail, M['tail'], False)
    out['rope'] = mk('CAMION_Sogas', rope, M['rope'])
    out['plate'] = mk('CAMION_Patente', plate, M['plate'], False)
    out['stencil'] = mk('CAMION_Estarcido', stencil, M['stencil'], False)
    out['arch'] = mk('CAMION_Arcos_Toldo', arch, M['iron'])
    out['canvas'] = mk('CAMION_Toldo_Lona', bmc, [M['canvas'], M['patch']])
    # luces
    for sx in (-1, 1):
        ld = bpy.data.lights.new('LUZ_Faro_%d' % sx, 'SPOT')
        ld.color = (1.0, 0.82, 0.55)
        ld.energy = 900
        ld.spot_size = math.radians(55)
        ld.spot_blend = 0.6
        ld.shadow_soft_size = 0.08
        try:
            ld.volume_factor = 1.0
        except Exception:
            pass
        lo = bpy.data.objects.new('LUZ_Faro_%d' % sx, ld)
        coll(CN).objects.link(lo)
        lo.location = (sx * 0.53, 3.2, 1.40)
        lo.rotation_euler = (math.radians(-90 + 8 + 0), 0, 0)   # apunta a +Y, levemente hacia abajo
        lo.rotation_euler = Vector((0, 1, -0.1)).to_track_quat('-Z', 'Y').to_euler()
        lo.parent = root
    for sx in (-1, 1):
        ld = bpy.data.lights.new('LUZ_Trasera_%d' % sx, 'POINT')
        ld.color = (1, 0.08, 0.03)
        ld.energy = 0.55
        ld.shadow_soft_size = 0.06
        lo = bpy.data.objects.new('LUZ_Trasera_%d' % sx, ld)
        coll(CN).objects.link(lo)
        lo.location = (sx * 0.78, -2.9, 0.9)
        lo.parent = root
    # apoyar las 4 ruedas en las huellas de barro del camino con leve inclinacion natural
    try:
        import env
        z_fl = env.terrain_h(-WHEEL_X, AXLE_F)[0]
        z_fr = env.terrain_h(+WHEEL_X, AXLE_F)[0]
        z_rl = env.terrain_h(-WHEEL_X, AXLE_R)[0]
        z_rr = env.terrain_h(+WHEEL_X, AXLE_R)[0]
        z_avg = 0.25 * (z_fl + z_fr + z_rl + z_rr)
        pitch = math.atan2(0.5 * (z_fl + z_fr) - 0.5 * (z_rl + z_rr), AXLE_F - AXLE_R)
        roll = -math.atan2(0.5 * (z_fr + z_rr) - 0.5 * (z_fl + z_rl), 2.0 * WHEEL_X)
        # WHEEL_Z - TIRE_R = -0.04; hundimos 0.03m en el barro blando
        root.location = (env.cx(0.0), 0.0, z_avg + 0.01)
        root.rotation_euler = (pitch, roll, 0.0)
    except Exception:
        pass
    return 'ok'


def _side_plank(bm, p0, p1, height, thick, rng):
    """tablon lateral: largo en Y, alto en Z, espesor en X"""
    p0 = Vector(p0); p1 = Vector(p1)
    L = abs(p1.y - p0.y)
    n = max(2, int(L / 0.35))
    rows = []
    for i in range(n + 1):
        t = i / n
        c = p0.lerp(p1, t)
        w = rng.uniform(-0.004, 0.004)
        h = height / 2
        th = thick / 2
        rows.append([bm.verts.new((c.x - th + w, c.y, c.z - h)), bm.verts.new((c.x + th + w, c.y, c.z - h)),
                     bm.verts.new((c.x + th + w, c.y, c.z + h)), bm.verts.new((c.x - th + w, c.y, c.z + h))])
    for r in range(n):
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
    for row in (rows[0], rows[-1]):
        for v in row:
            if rng.random() < 0.6:
                v.co.y += rng.uniform(-0.012, 0.012)


def _front_plank(bm, p0, p1, height, thick, rng):
    p0 = Vector(p0); p1 = Vector(p1)
    n = 6
    rows = []
    for i in range(n + 1):
        t = i / n
        c = p0.lerp(p1, t)
        h = height / 2
        th = thick / 2
        rows.append([bm.verts.new((c.x, c.y - th, c.z - h)), bm.verts.new((c.x, c.y + th, c.z - h)),
                     bm.verts.new((c.x, c.y + th, c.z + h)), bm.verts.new((c.x, c.y - th, c.z + h))])
    for r in range(n):
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

