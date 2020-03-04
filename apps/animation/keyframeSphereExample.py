"""
Keyframe animation by reading data from an excel file.
"""

import os
import sys

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../..'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

import pandas as pd
import bpn # pylint: disable=unused-import

from importlib import reload

bpn = reload(bpn)
bpy = bpn.bpy

# xl_name = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'keyframeSphereExample.xlsx'))

# bpn.new.sphere(objName='sphere', mshName='sph', collName='myColl')
# bpn.animate_simple(xl_name)

# frameID = [1, 50, 100]
# loc = [(1, 1, 1), (1, 2, 1), (2, 2, 1)]
# attr = 'location'
# for thisFrame, thisLoc in zip(frameID, loc):
#     bpy.context.scene.frame_set(thisFrame)
#     setattr(obj, attr, thisLoc)
#     obj.keyframe_insert(data_path=attr, frame=thisFrame)

xl_name = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'armReach_ineffTrial.xlsx'))
anim_data = pd.read_excel(xl_name, sheet_name='animation')

objNames = ['PN_Phone', 'RH_AcromioClavicular', 'RH_ElbowLat', 'RH_ElbowMed', 'RH_RadiusWrist', 'RH_UlnaWrist']
for objName in objNames:
    bpn.new.sphere(objName=objName, mshName='sph', collName='Points', r=0.1)
bpn.animate_simple(anim_data)

traj_coll_name = 'Trajectories'
bpn.new.collection(traj_coll_name)
for objName in objNames:
    p = [eval(k) for k in anim_data.loc[anim_data['object'] == objName]['value']]
    x = [k[0] for k in p]
    y = [k[1] for k in p]
    z = [k[2] for k in p]
    bpn.plot(x, y, z, mshName=objName+'_trajectory', collName=traj_coll_name)
