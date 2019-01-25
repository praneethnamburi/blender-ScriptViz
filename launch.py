### Use the command blender --python launch.py in the terminal to launch blender

# add custom module locations to system path
# note that the appended paths persist 
import sys 
sys.path.append('/home/praneeth/Workspace/blenderPython')


## import custom modules
import bpnModule as b

## store them in bpy
'''this is the only way by which I managed to send data from the command line to the python console inside blender'''
import bpy #pylint: disable=import-error
bpy.b = b

## do stuff on startup
# b.demo_animateDNA()