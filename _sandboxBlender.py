import bpy #pylint: disable=import-error
# context.area: VIEW_3D
"""
This is a sandbox. Develop code here!
"""
#-----------------
import os
import sys
import numpy as np

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '.'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

import pntools as pn
import bpn # pylint: disable=unused-import

bpy = bpn.bpy
bpy.data.scenes['Scene'].cursor.location[0] = -10

bpn.env.reset()
#-----------------

import bmesh
import math
import mathutils

# Make a new BMesh
a = bpn.Draw()

# Add a circle XXX, should return all geometry created, not just verts.
bmesh.ops.create_circle(a.bm, radius=0.2, segments=10)

# Spin and deal with geometry on side 'a'
edges_start_a = a.bm.edges[:]
geom_start_a = a.bm.verts[:] + edges_start_a
ret = bmesh.ops.spin(
    a.bm,
    geom=geom_start_a,
    angle=math.radians(180.0),
    steps=10,
    axis=(1.0, 0.0, 0.0),
    cent=(0.0, 1.0, 0.0),
    use_duplicate=False)
edges_end_a = [ele for ele in ret["geom_last"]
               if isinstance(ele, bmesh.types.BMEdge)]
del ret

# Extrude and create geometry on side 'b'
ret = bmesh.ops.extrude_edge_only(
    a.bm,
    edges=edges_start_a)
geom_extrude_mid = ret["geom"]
del ret

# Collect the edges to spin XXX, 'extrude_edge_only' could return this.
verts_extrude_b = [ele for ele in geom_extrude_mid
                   if isinstance(ele, bmesh.types.BMVert)]
edges_extrude_b = [ele for ele in geom_extrude_mid
                   if isinstance(ele, bmesh.types.BMEdge) and ele.is_boundary]
bmesh.ops.translate(
    a.bm,
    verts=verts_extrude_b,
    vec=(0.0, 0.0, 1.0))

# Create the circle on side 'b'
ret = bmesh.ops.spin(
    a.bm,
    geom=verts_extrude_b + edges_extrude_b,
    angle=-math.radians(90.0),
    steps=8,
    axis=(1.0, 0.0, 0.0),
    cent=(0.0, 1.0, 1.0))
edges_end_b = [ele for ele in ret["geom_last"]
               if isinstance(ele, bmesh.types.BMEdge)]
del ret

# Bridge the resulting edge loops of both spins 'a & b'
bmesh.ops.bridge_loops(
    a.bm,
    edges=edges_end_a + edges_end_b)

# Now we have made a links of the chain, make a copy and rotate it
# (so this looks something like a chain)

ret = bmesh.ops.duplicate(
    a.bm,
    geom=a.bm.verts[:] + a.bm.edges[:] + a.bm.faces[:])
geom_dupe = ret["geom"]
verts_dupe = [ele for ele in geom_dupe if isinstance(ele, bmesh.types.BMVert)]
del ret

# position the new link
bmesh.ops.translate(
    a.bm,
    verts=verts_dupe,
    vec=(0.0, 0.0, 2.0))
bmesh.ops.rotate(
    a.bm,
    verts=verts_dupe,
    cent=(0.0, 1.0, 0.0),
    matrix=mathutils.Matrix.Rotation(math.radians(90.0), 3, 'Z'))

-a

# # test Draw - basic
# a = bpn.Draw()
# bmesh.ops.create_circle(a.a.bm, cap_ends=False, radius=0.2, segments=10)
# -a
