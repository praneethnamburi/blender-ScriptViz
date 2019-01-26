## import commonly used modules
import sys
import os
from importlib import reload
import numpy as np
import bpy #pylint: disable=import-error

## import custom modules
sys.path.append('/home/praneeth/Workspace/blenderPython')
import bpnModule as bpn

## do stuff on startup
# bpn.demo_animateDNA()