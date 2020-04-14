"""
Keyframe animation by reading data from an excel file.
"""

import os
import sys

from importlib import reload
import numpy as np
import copy
# import pandas as pd
# from functools import partial

import bpn # pylint: disable=unused-import
bpn = reload(bpn)
import bmesh # pylint: disable=import-error

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
# core.Collection(traj_coll_name)
# for obj_name in obj_names:
#     p = np.array([eval(k) for k in anim_data.loc[anim_data['object'] == obj_name]['value']])
#     bpn.Msh(x=p[:, 0], y=p[:, 1], z=p[:, 2], name=obj_name+'_trajectory', coll_name=traj_coll_name)


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

# Frame event handlers!------------

# bpn.env.reset()

# bpy.app.handlers.frame_change_pre.clear()

# sph = bpn.new.sphere(name='sphere').translate((-2, 0, 0))
# mky = bpn.new.monkey(name='suzy').translate((2, 0, 0))

# def flat_top(obj):
#     """
#     input: bpn.Msh object 
#     """
#     v_orig = obj.v
#     v_targ = copy.deepcopy(v_orig)
#     v_targ[v_targ[:, -1] > 0, -1] = 0

#     def my_handler(scene):
#         p = scene.frame_current/scene.frame_end
#         obj.v = (1-p)*v_orig + p*v_targ
#     bpy.app.handlers.frame_change_pre.append(my_handler)  

# flat_top(sph)
# flat_top(mky)

# ------------
bpn.env.reset()

s = bpn.demo.plane_slice()

def morph(obj):
    """
    input: bpn.Msh object 
    """
    v_orig = obj.vInit
    v_targ = obj.v

    def my_handler(scene):
        p = scene.frame_current/scene.frame_end
        obj.v = (1-p)*v_orig + p*v_targ
    bpy.app.handlers.frame_change_pre.append(my_handler)  

bpy.app.handlers.frame_change_pre.clear()
bpn.env.Key().lim = 1, 50
morph(s) 
