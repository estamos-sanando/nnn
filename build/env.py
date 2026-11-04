"""Entorno: camino de tierra, zanjas, pastizal, zarzas, bosque, instalacion militar lejana, postes."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, noise
from common import *

CNAME = 'Entorno'


def cx(y):
    t = max(y - 6.0, 0.0)
    return -0.0035 * t * t + 0.35 * math.sin(0.09 * t)


def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def terrain_h(u, y):
    """altura del terreno en coordenadas de camino (u = distancia lateral al eje del camino)"""
    au = abs(u)
    # relieve base suave
    h = noise.noise(Vector((u * 0.045, y * 0.045, 1.7))) * 0.9
    h += noise.noise(Vector((u * 0.17, y * 0.17, 9.1))) * 0.18
    # corona del camino
    if au < 2.9:
        h += 0.07 * (1 - (au / 2.9) ** 2)
    ruts = 0.0
    # huellas profundas (vehiculos pesados) con variacion a lo largo del camino
    var = 0.75 + 0.5 * (noise.noise(Vector((y * 0.21, 3.3, 0.0))) * 0.5 + 0.5)
    for off, depth, w in ((-0.90, 0.17, 0.25), (0.90, 0.17, 0.25), (-1.38, 0.07, 0.28), (1.45, 0.06, 0.3)):
        ww = w * (0.9 + 0.3 * noise.noise(Vector((y * 0.5, off * 3, 2.2))))
        d = depth * var * math.exp(-((u - off) / ww) ** 2)
        ruts += d
    h -= ruts
    # baches y erosion en las huellas
    h -= 0.05 * max(0.0, noise.noise(Vector((u * 1.3, y * 1.1, 4.4)))) * smoothstep(2.6, 1.0, au)
    h += 0.018 * noise.noise(Vector((u * 7.0, y * 7.0, 0.5)))
    # zanjas laterales
    for side in (-1, 1):
        dd = au - 3.7
        if side * u > 0:
            h -= 0.55 * math.exp(-(dd / 0.75) ** 2) * (0.8 + 0.4 * noise.noise(Vector((y * 0.2, side * 5, 0))))
            if au > 4.4:
                h += 0.40 * (1 - math.exp(-(au - 4.4) / 2.5))
    if au > 16:
        h += (au - 16) * 0.05 + noise.noise(Vector((u * 0.1, y * 0.1, 6.0))) * 0.6
    return h, ruts


def build_terrain():
    ys = []
    y = -70.0
    while y < -20: ys.append(y); y += 1.5
    while y < 30: ys.append(y); y += 0.25
    while y <= 90: ys.append(y); y += 1.5
    us = []
    u = -60.0
    while u < -12: us.append(u); u += 2.0
    while u < -5: us.append(u); u += 0.5
    while u < 5: us.append(u); u += 0.1
    while u < 12: us.append(u); u += 0.5
    while u <= 60: us.append(u); u += 2.0
    bm = bmesh.new()
    lroad = bm.verts.layers.float.new('road')
    lwet = bm.verts.layers.float.new('wet')
    grid = []
    for y in ys:
        row = []
        for u in us:
            h, ruts = terrain_h(u, y)
            v = bm.verts.new((cx(y) + u, y, h))
            v[lroad] = 1.0 - smoothstep(2.6, 3.5, abs(u))
            v[lwet] = max(0.0, min(1.0, (ruts - 0.03) / 0.10))
            row.append(v)
        grid.append(row)
    for r in range(len(ys) - 1):
        for c in range(len(us) - 1):
            bm.faces.new([grid[r][c], grid[r][c + 1], grid[r + 1][c + 1], grid[r + 1][c]])
    mat = mat_terrain()
    o = obj_from_bm('TERRENO_Camino', bm, mat, CNAME, smooth=True)
    return o


def mat_terrain():
    mb = MB('MAT_Terreno_BarroHumedo')
    vec = mb.tc('Object')
    road = mb.attr('road')
    wet = mb.attr('wet')
    n_big = mb.noise(0.35, 6, 0.6)
    n_mid = mb.noise(4.0, 7, 0.6)
    n_fine = mb.noise(60.0, 4, 0.5)
    mud_col = mb.mixc(mb.ramp(n_mid, [(0.3, (0, 0, 0, 1)), (0.7, (1, 1, 1, 1))]), srgb('#2f2316'), srgb('#5a4630'))
    mud_col = mb.mixc(mb.maprange(n_big, 0.35, 0.7, 0.0, 0.5), mud_col, srgb('#6d5a40'))   # tierra seca clara
    grass_col = mb.mixc(mb.ramp(n_mid, [(0.3, (0, 0, 0, 1)), (0.7, (1, 1, 1, 1))]), srgb('#17140a'), srgb('#2e2a14'))
    col = mb.mixc(road, grass_col, mud_col)
    col = mb.mixc(wet, col, srgb('#120c06'))      # barro empapado en las huellas
    pebble = mb.vor(38.0, 1.0)
    peb_m = mb.maprange(pebble, 0.18, 0.05, 0.0, 1.0)
    col = mb.mixc(mb.math('MULTIPLY', peb_m, mb.math('MULTIPLY', road, 0.5)), col, srgb('#7a6e5c'))
    rough = mb.mixf(road, 0.92, 0.80)
    rough = mb.mixf(wet, rough, 0.08)       # charcos/brillo en huellas
    spec = mb.mixf(wet, 0.18, 0.65)
    # huellas de neumatico (tacos) en los bordes humedos, agua lisa en el fondo del charco
    puddle_flat = mb.maprange(wet, 0.55, 0.95, 1.0, 0.08)
    tread = mb.wave(24.0, 1.2, 0.0, vec=mb.map(scale=(1, 1, 1)), direction='Y', profile='SAW')
    tread = mb.math('MULTIPLY', tread, mb.math('MULTIPLY', mb.maprange(wet, 0.15, 0.55, 0.0, 1.0), puddle_flat))
    h = mb.math('ADD', mb.math('MULTIPLY', n_fine, 0.6), mb.math('MULTIPLY', mb.maprange(pebble, 0.0, 0.3, 0.0, 1.0), 0.4))
    h = mb.math('MULTIPLY', h, puddle_flat)
    h = mb.math('ADD', h, mb.math('MULTIPLY', tread, 0.55))
    nrm = mb.bump(h, mb.mixf(wet, 0.85, 0.18), 0.04)
    mb.set(Base_Color=col, Roughness=rough, Specular_IOR_Level=spec, Normal=nrm)
    return mb.done()


# ----------------------------------------------------------------------------
# Pastizal / malezas
# ----------------------------------------------------------------------------
def mat_grass():
    mb = MB('MAT_Pastizal_Seco')
    tt = mb.attr('tt')
    n = mb.noise(1.3, 4, 0.5)
    base = mb.mixc(n, srgb('#3a3216'), srgb('#6b5a2a'))
    tip = mb.mixc(n, srgb('#7d6c3a'), srgb('#a08c50'))
    col = mb.mixc(tt, base, tip)
    col = mb.mixc(mb.noise(30, 3, 0.5), col, srgb('#1f1b0c'))
    mb.set(Base_Color=col, Roughness=0.85)
    # ligera translucidez de hojas secas
    try:
        mb.set(Subsurface_Weight=0.1)
    except Exception:
        pass
    mb.m.use_backface_culling = False
    return mb.done()


def blade(bm, base, height, width, bend_dir, bend, lt, segs=3):
    ring = []
    for i in range(segs + 1):
        t = i / segs
        w = width * (1 - t) ** 0.8 * (1 if i < segs else 0.0)
        p = base + Vector((0, 0, height * t)) + bend_dir * (bend * t * t * height)
        p.z = base.z + height * t * (1 - 0.25 * bend * t)
        side = Vector((-bend_dir.y, bend_dir.x, 0)) * w
        ring.append((p, side, t))
    verts = []
    for i, (p, side, t) in enumerate(ring):
        if i == segs:
            v = bm.verts.new(p); v[lt] = 1.0
            verts.append((v, None))
        else:
            a = bm.verts.new(p - side); a[lt] = t
            b = bm.verts.new(p + side); b[lt] = t
            verts.append((a, b))
    for i in range(segs):
        a0, b0 = verts[i]
        a1, b1 = verts[i + 1]
        if b1 is None:
            bm.faces.new([a0, b0, a1])
        else:
            bm.faces.new([a0, b0, b1, a1])


def build_grass(count_near=5200, seed=3):
    rng = random.Random(seed)
    mat = mat_grass()
    chunks = {}
    placed = 0
    tries = 0
    while placed < count_near and tries < count_near * 20:
        tries += 1
        y = rng.uniform(-14, 10) if rng.random() < 0.6 else rng.uniform(-22, 40)
        u = rng.choice([-1, 1]) * (abs(rng.gauss(0, 1)) * 5.5 + 1.1)
        au = abs(u)
        if au > 22:
            continue
        # el centro del camino (entre huellas) solo con yuyos ralos
        if au < 2.8 and abs(abs(u) - 0.9) < 0.4:
            continue
        dens = smoothstep(1.0, 3.2, au)
        if au < 2.8 and rng.random() > 0.25:
            continue
        if rng.random() > dens + 0.1:
            continue
        x = cx(y) + u
        h, ruts = terrain_h(u, y)
        key = (int((x + 60) // 20), int((y + 70) // 25))
        bm = chunks.get(key)
        if bm is None:
            bm = bmesh.new()
            bm.verts.layers.float.new('tt')
            chunks[key] = bm
        lt = bm.verts.layers.float['tt']
        pasto = au > 2.8
        nb = rng.randint(5, 9)
        hmax = rng.uniform(0.55, 1.25) if pasto else rng.uniform(0.15, 0.4)
        for _ in range(nb):
            a = rng.uniform(0, 2 * math.pi)
            r = rng.uniform(0, 0.09)
            base = Vector((x + math.cos(a) * r, y + math.sin(a) * r, h - 0.02))
            ba = rng.uniform(0, 2 * math.pi)
            blade(bm, base, hmax * rng.uniform(0.6, 1.0), rng.uniform(0.007, 0.014),
                  Vector((math.cos(ba), math.sin(ba), 0)), rng.uniform(0.25, 0.7), lt)
        placed += 1
    objs = []
    for k, bm in chunks.items():
        o = obj_from_bm('PASTIZAL_%d_%d' % k, bm, mat, CNAME, smooth=True)
        objs.append(o)
    return objs


# ----------------------------------------------------------------------------
# Zarzas
# ----------------------------------------------------------------------------
def mat_bramble():
    return weathered('MAT_Zarza', srgb('#2b2113'), srgb('#4a3820'), rough=0.8, scale=8.0, bump=0.3, grime=0.3)


def mat_leaf():
    mb = MB('MAT_Hoja_Seca')
    n = mb.noise(6.0, 3, 0.5)
    mb.set(Base_Color=mb.mixc(n, srgb('#1d2412'), srgb('#4a4020')), Roughness=0.7)
    mb.m.use_backface_culling = False
    return mb.done()


def build_brambles(count=46, seed=11):
    rng = random.Random(seed)
    bm = bmesh.new()
    bml = bmesh.new()
    for _ in range(count):
        y = rng.uniform(-18, 32)
        side = rng.choice([-1, 1])
        u = side * rng.uniform(3.4, 5.6)
        x = cx(y) + u
        h, _r = terrain_h(u, y)
        n_c = rng.randint(6, 10)
        for _c in range(n_c):
            a0 = rng.uniform(0, 2 * math.pi)
            length = rng.uniform(0.9, 1.9)
            pts = []
            rad = []
            cur = Vector((x + rng.uniform(-0.1, 0.1), y + rng.uniform(-0.1, 0.1), h))
            dirv = Vector((math.cos(a0) * 0.6, math.sin(a0) * 0.6, 1.0)).normalized()
            for i in range(6):
                pts.append(cur.copy())
                rad.append(0.011 * (1 - i / 7.0))
                cur += dirv * length / 5
                dirv += Vector((0, 0, -0.35)) + Vector((rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15), 0))
                dirv.normalize()
                cur.z = max(cur.z, h + 0.05)
                # espinas / hojas
                if i >= 1 and rng.random() < 0.9:
                    for _l in range(2):
                        la = rng.uniform(0, 2 * math.pi)
                        s = rng.uniform(0.035, 0.07)
                        c = cur + Vector((math.cos(la) * 0.03, math.sin(la) * 0.03, rng.uniform(-0.02, 0.03)))
                        d1 = Vector((math.cos(la), math.sin(la), rng.uniform(-0.2, 0.4))) * s
                        d2 = Vector((-math.sin(la), math.cos(la), 0)) * s * 0.6
                        v = [bml.verts.new(c), bml.verts.new(c + d1 + d2), bml.verts.new(c + d1 * 1.6),
                             bml.verts.new(c + d1 - d2)]
                        try:
                            bml.faces.new(v)
                        except ValueError:
                            pass
            tube(bm, pts, rad, sides=4)
    o1 = obj_from_bm('ZARZAS_Cañas', bm, mat_bramble(), CNAME, smooth=False)
    o2 = obj_from_bm('ZARZAS_Hojas', bml, mat_leaf(), CNAME, smooth=False)
    return [o1, o2]


# ----------------------------------------------------------------------------
# Bosque (siluetas de arboles) + arbustos
# ----------------------------------------------------------------------------
def mat_bark():
    return weathered('MAT_Corteza', srgb('#17120c'), srgb('#2c241a'), rough=0.9, scale=4.0, bump=0.8, grime=0.5)


def mat_foliage():
    mb = MB('MAT_Follaje_Noche')
    n = mb.noise(2.5, 5, 0.6)
    n2 = mb.noise(28.0, 5, 0.65)
    col = mb.mixc(mb.ramp(n, [(0.3, (0, 0, 0, 1)), (0.7, (1, 1, 1, 1))]), srgb('#020503'), srgb('#081107'))
    col = mb.mixc(mb.maprange(n2, 0.4, 0.8, 0.0, 0.5), col, (0.002, 0.003, 0.002, 1))
    h = mb.math('ADD', mb.noise(14, 6, 0.65), mb.math('MULTIPLY', n2, 0.6))
    mb.set(Base_Color=col, Roughness=0.98, Specular_IOR_Level=0.03, Normal=mb.bump(h, 1.1, 0.08))
    return mb.done()


def tree(bmt, bmf, pos, rng, kind='euc'):
    x, y, z = pos
    H = rng.uniform(10.5, 18.5)
    lean = Vector((rng.uniform(-0.7, 0.7), rng.uniform(-0.7, 0.7), 0))
    pts = []
    rad = []
    n = 8
    for i in range(n):
        t = i / (n - 1)
        pts.append(Vector((x, y, z - 0.3)) + Vector((0, 0, H * t)) + lean * (t * t * 1.0))
        rad.append(0.36 * (1 - t) ** 0.85 + 0.04)
    tube(bmt, pts, rad, sides=7)
    # ramas principales + masas densas e irregulares de follaje (siluetas de eucaliptos/casuarinas)
    for _ in range(rng.randint(7, 11)):
        t = rng.uniform(0.32, 0.98)
        i = min(n - 2, int(t * (n - 1)))
        f = t * (n - 1) - i
        base = pts[i].lerp(pts[i + 1], f)
        a = rng.uniform(0, 2 * math.pi)
        L = rng.uniform(1.8, 3.8) * (1.35 - t * 0.45)
        tip = base + Vector((math.cos(a) * L, math.sin(a) * L, rng.uniform(0.1, 1.6)))
        tube(bmt, [base, base.lerp(tip, 0.5) + Vector((0, 0, 0.35)), tip], [0.08, 0.05, 0.02], sides=5)
        s = rng.uniform(1.1, 2.2)
        for _b in range(3):
            ico(bmf, 1.0, tip + Vector((rng.uniform(-1.1, 1.1), rng.uniform(-1.1, 1.1), rng.uniform(-0.8, 0.9))),
                (s * rng.uniform(0.85, 1.35), s * rng.uniform(0.85, 1.35), s * rng.uniform(0.55, 0.95)), sub=2, rnd=0.22, smooth=True,
                seed=rng.randint(0, 9999))
    # copa
    top = pts[-1]
    for _b in range(4):
        s = rng.uniform(1.4, 2.5)
        ico(bmf, 1.0, top + Vector((rng.uniform(-1.1, 1.1), rng.uniform(-1.1, 1.1), rng.uniform(-0.3, 1.1))),
            (s * rng.uniform(0.9, 1.3), s * rng.uniform(0.9, 1.3), s * 0.78), sub=2, rnd=0.22, smooth=True, seed=rng.randint(0, 9999))


def build_forest(seed=21):
    rng = random.Random(seed)
    groups = {}
    count = 0
    # anillo denso alrededor del camino
    attempts = 0
    while count < 80 and attempts < 2000:
        attempts += 1
        y = rng.uniform(-60, 88)
        side = rng.choice([-1, 1])
        d = 11 + abs(rng.gauss(0, 7))
        # delante del camino (donde el camino 'entra' al fondo) el bosque cierra el horizonte
        u = side * d
        x = cx(y) + u
        # no obstruir la instalacion militar (zona lejana a la izquierda): dejar claro alrededor de (-24, 72)
        if math.hypot(x + 22, y - 72) < 15:
            continue
        # no cerrar completamente la boca del camino (dejar un pasillo estrecho) pero si dar cuerpo detras
        h, _r = terrain_h(u, y)
        key = (0 if x < 0 else 1, 0 if y < 15 else 1)
        if key not in groups:
            groups[key] = (bmesh.new(), bmesh.new())
        tree(groups[key][0], groups[key][1], (x, y, h), rng)
        count += 1
    # muro de fondo
    for i in range(34):
        x = rng.uniform(-60, 60)
        y = rng.uniform(86, 95)
        if math.hypot(x + 22, y - 72) < 15:
            continue
        h, _r = terrain_h(x - cx(y), y)
        key = ('far', 0)
        if key not in groups:
            groups[key] = (bmesh.new(), bmesh.new())
        tree(groups[key][0], groups[key][1], (x, y, h), rng)
    # muro detras de la camara (cierre)
    for i in range(30):
        x = rng.uniform(-45, 45)
        y = rng.uniform(-68, -48)
        h, _r = terrain_h(x, y)
        key = ('back', 0)
        if key not in groups:
            groups[key] = (bmesh.new(), bmesh.new())
        tree(groups[key][0], groups[key][1], (x, y, h), rng)
    objs = []
    mb_, mf_ = mat_bark(), mat_foliage()
    for k, (bt, bf) in groups.items():
        objs.append(obj_from_bm('BOSQUE_Troncos_%s_%s' % k, bt, mb_, CNAME, smooth=True))
        objs.append(obj_from_bm('BOSQUE_Follaje_%s_%s' % k, bf, mf_, CNAME, smooth=True))
    return objs


def build_bushes(count=70, seed=33):
    rng = random.Random(seed)
    bm = bmesh.new()
    for _ in range(count):
        y = rng.uniform(-35, 50)
        side = rng.choice([-1, 1])
        u = side * (5.5 + abs(rng.gauss(0, 3.5)))
        x = cx(y) + u
        h, _r = terrain_h(u, y)
        s = rng.uniform(0.75, 1.5)
        n_clumps = rng.randint(3, 5)
        for _k in range(n_clumps):
            ox = rng.uniform(-0.55, 0.55) * s
            oy = rng.uniform(-0.55, 0.55) * s
            oz = rng.uniform(0.25, 0.75) * s
            rs = s * rng.uniform(0.45, 0.65)
            ico(bm, rs, (x + ox, y + oy, h + oz),
                (rng.uniform(0.9, 1.2), rng.uniform(0.9, 1.2), rng.uniform(0.8, 1.0)),
                sub=2, rnd=0.16, seed=rng.randint(0, 9999), smooth=True)
    return obj_from_bm('ARBUSTOS_Silvestres', bm, mat_foliage(), CNAME, smooth=True)


# ----------------------------------------------------------------------------
# Instalacion militar lejana + postes
# ----------------------------------------------------------------------------
def build_facility():
    bm = bmesh.new()
    bmw = bmesh.new()   # ventanas emisivas
    bml = bmesh.new()   # lamparas
    base = Vector((-24, 74, 0))
    h0, _ = terrain_h(base.x - cx(base.y), base.y)
    z0 = h0
    # barracas
    for i, (ox, oy, sx, sy, sz) in enumerate([(0, 0, 14, 5, 3.2), (-9, 8, 9, 4, 2.8), (10, 6, 7, 4.5, 3.0)]):
        box(bm, (sx, sy, sz), (base.x + ox, base.y + oy, z0 + sz / 2))
        box(bm, (sx + 0.6, sy + 0.6, 0.25), (base.x + ox, base.y + oy, z0 + sz + 0.1))
        for k in range(int(sx // 2.2)):
            wx = base.x + ox - sx / 2 + 1.2 + k * 2.2
            box(bmw, (0.9, 0.05, 0.9), (wx, base.y + oy - sy / 2 - 0.03, z0 + 1.7))
    # torre de vigilancia
    tx, ty = base.x + 20, base.y - 6
    for dx_, dy_ in ((-0.7, -0.7), (0.7, -0.7), (0.7, 0.7), (-0.7, 0.7)):
        box(bm, (0.16, 0.16, 8.0), (tx + dx_, ty + dy_, z0 + 4.0))
    box(bm, (2.2, 2.2, 0.2), (tx, ty, z0 + 8.0))
    box(bm, (2.0, 2.0, 1.2), (tx, ty, z0 + 8.8))
    box(bmw, (1.2, 0.05, 0.5), (tx, ty - 1.02, z0 + 8.9))
    box(bm, (2.6, 2.6, 0.15), (tx, ty, z0 + 9.5), bevel=0.02)
    # cerco perimetral con postes
    for i in range(36):
        px = base.x - 22 + i * 1.8
        py = base.y - 10
        hh, _ = terrain_h(px - cx(py), py)
        box(bm, (0.1, 0.1, 2.6), (px, py, hh + 1.3))
        box(bm, (1.8, 0.02, 0.02), (px + 0.9, py, hh + 2.3))
        box(bm, (1.8, 0.02, 0.02), (px + 0.9, py, hh + 1.4))
    # focos (sodio calido)
    for (lx, ly, lz) in [(base.x - 10, base.y - 8, 6.0), (base.x + 4, base.y - 8, 6.0), (base.x + 16, base.y - 8, 6.0), (tx, ty - 1.2, z0 + 9.2)]:
        box(bm, (0.12, 0.12, lz), (lx, ly, z0 + lz / 2))
        box(bml, (0.5, 0.3, 0.12), (lx, ly - 0.2, z0 + lz + 0.1))
    mat_b = weathered('MAT_Instalacion_Muro', srgb('#1a1c18'), srgb('#2a2b25'), rough=0.9, scale=2.0, bump=0.3)
    o1 = obj_from_bm('INSTALACION_Edificios', bm, mat_b, CNAME, smooth=False)
    o2 = obj_from_bm('INSTALACION_Ventanas', bmw, emit_mat('MAT_Ventana_Calida', srgb('#ff9a3c'), 6.0), CNAME, smooth=False)
    o3 = obj_from_bm('INSTALACION_Focos', bml, emit_mat('MAT_Foco_Sodio', srgb('#ffa64a'), 40.0), CNAME, smooth=False)
    # luces
    for (lx, ly, lz) in [(base.x - 10, base.y - 8, z0 + 5.9), (base.x + 4, base.y - 8, z0 + 5.9), (base.x + 16, base.y - 8, z0 + 5.9), (tx, ty - 1.2, z0 + 9.0)]:
        ld = bpy.data.lights.new('LUZ_Foco_%d' % int(lx), 'POINT')
        ld.color = (1.0, 0.55, 0.22)
        ld.energy = 9000
        ld.shadow_soft_size = 0.4
        lo = bpy.data.objects.new('LUZ_Foco_%d' % int(lx), ld)
        coll('Luces').objects.link(lo)
        lo.location = (lx, ly, lz)
    return [o1, o2, o3]


def mat_wood_pole():
    return weathered('MAT_Poste_Madera', srgb('#1c150e'), srgb('#3a2d1e'), rough=0.9, scale=3.0, bump=0.7, grime=0.6)


def build_poles():
    bm = bmesh.new()
    bmc = bmesh.new()
    pts_top = []
    for i, y in enumerate([-30, -14, 2, 18, 34, 50]):
        u = 5.8
        x = cx(y) + u
        h, _ = terrain_h(u, y)
        tube(bm, [Vector((x, y, h - 0.4)), Vector((x + 0.03, y, h + 4.5)), Vector((x + 0.06, y, h + 8.2))], [0.17, 0.14, 0.11], sides=8)
        box(bm, (0.12, 0.12, 0.12), (x, y, h + 8.0))
        box(bm, (2.0, 0.1, 0.1), (x, y, h + 7.7))
        for k in (-0.8, 0.0, 0.8):
            pts_top.append((i, k, Vector((x + k, y, h + 7.85))))
    for k in (-0.8, 0.0, 0.8):
        pts = [p for (i, kk, p) in pts_top if kk == k]
        for a, b in zip(pts[:-1], pts[1:]):
            mid = a.lerp(b, 0.5) - Vector((0, 0, 0.9))
            seg = []
            for j in range(9):
                t = j / 8
                p = a.lerp(b, t)
                p.z -= 0.9 * 4 * t * (1 - t)
                seg.append(p)
            tube(bmc, seg, 0.008, sides=3, caps=False)
    return [obj_from_bm('POSTES_Telegraficos', bm, mat_wood_pole(), CNAME, smooth=True),
            obj_from_bm('POSTES_Cables', bmc, black_mat('MAT_Cable'), CNAME, smooth=False)]


def build():
    clear_collection(CNAME)
    for o in [o for o in bpy.data.objects if o.name.startswith('LUZ_Foco')]:
        bpy.data.objects.remove(o, do_unlink=True)
    out = {}
    out['terreno'] = build_terrain()
    out['pasto'] = build_grass()
    out['zarzas'] = build_brambles()
    out['bosque'] = build_forest()
    out['arbustos'] = build_bushes()
    out['instalacion'] = build_facility()
    out['postes'] = build_poles()
    return out
