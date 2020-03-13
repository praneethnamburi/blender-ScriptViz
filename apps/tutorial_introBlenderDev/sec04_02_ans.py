import os
import sys

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../..'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

import bpn # pylint: disable=unused-import
from bpn import Props

bpy = bpn.bpy
bpy.data.scenes['Scene'].cursor.location[0] = -100

bpn.reset_blender()

# Instantiating a class using parenthesis
print(Props())

# Calling an object. Intro do Python magic methods.
print(Props()())

# More magic methods. 
a = Props()
bpy.ops.mesh.primitive_cube_add(location=(1.0, 1.0, 1.0))
b = Props()
print((b-a)())

# a | b - union
# a & b - intersection
# a - b
# a ^ b
