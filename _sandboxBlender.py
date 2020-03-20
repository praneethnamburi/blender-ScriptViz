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
from bpn.utils import geom2vef
import bpy #pylint: disable=import-error

bpn.env.reset()
#-----------------

import bmesh #pylint: disable=import-error

import mathutils #pylint: disable=import-error

from importlib import reload
reload(bpn)

bpn.env.reset()

# geom2vef = bpn.utils.geom2vef
# Make a new BMesh
a = bpn.Draw('link2')
bmesh.ops.create_circle(a.bm, radius=0.2, segments=6)
for vert in a.bm.verts[:]:
    vert.co += mathutils.Vector((0., -1., 0))

# a.bm.faces.new(a.bm.verts[:])

# Spin and deal with geometry on side 'a'
edges_start_a = a.bm.edges[:]
geom = a.spin(angle=np.pi, steps=12, axis='x', cent=(0., 0., 0.))

_, edges_end_a, _ = geom.vef

print(a.obj_name)

# Extrude and create geometry on side 'b'
# verts_extrude_b, edges_extrude_b, _ = a.extrude(a.geom_last[1])

# for vert in verts_extrude_b:
#     vert.co = vert.co + mathutils.Vector((0, 0, 1))

# # Create the circle on side 'b'
# _, edges_end_b, _ = geom2vef(bmesh.ops.spin(
#     a.bm,
#     geom=verts_extrude_b + edges_extrude_b,
#     angle=math.radians(180.0),
#     steps=8,
#     axis=(1.0, 0.0, 0.0),
#     cent=(0.0, 1.0, 1.0))['geom_last'])

# # Bridge the resulting edge loops of both spins 'a & b'
# bmesh.ops.bridge_loops(
#     a.bm,
#     edges=edges_start_a + edges_end_b)



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

lnk = +a

# # test Draw - basic
# a = bpn.Draw()
# bmesh.ops.create_circle(a.bm, cap_ends=False, radius=0.2, segments=10)
# -a
