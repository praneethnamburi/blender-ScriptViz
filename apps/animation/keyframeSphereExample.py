"""
Keyframe animation by reading data from an excel file.
"""

import os
import sys

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../..'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

import bpn # pylint: disable=unused-import

xl_name = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'keyframeSphereExample.xlsx'))

bpn.new.sphere(objName='sphere', mshName='sph', collName='myColl')
bpn.animate_simple(xl_name)

# frameID = [1, 50, 100]
# loc = [(1, 1, 1), (1, 2, 1), (2, 2, 1)]
# attr = 'location'
# for thisFrame, thisLoc in zip(frameID, loc):
#     bpy.context.scene.frame_set(thisFrame)
#     setattr(obj, attr, thisLoc)
#     obj.keyframe_insert(data_path=attr, frame=thisFrame)
