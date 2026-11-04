import bpy, time, os
B = r'd:\jeugosnacho\build'


def bench(tag, fog=True, rt=True, vol_world=True, res=(480, 270), samples=4, tile='4', vsamples=32, out=None):
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.eevee.taa_render_samples = samples
    sc.eevee.use_raytracing = rt
    sc.eevee.volumetric_tile_size = tile
    sc.eevee.volumetric_samples = vsamples
    f = bpy.data.objects.get('FX_NieblaRasante')
    if f:
        f.hide_render = not fog
    w = bpy.data.worlds['Cielo_Nocturno']
    # conectar/desconectar volumen mundo
    out_n = [n for n in w.node_tree.nodes if n.type == 'OUTPUT_WORLD'][0]
    vol = [n for n in w.node_tree.nodes if n.type == 'VOLUME_SCATTER'][0]
    for l in list(out_n.inputs['Volume'].links):
        w.node_tree.links.remove(l)
    if vol_world:
        w.node_tree.links.new(vol.outputs['Volume'], out_n.inputs['Volume'])
    sc.render.filepath = out or (B + '\\bench_%s.png' % tag)
    t = time.time()
    bpy.ops.render.render(write_still=True)
    dt = time.time() - t
    open(B + '\\bench.txt', 'a').write('%s: %.1fs\n' % (tag, dt))
