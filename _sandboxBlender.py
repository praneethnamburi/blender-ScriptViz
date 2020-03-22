# context.area: VIEW_3D
"""
This is a sandbox. Develop code here!
"""
#-----------------
import math
import os
import sys
import numpy as np

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '.'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

# import pntools as pn
import bpn # pylint: disable=unused-import
import bpy #pylint: disable=import-error

bpn.env.reset()
#-----------------

import bmesh #pylint: disable=import-error

import mathutils #pylint: disable=import-error

from importlib import reload
reload(bpn.turtle)
reload(bpn)

bpn.env.reset()

pts = [(0, 0, 0), (0, 0, 1), (2, 0, 2)]

a = bpn.Draw('follow')
tc = a.ngon(n=4, r=1)
for pt in pts[1:]:
    tc = a.extrude(tc.e)
    print(tc.vef)
    tc.center = pt
    
print(a.all_geom)
# out1 = bmesh.ops.create_circle(a.bm, cap_ends=False, radius=0.2, segments=10)
+a

# for p in tor.bm.polygons:
#     p.use_smooth = True
# a.bm.faces.new(a.bm.verts[:])

# # Now we have made a links of the chain, make a copy and rotate it
# # (so this looks something like a chain)

# ret = bmesh.ops.duplicate(
#     a.bm,
#     geom=a.bm.verts[:] + a.bm.edges[:] + a.bm.faces[:])
# geom_dupe = ret["geom"]
# verts_dupe = [ele for ele in geom_dupe if isinstance(ele, bmesh.types.BMVert)]
# del ret

# # position the new link
# bmesh.ops.translate(
#     a.bm,
#     verts=verts_dupe,
#     vec=(0.0, 0.0, 2.0))
# bmesh.ops.rotate(
#     a.bm,
#     verts=verts_dupe,
#     cent=(0.0, 1.0, 0.0),
#     matrix=mathutils.Matrix.Rotation(math.radians(90.0), 3, 'Z'))



# # test Draw - basic
# a = bpn.Draw()
# bmesh.ops.create_circle(a.bm, cap_ends=False, radius=0.2, segments=10)
# -a
