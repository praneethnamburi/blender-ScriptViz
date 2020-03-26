"""
Praneeth's blender python module
"""
# Imports from the standard library
import errno
import functools
import inspect
import math
import os
import sys
import types

# Installed using _requirements
import numpy as np
import pandas as pd

# Blender's library
import bpy #pylint: disable=import-error
import bmesh #pylint: disable=import-error
import mathutils #pylint: disable=import-error
from io_mesh_stl.stl_utils import write_stl #pylint: disable=import-error

# Peronal library
import pntools as pn

# This package
if __package__ is not None:
    # modules
    from . import new, env, demo, utils, turtle, vef, trf, io, core
    # classes
    from .core import Msh
    from .env import Props, ReportDelta
    from .turtle import Draw
    from .trf import CoordFrame as Frm
    from .trf import PointCloud as PC
    # functions
    from .io import readattr, animate_simple
    from .utils import get
    # variables
    from .core import PATH, DEV_ROOT

# For customizing workspace variables in blender's python console.
loadStr = ''.join([line for line in open(os.path.join(str(DEV_ROOT), 'bpn\\_blenderwksp.py')) if not '__bpnRemovesThisLine__' in line]).replace('__bpnModifyFilePath__', str(DEV_ROOT).replace('\\', '\\\\'))
