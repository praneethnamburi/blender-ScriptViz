"""Demonstrate matrix multiplication on points forming 3d objects using blender."""

import os
import pickle
import sys
import numpy as np

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../..'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

import bpn # pylint: disable=unused-import

bpy = bpn.bpy
bpy.data.scenes['Scene'].cursor_location[0] = -100

try:
    msh = bpn.Msh('Suzanne')
except:
    bpn.addPrimitive(pType='monkey', location=(0.0, 0.0, 0.0))
    msh = bpn.Msh('Suzanne')

# reset suzanne
with open('./_temp/suzanneCoords.pkl', 'rb') as f:
    coords = pickle.load(f)
msh.v = coords

coords = msh.v.T

# Exercises:
# 1. Make the monkey look away
# 2. Make the monkey's face thin
# 3. make the monkey look around (chaining transforms)

m1 = np.array([\
    [1, 0, 0],\
    [0, 1, 0],\
    [0, 0, 1]\
    ])

newCoords = m1@coords

targetMode = 'OBJECT'
modeChangeFlag = False
if not bpy.context.object.mode == targetMode:
    current_mode = bpy.context.object.mode
    modeChangeFlag = True
    bpy.ops.object.mode_set(mode=targetMode)

msh.v = newCoords.T

if modeChangeFlag:
    bpy.ops.object.mode_set(mode=current_mode)

# coords = msh.v
# for i, co in enumerate(coords):
#     coords[i] = coords[i] + 0.01*np.random.randn(3)
# msh.v = coords

# try:
#     λ = bpy.lamb
# except:
#     λ = 0
# δλ = np.pi/6
# λ = λ + δλ
# m1 = np.array([\
#     [np.cos(λ), -np.sin(λ), 0],\
#     [np.sin(λ), np.cos(λ), 0],\
#     [0, 0, 1]\
#     ])
