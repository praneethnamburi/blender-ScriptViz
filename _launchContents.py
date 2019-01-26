## import commonly used modules
import sys
import os
from importlib import reload
import numpy as np
import math
import inspect

import bpy #pylint: disable=import-error
import mathutils #pylint: disable=import-error

## import custom modules
sys.path.append('/home/praneeth/Workspace/blenderPython')
import bpn
import pnTools as my
import marmosetAtlas as atl

def reloadAll():
    exec('bpn = reload(bpn); my = reload(my)')

def clearWorkSpace():
    for k in list(my.getmembers(math).keys()): 
        del(globals()[k])
    for k in list(my.getmembers(mathutils).keys()): 
        del(globals()[k])
    del(globals()['C'])
    del(globals()['D'])

del(bpy.loadStr)

# delete convenience variables that are polluting the namespace!

## do stuff on startup
# bpn.demo_animateDNA()