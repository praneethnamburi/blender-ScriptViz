"""Demonstrate matrix multiplication on points forming 2d objects using blender."""

import os
import sys
import numpy as np

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../..'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

import bpn # pylint: disable=unused-import

from importlib import reload

bpn = reload(bpn)
bpy = bpn.bpy
bpy.data.scenes['Scene'].cursor.location[0] = -100

try:
    msh = bpn.Msh(name='Plane')
except:
    bpn.new.circle(obj_name='Plane')
    msh = bpn.Msh(name='Plane')

msh.v = np.array([\
    [-1, -1, 0],\
    [1, -1, 0],\
    [-1, 1, 0],
    [1, 1, 0]\
    ])

coords = msh.v.T

# Exercises:
# 1. Stretch the square by 2 along the X axis
# 2. Rotate the square by 45 degrees
# 3. Is this the only way to rotate the square?
# 4. Shear the square
# 5. Make the square disappear.
m1 = np.array([\
    [1, 0, 0],\
    [0, 1, 0],\
    [0, 0, 1]\
    ])

newCoords = m1@coords

msh.v = newCoords.T
