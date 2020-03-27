"""
Praneeth's blender python module
"""
# Imports from the standard library
import os
import inspect
import importlib

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

def _reload():
    """
    Reloads all sub-modules of this module.
    Returns names of all the modules that were identified for reload.
    usage: bpn._reload()
    """
    #pylint: disable=eval-used
    all_mod = [obj for obj in globals() if inspect.ismodule(eval(obj)) and __package__ in str(eval(obj))] # pylint: disable=W0122
    for modname in all_mod:
        importlib.reload(eval(modname))
    return all_mod
