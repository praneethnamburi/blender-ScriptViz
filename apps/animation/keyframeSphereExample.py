"""
Keyframe animation by reading data from an excel file.
"""

import os
import sys

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../..'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

import numpy as np
import pandas as pd
from functools import partial
import bpn # pylint: disable=unused-import

from importlib import reload

bpn = reload(bpn)
bpn.new = reload(bpn.new)
bpy = bpn.bpy

# xl_name = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'keyframeSphereExample.xlsx'))
# bpn.new.sphere(obj_name='sphere', msh_name='sph', coll_name='myColl')
# bpn.animate_simple(xl_name)

# xl_name = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'armReach_ineffTrial.xlsx'))
# anim_data = pd.read_excel(xl_name, sheet_name='animation')

# # keyframe animation
# bpn.animate_simple(anim_data, propfunc=partial(bpn.new.sphere, **{'r':0.1, 'coll_name':'myColl', 'msh_name':'sph'}))

# # plot trajectories
# obj_names = anim_data['object'].unique()
# traj_coll_name = 'Trajectories'
# bpn.new.collection(traj_coll_name)
# for obj_name in obj_names:
#     p = np.array([eval(k) for k in anim_data.loc[anim_data['object'] == obj_name]['value']])
#     bpn.Msh(x=p[:, 0], y=p[:, 1], z=p[:, 2], name=obj_name+'_trajectory', coll_name=traj_coll_name)

bpn.new.sphere(obj_name='sph30', msh_name='sp30', coll_name='myc', r=3, u=3, v=2)
