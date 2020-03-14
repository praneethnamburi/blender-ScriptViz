"""
Demonstrations using the bpn module
"""
import bpy #pylint: disable=import-error
from . import new

def animate_sphere():
    """
    Demonstration for animating a sphere.
    """
    obj = new.sphere(obj_name='sphere', msh_name='sph', coll_name='Collection')
    frameID = [1, 50, 100]
    loc = [(1, 1, 1), (1, 2, 1), (2, 2, 1)]
    attrs = ['location', 'rotation_euler', 'scale']
    for thisFrame, thisLoc in zip(frameID, loc):
        bpy.context.scene.frame_set(thisFrame)
        for attr in attrs:
            setattr(obj.bo, attr, thisLoc)
            obj.bo.keyframe_insert(data_path=attr, frame=thisFrame)
