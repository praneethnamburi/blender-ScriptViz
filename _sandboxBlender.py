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
from copy import deepcopy
from importlib import reload

reload(bpn.turtle)
reload(bpn)

bpn.env.reset()

def normal2tfmat(n):
    n = n/np.linalg.norm(n)
    nx = n[0]
    ny = n[1]
    nz = n[2]
    d = np.sqrt(1-nx**2)
    m = np.array([\
        [d, 0, nx],\
        [-nx*ny/d, nz/d, ny],\
        [-nx*nz/d, -ny/d, nz]\
        ])
    return m

θ = np.radians(np.arange(0, 360*2+40, 40))
z = np.sin(θ)
y = np.cos(θ)
x = θ/2

pts = np.array([np.array((tx, ty, tz)) for tx, ty, tz in zip(x, y, z)])

normals = np.vstack((pts[1, :] - pts[0, :], pts[2:, :] - pts[:-2, :], pts[-1, :] - pts[-2, :]))

a = bpn.Draw('follow')
for i in range(np.shape(pts)[0]):
    if i == 0:
        tc = a.ngon(n=6, r=0.3)
        vertpos_orig = []
        for v in tc.v:
            vertpos_orig.append(deepcopy(v.co))
    else:
        tc = a.extrude(tc.e)
    tfmat = normal2tfmat(normals[i, :])
    for v, v_orig in zip(tc.v, vertpos_orig):
        v.co = mathutils.Vector(tfmat@np.array(v_orig))
    tc.center = pts[i, :]
strand = +a
strand.shade('smooth')
strand.subsurf(2, 2)

# pts = [(0, 0, 0), (0, 1, 1), (2, 2, 2)]

# a = bpn.Draw('follow')
# tc = a.ngon(n=4, r=0.5)
# tc2 = a.extrude(tc.e)
# p2 = np.array(pts[1])
# p1 = np.array(pts[0])
# tfmat = normal2tfmat(p2-p1)
# for v in tc2.v:
#     v.co = mathutils.Vector(tfmat@np.array(v.co))
# tc2.center = pts[1]

# tc2 = a.extrude(tc2.e)
# tfmat = normal2tfmat(np.array(pts[2]) - np.array(pts[1]))
# for v, v_orig in zip(tc2.v, tc.v):
#     v.co = mathutils.Vector(tfmat@np.array(v_orig.co))
# tc2.center = pts[2]

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
