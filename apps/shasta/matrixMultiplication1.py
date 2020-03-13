"""Demonstrate matrix multiplication on points using blender."""

# make sure you're in Object Mode in the 3D Viewport

import os
import sys
import numpy as np

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../..'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

import bpn # pylint: disable=unused-import

bpy = bpn.bpy
bpy.data.scenes['Scene'].cursor.location[0] = -100

origin = [0, 0, 0]
v1 = [1, 2, 0]

# Exercises
# 1. Make the vector in orange twice its size
# 2. Scale only the X axis by a factor of 2
# 3. Rotate the vector by 90 degrees
# 4. Rotate the vector by a given angle theta
# 5. Reflect the vector along the line x=y
m1 = np.array([\
    [1, 0, 0],\
    [0, 1, 0],\
    [0, 0, 0]\
    ])

v2 = m1@v1

verts = {'v1': v1, 'v2':v2}

for vertName, vertPos in verts.items():
    try:
        vMsh = bpn.Msh(name=vertName)
        coords = vMsh.v
        vMsh.v = np.array([origin, vertPos])
    except:
        vMsh = bpn.Msh(x=[origin[0], vertPos[0]], y=[origin[1], vertPos[1]], z=[origin[2], vertPos[2]], name=vertName)
