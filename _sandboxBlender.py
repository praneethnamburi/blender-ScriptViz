# context.area: VIEW_3D
"""
This is a sandbox. Develop code here!
"""
#-----------------
import math
import os
import sys
import inspect
import numpy as np

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '.'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

# import pntools as pn
import bpn # pylint: disable=unused-import
import pntools as pn
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

class Tube(bpn.Msh):
    def __init__(self, name=None, x=0, y=0, z=0, **kwargs):
        names, kwargs = bpn.utils.clean_names(name, kwargs, {'msh_name':'tube_msh', 'obj_name':'tube_obj', 'priority_obj':'new', 'priority_msh':'new'})
        kwargs_ngon, kwargs = pn.clean_kwargs(kwargs, {'n':6, 'r':0.3, 'theta_offset_deg':-1}, {'n':['segments', 'seg', 'u', 'n'], 'r':['radius', 'r'], 'theta_offset_deg':['theta_offset_deg', 'th', 'offset', 'th_off_deg']})
        kwargs_this, kwargs_bpnmsh = pn.clean_kwargs(kwargs, {'shade':'smooth', 'subsurf':True, 'subsurf_levels':2, 'subsurf_render_levels':2})
        
        spine = np.array([np.array((tx, ty, tz)) for tx, ty, tz in zip(x, y, z)])
        normals = np.vstack((spine[1, :] - spine[0, :], spine[2:, :] - spine[:-2, :], spine[-1, :] - spine[-2, :]))

        a = bpn.Draw(**names)
        a.skin(spine, **kwargs_ngon)
        a_exp = a.export()
        -a
        super().__init__(**{**names, **kwargs_bpnmsh})
        self.shade(kwargs_this['shade'])
        if kwargs['subsurf']:
            self.subsurf(kwargs_this['subsurf_levels'], kwargs_this['subsurf_render_levels'])

        self.xsec = [bpn.turtle.DirectedSubMsh(self, normals[i, :], **s) for i, s in enumerate(a_exp)]

θ = np.radians(np.arange(0, 360+40, 40))
z1 = np.sin(θ)
y1 = np.cos(θ)
x1 = θ/2

t = Tube('myTube', x=x1, y=y1, z=z1, n=4, th=0, shade='smooth', subsurf=True)
t.xsec[0].normal = (0, 0, 1)
t.xsec[-1].scale(3)
t.xsec[-1].normal = (0, 0, 1)
t.morph(frame_start=100)

# b[0].center = (0, 1, 0)

# print(a_exp[1].f_idx)
# print(all_callers)
# strand.v

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
