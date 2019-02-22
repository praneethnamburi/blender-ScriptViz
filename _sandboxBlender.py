"""
This is a sandbox. Develop code here!
"""
#-----------------
import os
import sys
import numpy as np

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '.'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

import bpn # pylint: disable=unused-import

bpy = bpn.bpy
bpy.data.scenes['Scene'].cursor_location[0] = -100

# bpn.reset_blender()
#-----------------
