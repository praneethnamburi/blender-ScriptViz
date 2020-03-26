"""
Praneeth's blender python module
"""
# Imports from the standard library
import os

# Installed using _requirements
import numpy as np
import pandas as pd

# Blender's library
import bpy #pylint: disable=import-error
import bmesh #pylint: disable=import-error
import mathutils #pylint: disable=import-error

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

# Convenience
Matrix = mathutils.Matrix
Vector = mathutils.Vector
