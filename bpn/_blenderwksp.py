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
1. Launch blender using blender.start command from the VSCode blender add-on.
2. Type the following commands into the blender console.
>>> from bpn.utils import LOAD
>>> exec(LOAD)

Testing:
To check if the script worked as intended, inspect variables in
blender's python console by comparing the output of dir() before and
after executing the exec(LOAD) command

! Caution:
Don't call this function from the command line. This was causing some
unpredictable behavior and the code is meant to terminate if it is not
called properly (i.e. through the bpn module)

Tip:
Given that the bpn module parses this script, add this comment to any
line that should be removed #__bpnRemovesThisLine__
"""

import sys
print("Don't run _blenderwksp.py directly. Exiting.") #__bpnRemovesThisLine__
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
import pntools as pn

def reload_all(constraint='Workspace'):
    """
    Reloads all modules with constraint in str(module).
    If all your modules to be reloaded are in drive D:, then use constraint = 'D:'
    Returns names of all the modules that were identified for reload
    """
    all_mod = [obj for obj in globals() if inspect.ismodule(eval(obj)) and constraint in str(eval(obj))] # pylint: disable=W0122
    for modname in all_mod:
        reload(eval(modname))
    return all_mod

# delete convenience variables that are polluting the namespace!
def clear_workSpace():
    """Removes blender's convenience variables and import * imports"""
    for k in list(pn.get_mod_members(math).keys()):
        del globals()[k]
    for k in list(pn.get_mod_members(mathutils).keys()):
        del globals()[k]
    del globals()['C']
    del globals()['D']

clear_workSpace()
del clear_workSpace
del LOAD #pylint:disable=undefined-variable

from bpn import *

# Don't add anything here to test. Add only things you want done every
# time you load blender
