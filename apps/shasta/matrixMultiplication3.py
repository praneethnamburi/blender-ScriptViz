"""Demonstrate matrix multiplication on points forming 3d objects using blender."""

import os
import pickle
import sys
import numpy as np

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../..'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

import bpn # pylint: disable=unused-import
from importlib import reload

bpn = reload(bpn)
bpy = bpn.bpy
# bpy.data.scenes['Scene'].cursor_location[0] = -100

COORD_FILE = os.path.join(DEV_ROOT, '_temp/suzanneCoords.pkl')

try:
    msh = bpn.Msh(name='Suzy')
except:
    bpn.new.monkey()
    msh = bpn.Msh(name='Suzy')

if not os.path.exists(COORD_FILE):
    coords = msh.v
    with open(COORD_FILE, 'wb') as f:
        pickle.dump(coords, f)

# reset suzanne
# NOTE: If the file is not there, add suzanne manually and then run this script
with open(COORD_FILE, 'rb') as f:
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

# make sure you're in object mode
msh.v = newCoords.T

coords = msh.v
for i, co in enumerate(coords):
    coords[i] = coords[i] + 0.01*np.random.randn(3)
msh.v = coords

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
