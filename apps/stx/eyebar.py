"""
Eye bar modifications for the marmoset stereotax.

Loads the STL file into blender and moves the vertices around.

Usage:
    blender --background --python apps/stx/eyebar.py
"""

import os
import sys

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../..'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

import bpn # pylint: disable=unused-import

bpy = bpn.bpy
bpy.data.scenes['Scene'].cursor_location[0] = -100

bpn.reset_blender()

import numpy as np

LOAD_PATH = os.path.realpath(r"D:\GDrive Columbia\issalab_data\Marmoset stereotax\Gilbert Menon 2019\EyeBar.STL")
SAVE_PATH = os.path.realpath(r"D:\GDrive Columbia\issalab_data\Marmoset stereotax\pn\EyeBarGM2019.STL")

from importlib import reload
bpn = reload(bpn)

# load the original eyebar mesh from Gilbert Menon 2019
m = bpn.Msh(bpn.loadSTL(LOAD_PATH)['meshes'][0])
coords = m.v

width_frac = 0.70 # (min, max) -> (2/3, 1)
height_frac = 0.65 # modulate the height of the eyebar by this fraction
inc_length = 12 # mm increase the length (keep the hole out of this)
inc_hole = 5 # mm increase the hole by this amount

x = 0 # length
y = 1 # height
z = 2 # width

# center along width, then squish
width_center = np.mean([np.min(coords[:, z]), np.max(coords[:, z])])
coords[:, z] = coords[:, z] - width_center
selGrooveNeg = coords[:, x] < 33 # excluding the eye groove
coords[selGrooveNeg, z] = coords[selGrooveNeg, z]*width_frac

# squish the height
sel = coords[:, y] > 3
coords[sel, y] = coords[sel, y]*height_frac

# inccrease the length (without the hole)
selX = coords[:, x] > 20
coords[selX, x] = coords[selX, x] + inc_length

# increase the hole length
selX = np.logical_and(coords[:, x] > 10, coords[:, x] < 20)
coords[selX, x] = coords[selX, x] + inc_hole

m.v = coords

m.export(SAVE_PATH)
