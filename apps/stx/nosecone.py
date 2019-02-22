"""Nose cone modifications for the marmoset stereotax."""

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

# load the original eyebar mesh from Gilbert Menon 2019
nosecone_path = os.path.realpath(r"D:\GDrive Columbia\issalab_data\Marmoset stereotax\Gilbert Menon 2019\NoseCone.STL")
m = bpn.msh(bpn.loadSTL(nosecone_path)['meshes'][0])

coords = m.v
# mods go in here
m.v = coords