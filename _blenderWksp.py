### This code helps manipulate the workspace in blender's terminal
# To use it, load this code as a string and store it in bpy (such as bpy.loadStr)
# Once you launch blender (from whichever code), execute the contents of bpy.loadStr using exec(bpy.loadStr) in blender's python console
# That will execute the contents of this file
# If you are using bpn, it will do this for you. Just launch blender from any script that imports bpn (such as marmosetAtlas.py) using the following command in the terminal:
# blender --python marmosetAtlas.py
# ! Don't call this function from the command line (don't do blender --python _blenderWksp.py)

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
# Note that in this file, the paths unfortunately have to be hard coded
if sys.platform == 'linux':
    sys.path.append('/home/praneeth/Workspace/blenderPython')
else:
    sys.path.append('C:\\Workspace\\blenderPython')
import bpn
import pnTools as my
import marmosetAtlas as atl

def reloadAll():
    exec('bpn = reload(bpn); my = reload(my)')

# delete convenience variables that are polluting the namespace!
def clearWorkSpace():
    for k in list(my.getmembers(math).keys()): 
        del(globals()[k])
    for k in list(my.getmembers(mathutils).keys()): 
        del(globals()[k])
    del(globals()['C'])
    del(globals()['D'])

clearWorkSpace()
del(clearWorkSpace)
del(bpy.loadStr)

## Don't add anything here to test. Add only things you want done every time you load blender