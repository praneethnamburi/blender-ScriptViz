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
from importlib import reload
from timeit import default_timer as timer

# Installed using _requirements
import numpy as np
import pandas as pd

# Blender's library
import bpy #pylint: disable=import-error
import bmesh #pylint: disable=import-error
import mathutils #pylint: disable=import-error

# Peronal library
import pntools as pn
from pntools import sampled
import bpn
# modules
from bpn import new, env, demo, utils, turtle, vef, trf, io, mantle, core
# classes
from bpn.mantle import Pencil, Screen
# functions
from bpn.utils import get
from pntools import run

# # Convenience
# Matrix = mathutils.Matrix
# Vector = mathutils.Vector

# for using matplotlib from within blender
import multiprocess
multiprocess.set_executable(pn.locate_command('python', 'conda', verbose=False).split('\r\n')[0])
from plots import plot

def reset():
    env.reset()
    core.ThingDB = core._ThingDB()

# bridge to julia
# pylint: disable=no-name-in-module, wrong-import-order
# from julia import Pkg
# Pkg.activate(os.path.join(os.path.dirname(__file__), "SimPN"))
# from julia import SimPN as spn
# Pkg.activate() # switch back to the default environment in julia
# pylint: enable=no-name-in-module, wrong-import-order

# # bridge to MATLAB
# try:
#     import matlab.engine
#     ml_eng_installed = True
# except ImportError:
#     print("Unable to detect MATLAB engine.")
#     ml_eng_installed = False

# if ml_eng_installed:
#     all_ml = matlab.engine.find_matlab()
#     if len(all_ml) == 0:
#         print("No shared MATLAB engine sessions found. Type matlab.engine.shareEngine at the MATLAB command prompt")
#     elif len(all_ml) == 1:
#         future = matlab.engine.connect_matlab(all_ml[0], background=True)
#         eng = future.result()
#         mw = eng.workspace
#     elif len(all_ml) > 1:
#         print("Multiple MATLAB sessions found. Please connect manually.")
