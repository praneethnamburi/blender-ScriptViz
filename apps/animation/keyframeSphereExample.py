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
# bpn.new.sphere(obj_name='sphere', msh_name='sph', coll_name='myColl')
# bpn.animate_simple(xl_name)

xl_name = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'armReach_ineffTrial.xlsx'))
anim_data = pd.read_excel(xl_name, sheet_name='animation')

objNames = ['PN_Phone', 'RH_AcromioClavicular', 'RH_ElbowLat', 'RH_ElbowMed', 'RH_RadiusWrist', 'RH_UlnaWrist']
for obj_name in objNames:
    bpn.new.sphere(obj_name=obj_name, msh_name='sph', coll_name='Points', r=0.1)
bpn.animate_simple(anim_data)

traj_coll_name = 'Trajectories'
bpn.new.collection(traj_coll_name)
for obj_name in objNames:
    p = [eval(k) for k in anim_data.loc[anim_data['object'] == obj_name]['value']]
    x = [k[0] for k in p]
    y = [k[1] for k in p]
    z = [k[2] for k in p]
    bpn.plot(x, y, z, msh_name=obj_name+'_trajectory', coll_name=traj_coll_name)
