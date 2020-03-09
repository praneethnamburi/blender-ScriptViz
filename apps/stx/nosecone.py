# context.area: VIEW_3D
"""Nose cone modifications for the marmoset stereotax."""

import os
import sys

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../..'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

import bpn # pylint: disable=unused-import

from importlib import reload
bpn = reload(bpn)

bpy = bpn.bpy
bpy.data.scenes['Scene'].cursor_location[0] = -100

bpn.reset_blender()
import numpy as np

# load the original eyebar mesh from Gilbert Menon 2019
nosecone_path = os.path.realpath(r"D:\GDrive Columbia\issalab_data\Marmoset stereotax\pn\NoseConeGM2019.stl")
out1 = bpn.loadSTL(nosecone_path)

ncObj = out1['objects'][0]
m = bpn.Msh(out1['meshes'][0])

ncObj.name = 'NoseCone'
m.bpy_msh.name = 'NoseCone'

bpn.shade('WIREFRAME')

print(dir(bpy))

# p_xlim = (23, 31)
# p_ylim = (54, 62)

# coords = m.v
# # mods go in here
# m.v = coords

# my_areas = bpy.data.screens['Layout'].areas
# my_shading = 'WIREFRAME'  # 'WIREFRAME' 'SOLID' 'MATERIAL' 'RENDERED'

# for area in my_areas:
#     # print(dir(area))
#     for space in area.spaces:
#         print(area.type, space.type)
#         if space.type == 'VIEW_3D' and area.type == 'VIEW_3D':
#             space.shading.type = my_shading

# for window in bpy.context.window_manager.windows:
#     screen = window.screen

#     for area in screen.areas:
#         for space in area.spaces:
#             if space.type == 'VIEW_3D' and area.type == 'VIEW_3D':
#                 override = {'window': window, 'screen': screen, 'space': space, 'area': area}
#                 bpy.ops.object.mode_set(mode='OBJECT', window=window, screen=screen, space=space, area=area)
#                 break

# import bmesh
# m = bpn.Msh('NoseCone')
# bpy.ops.object.mode_set(mode='EDIT')
# bm = bmesh.from_edit_mesh(m.bpyMsh)
# verts = [v for v in bm.verts if v.co[2] > 20]
# bmesh.ops.delete(bm, geom=verts, context='VERTS')
# bmesh.update_edit_mesh(m.bpyMsh)
# bpy.ops.object.mode_set(mode='OBJECT')
