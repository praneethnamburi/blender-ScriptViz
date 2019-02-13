"""
Customize workspace variables in blender's python console.

Purpose:
Blender's python console has a polluted workspace, and oftentimes, we
need some standard imports available soon as blender starts. The purpose
of this script is to hold those commands. Note that loading this script
in Blender's text editor and executing it does not inject all these
variables into blender's console. Supplying this script as a command
line input will not work either, because the variables will only exist
in this module's scope. Only variables injected into bpy object are
retained in Blender's workspace.

Strategy:
Read this file as a string and inject it into blender's bpy data object.
The bpn module already does this, and therefore, supply any script that
imports the bpn module as a command line argument when launching blender
from a terminal. Then, execute that string within blender's python
console.

Usage:
1. Launch blender from the terminal using:
>>> blender --python marmosetAtlas.py
2. Execute the following command in blender's python console:
>>> exec(bpy.loadStr)

Testing:
To check if the script worked as intended, inspect variables in
blender's python console by comparing the output of dir() before and
after executing the exec(bpy.loadStr) command

! Caution:
Don't call this function from the command line. This was causing some
unpredictable behavior and the code is meant to terminate if it is not
called properly (i.e. through the bpn module)

Tip:
Given that the bpn module parses this script, add this comment to any
line that should be removed #__bpnRemovesThisLine__
"""

import sys
print("Don't run _blenderWksp.py directly. Exiting.") #__bpnRemovesThisLine__
sys.exit() #__bpnRemovesThisLine__
import os
import math
import inspect # pylint: disable=W0611
from importlib import reload # pylint: disable=W0611
import numpy as np # pylint: disable=W0611

import mathutils #pylint: disable=import-error

## import custom modules
# Note that in this file, the paths unfortunately have to be hard coded
if os.path.dirname('__bpnModifyFilePath__') not in sys.path:
    sys.path.append('__bpnModifyFilePath__')

import bpn
import pntools as my
import marmosetAtlas as atl # pylint: disable=W0611

def reloadAll():
    """Reloads bpn and my (pntools)"""
    exec('bpn = reload(bpn); my = reload(my)') # pylint: disable=W0122

# delete convenience variables that are polluting the namespace!
def clearWorkSpace():
    """Removes blender's convenience variables and import * imports"""
    for k in list(my.getmembers(math).keys()):
        del globals()[k]
    for k in list(my.getmembers(mathutils).keys()):
        del globals()[k]
    del globals()['C']
    del globals()['D']

clearWorkSpace()
del clearWorkSpace
del bpn.bpy.loadStr

# Don't add anything here to test. Add only things you want done every
# time you load blender
