"""
Keyframe animation by reading data from an excel file.
"""

import os
import sys

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../..'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

# import numpy as np
# import pandas as pd
# from functools import partial
import bpn # pylint: disable=unused-import

from importlib import reload

bpn = reload(bpn)
bpn.new = reload(bpn.new)
bpy = bpn.bpy

# xl_name = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'keyframeSphereExample.xlsx'))
# bpn.new.sphere(obj_name='sphere', msh_name='sph', coll_name='myColl')
# bpn.animate_simple(xl_name)

# xl_name = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'armReach_ineffTrial.xlsx'))
# anim_data = pd.read_excel(xl_name, sheet_name='animation')

# # keyframe animation
# bpn.animate_simple(anim_data, propfunc=partial(bpn.new.sphere, **{'r':0.1, 'coll_name':'myColl', 'msh_name':'sph'}))

# # plot trajectories
# obj_names = anim_data['object'].unique()
# traj_coll_name = 'Trajectories'
# bpn.new.collection(traj_coll_name)
# for obj_name in obj_names:
#     p = np.array([eval(k) for k in anim_data.loc[anim_data['object'] == obj_name]['value']])
#     bpn.Msh(x=p[:, 0], y=p[:, 1], z=p[:, 2], name=obj_name+'_trajectory', coll_name=traj_coll_name)

# bpn.new.sphere(obj_name='sph30', msh_name='sp30', coll_name='myc', r=3, u=3, v=2)
# bpn.new.monkey(name='L', msh_name='M')
# bpn.new.sphere(name='Sph', r=2, u=6, v=8)
# bpn.new.cube(name='de', msh_name='e', size=0.4)
# bpn.new.cone(name='mycone', segments=4, diameter1=2, diameter2=2, depth=2*np.sqrt(2), cap_ends=True, cap_tris=False)
# bpn.new.cone(name='mycone')
# bpn.new.cone(name='mycone2', seg=3, d=1)
# bpn.new.cone(name='mycone2', seg=3, r1=3, r2=2, d=0, cap_ends=False)

# bpn.new.polygon(name='hex', seg=6)
# bpn.new.ngon(name='circle', coll_name='Collection', n=32, r1=1, r2=0)

# bpn.new.polygon(name='hex', seg=6)
# h = bpn.Msh(name='hex')

# #-------basic extrusion------- extend this!!
# bpn.new.circle(name='circle', n=6)
# h = bpn.Msh(name='circle')

# newV = h.v + np.array([1, 1, 1])
# v = [tuple(k) for k in np.concatenate([h.v, newV])]

# newE = h.e + h.nV
# connE = np.concatenate([[np.arange(0, h.nE)], [np.arange(0, h.nE) + h.nV]]).T
# e = [tuple(k) for k in np.concatenate([h.e, newE, connE])]

# connF = np.array([[connE[i, 0], connE[i, 1], connE[i+1, 1], connE[i+1, 0]] for i in np.arange(-1, np.shape(connE)[0]-1)])
# f = [tuple(k) for k in connF]

# bpn.Msh(name='hexCopy', v=v, e=e, f=f)

# # ------------assign vertices to groups
# get vertices in group
# verts_ig = [[v.index, [g.group for g in v.groups]] for v in m.bpy_msh.vertices]
# names of groups
# {k.index : k.name for k in o.vertex_groups}
# It looks like objects have the names of vertex groups, and meshes have the info for group membership of each vertex
# Vertex groups appear to ve a property of the object, rather than the mesh somehow. 
# Change bpn.Msh class to be an object 

# s = bpn.new.sphere(name='sphere')
# s.key(1)
# s.key(26)
# s.loc = (2, 2, 2)
# s.scl = (1, 0.2, 1) # this will be ignored
# s.key(26, 'l')
# s.key(51, 's', [(0.2, 1, 1)])


# set frame start, frame end, fps
