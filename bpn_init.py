"""
Initialization code for apps using Praneeth's blender python module.
Also useful for initalizing blender's workspace.

Usage:
    from bpn_init import *
    pn.reload() # useful when developing the module alongside the app
    env.reset() # if you want to delete objects, this is useful!
"""
#pylint:disable=unused-import
# Imports from the standard library
import os
import sys
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
import bpn
# modules
from bpn import new, env, demo, utils, turtle, vef, trf, io, mantle, core
# classes
from bpn.mantle import Pencil, Screen
# functions
from bpn.utils import get

# Convenience
Matrix = mathutils.Matrix
Vector = mathutils.Vector

# bridge to julia
# pylint: disable=no-name-in-module
from julia import Pkg
Pkg.activate(r"D:\Workspace\julia\pntools")
from julia import pntools as pnj
Pkg.activate() # switch back to the default environment in julia
