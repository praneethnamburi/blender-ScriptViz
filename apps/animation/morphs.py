"""
Morphs
"""

import os
import sys

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../..'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

from importlib import reload
import numpy as np
# import copy
# import pandas as pd
# from functools import partial

import bpn # pylint: disable=unused-import
import bmesh # pylint: disable=import-error

bpy = bpn.bpy
env = bpn.env

def tongue():
    """
    Morph should look like a tongue in one direction, and an alien helmet in another.

    During this, I learned that vertices should always be selected in an interval (it can be with a small epsilon), but exact values don't seem to work.
    """
    sph = bpn.new.sphere(name='tongue')
    sph.slice_x().slice_y().slice_z()

    eps = 0.002
    v = sph.v
    sel = np.logical_and.reduce((v[:, 0] > -eps, v[:, 0] < eps, v[:, 1] > -eps, v[:, 1] < eps)) #pylint: disable=no-member
    v[sel, 0:2] = v[sel, 0:2] - 0.2
    sph.v = v
    sph.morph(n_frames=25, frame_start=100)
    env.Key().goto(125)
    sph.bo.modifiers.new('subd', type='SUBSURF')
    sph.bo.modifiers['subd'].levels = 2
    sph.bo.modifiers['subd'].render_levels = 2

    for p in sph.bm.polygons:
        p.use_smooth = True

env.reset()
tongue()
