"""
Support for nutations.
"""

import os
import sys
import numpy as np # pylint: disable=unused-import

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../..'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

import bpn # pylint: disable=unused-import

bpy = bpn.bpy

# # in general, ops seems to be causing crashes
# bpy.ops.mesh.primitive_cube_add(location=(1.0, 0.0, 0.0))

# m = bpn.Msh('Cube')
# m.v = m.v*2

# # To set the current keyframe
# bpy.context.scene.frame_set(160)

# # To get the current object location
# o = bpn.getObj('Talus_R')
# print(o.location)

FRAME_INIT = 1
FRAME_INRIGHT = 100
FRAME_OUTRIGHT = 200

import mathutils # pylint: disable=import-error
import pickle

def setOriginToCenter(objName):
    """Bring every bone's origin to center."""
    new_origin = mathutils.Vector(bpn.Msh(bpy.data.objects[objName]).center)
    bpy.data.objects[objName].data.transform(mathutils.Matrix.Translation(-new_origin))
    bpy.data.objects[objName].matrix_world.translation += new_origin

def locRotKeyFrame(objName, frameNum=1):
    """Set location and rotation keyframes for a given object."""
    bpy.data.objects[objName].keyframe_insert(data_path="location", frame=frameNum)
    bpy.data.objects[objName].keyframe_insert(data_path="rotation_euler", frame=frameNum)

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

def saveLocRot(collnames, frameSave, fname):
    """
    Save location and rotation information of objects.
    Crated to save weight in and weight out nutational positions of bones.
    Generalizes to saving location and rotation information for any mesh objects.

    Inputs:
        collnames: list, ['Foot_R', 'Leg_R', 'Spine']
    """
    bpy.context.scene.frame_set(frameSave)
    x = {}
    for collName in collnames:
        for obj in bpy.data.collections[collName].all_objects:
            if obj.type == 'MESH':
                x[obj.name] = [np.array(obj.location), np.array(obj.rotation_euler)]

    f = open(fname, "wb")
    pickle.dump(x, f)
    f.close()

# # bpy.ops.wm.open_mainfile(filepath="D:\\Dropbox (MIT)\\Anatomy\\Workspace\\Ultimate_Human_Anatomy_Rigged_Blend_2-81\\Nutations-1.blend", display_file_selector=False)
# collNames = ['Foot_R']
# for FRAME_SAVE in [120, 160]:
#     saveLocRot(collNames, FRAME_SAVE, "./apps/anatomy/Nutations_Frame" + str(FRAME_SAVE) +  ".pkl")

# bpy.ops.wm.open_mainfile(filepath="D:\\Dropbox (MIT)\\Anatomy\\Workspace\\Ultimate_Human_Anatomy_Rigged_Blend_2-81\\skeletalSystem.blend", display_file_selector=False)
# initBones()

fName = "./apps/anatomy/Nutations_Frame160.pkl"
targetFrame = FRAME_INRIGHT

bpy.context.scene.frame_set(targetFrame)
dct = pickle.load(open(fName, "rb"))
print(dct)
for objName in dct.keys():
    bpy.data.objects[objName].location = mathutils.Vector(dct[objName][0])
    bpy.data.objects[objName].rotation_euler = mathutils.Vector(dct[objName][1])
    locRotKeyFrame(objName, frameNum=targetFrame)
