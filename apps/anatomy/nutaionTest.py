"""
Support for nutations.
"""
from importlib import reload
import numpy as np # pylint: disable=unused-import
# import pandas as pd 

import bpn # pylint: disable=unused-import

bpn = reload(bpn)

bpy = bpn.bpy

# # in general, ops seems to be causing crashes
# bpy.ops.mesh.primitive_cube_add(location=(1.0, 0.0, 0.0))

# m = bpn.Msh('Cube')
# m.v = m.v*2

# # To set the current keyframe
# bpy.context.scene.frame_set(160)

# # To get the current object location
# talus = bpn.get('Talus_R')
# print(talus.loc)

FRAME_INIT = 1
FRAME_INRIGHT = 100
FRAME_OUTRIGHT = 200

import mathutils # pylint: disable=import-error

def setOriginToCenter(obj_name):
    """Bring every bone's origin to center."""
    new_origin = mathutils.Vector(bpn.Msh(bpy.data.objects[obj_name]).center)
    bpy.data.objects[obj_name].data.transform(mathutils.Matrix.Translation(-new_origin))
    bpy.data.objects[obj_name].matrix_world.translation += new_origin

def locRotKeyFrame(obj_name, frameNum=1):
    """Set location and rotation keyframes for a given object."""
    bpy.data.objects[obj_name].keyframe_insert(data_path="location", frame=frameNum)
    bpy.data.objects[obj_name].keyframe_insert(data_path="rotation_euler", frame=frameNum)

def initBones():
    """
    Run this code once after importing the skeletal system from ultimate human anatomy file.
    I changed the rotation and the scale manually so the units make sense, and then ran this script
    """
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            setOriginToCenter(obj.name)
            locRotKeyFrame(obj.name, FRAME_INIT)
            locRotKeyFrame(obj.name, FRAME_INRIGHT)
            locRotKeyFrame(obj.name, FRAME_OUTRIGHT)

# bpy.ops.wm.open_mainfile(filepath="D:\\Dropbox (MIT)\\Anatomy\\Workspace\\Ultimate_Human_Anatomy_Rigged_Blend_2-81\\skeletalSystem.blend", display_file_selector=False)
# initBones()

### Saving nutations to excel, and applying them in another blend file

# # (load skeletalSystem.blend in blender)
# fname = r'D:\Workspace\blenderPython\apps\anatomy\nutations.xlsx'
# p2 = bpn.readattr('Skeletal_Sys', [1, 100], ['location', 'rotation_euler'], fname)

# (load skeletalSystem_originAtCenter_bkp02.blend)
fname = r'D:\Workspace\blenderPython\apps\anatomy\nutations.xlsx'
bpn.animate_simple(fname)
