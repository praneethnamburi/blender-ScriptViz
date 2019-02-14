import os
import sys
import numpy as np

import bpn # pylint: disable=unused-import

if os.path.dirname(os.path.realpath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))

# add modules here
bpy = bpn.bpy
bpy.data.scenes['Scene'].cursor_location[0] = -100

try:
    msh = bpn.msh('Plane')
except:
    bpn.addPrimitive(pType='plane', location=(0.0, 0.0, 0.0))
    msh = bpn.msh('Plane')

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
