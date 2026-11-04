import sys, os, time, shutil

B = r'd:\jeugosnacho\build'
if B not in sys.path:
    sys.path.insert(0, B)

import bpy
import common
import env
import truck
import captives
import props
import fx
import assemble

print("--- 1. Rebuilding Environment (Smooth foliage, rounded bushes) ---")
t0 = time.time()
env.build()
print("Env built in %.1fs" % (time.time() - t0))

print("--- 2. Rebuilding Truck (Rounded cab, vintage fenders, cloth toldo) ---")
t0 = time.time()
truck.build()
print("Truck built in %.1fs" % (time.time() - t0))

print("--- 3. Rebuilding Captives (Burlap sack ears, organic anatomy) ---")
t0 = time.time()
captives.build()
print("Captives built in %.1fs" % (time.time() - t0))

print("--- 4. Rebuilding Props ---")
t0 = time.time()
props.build()
print("Props built in %.1fs" % (time.time() - t0))

print("--- 5. Rebuilding FX ---")
t0 = time.time()
fx.build()
print("FX built in %.1fs" % (time.time() - t0))

print("--- 6. Saving & Exporting GLB ---")
t0 = time.time()
assemble.save_and_export()
print("Assemble & Export completed in %.1fs" % (time.time() - t0))

src_glb = r'd:\jeugosnacho\escena1_el_traslado.glb'
dst_glb = r'd:\jeugosnacho\public\escena1_el_traslado.glb'
shutil.copy2(src_glb, dst_glb)
print("Copied to %s (size: %.1f MB)" % (dst_glb, os.path.getsize(dst_glb) / 1048576))
print("ALL_REBUILD_SUCCESSFUL")

