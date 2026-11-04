import bpy, sys
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
out = argv[0] if argv else r'd:\jeugosnacho\build\test.png'
camname = argv[1] if len(argv) > 1 else None
pct = int(argv[2]) if len(argv) > 2 else 50
samples = int(argv[3]) if len(argv) > 3 else 24
sc = bpy.context.scene
if camname:
    sc.camera = bpy.data.objects[camname]
sc.render.resolution_percentage = pct
sc.eevee.taa_render_samples = samples
sc.render.filepath = out
sc.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(write_still=True)
print('RENDER_DONE', out)

