import os
import sys
import numpy as np

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../..'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

import bpn # pylint: disable=unused-import

bpy = bpn.bpy

# # in general, ops seems to be causing crashes
# bpy.ops.mesh.primitive_cube_add(location=(1.0, 0.0, 0.0))

# m = bpn.Msh('Cube')
# m.v = m.v*2

# # To get the current object location
# bpy.context.scene.frame_set(160)
# o = bpn.getObj('Talus_R')
# print(o.location)

FRAME_INIT = 1
FRAME_INRIGHT = 100
FRAME_OUTRIGHT = 200

import mathutils

def setOriginToCenter(objName):
    new_origin = mathutils.Vector(bpn.Msh(bpy.data.objects[objName]).center)
    bpy.data.objects[objName].data.transform(mathutils.Matrix.Translation(-new_origin))
    bpy.data.objects[objName].matrix_world.translation += new_origin

def locRotKeyFrame(objName, frameNum=1):
    bpy.data.objects[objName].keyframe_insert(data_path="location", frame=frameNum)
    bpy.data.objects[objName].keyframe_insert(data_path="rotation_euler", frame=frameNum)

# run this code once after importing the skeletal system from ultimate human anatomy file
# I changed the rotation and the scale manually so the units make sense, and then ran this script
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        setOriginToCenter(obj.name)
        locRotKeyFrame(obj.name, FRAME_INIT)
        locRotKeyFrame(obj.name, FRAME_INRIGHT)
        locRotKeyFrame(obj.name, FRAME_OUTRIGHT)
