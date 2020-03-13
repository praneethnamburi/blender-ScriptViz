import os
import sys

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../..'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

import bpn # pylint: disable=unused-import

bpy = bpn.bpy
bpy.data.scenes['Scene'].cursor.location[0] = -100

# bpn.env.reset()

bpy.ops.mesh.primitive_cube_add(location=(1.0, 0.0, 0.0))

m = bpn.Msh(name='Cube')
m.v = m.v*2
