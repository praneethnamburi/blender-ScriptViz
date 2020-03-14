"""
Demonstrations using the bpn module

Functions:
    animate_spheres - keyframe animation
    animate_dna - animated plots
"""
import os
import sys
import numpy as np

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

import bpn
import bpy #pylint: disable=import-error

from . import new

def animate_spheres():
    """
    Demonstration for animating a sphere using blender's functions.
    """
    # Animation with blender's keyframe_insert
    s1 = new.sphere(obj_name='sphere1', msh_name='sph', coll_name='Spheres')
    frameID = [1, 50, 100]
    loc = [(1, 1, 1), (1, 2, 1), (2, 2, 1)]
    attrs = ['location', 'rotation_euler', 'scale']
    for thisFrame, thisLoc in zip(frameID, loc):
        bpy.context.scene.frame_set(thisFrame)
        for attr in attrs:
            setattr(s1.bo, attr, thisLoc)
            s1.bo.keyframe_insert(data_path=attr, frame=thisFrame)

    # Animation with bpn.Msh's 'key' function.
    s2 = bpn.new.sphere(name='sphere2', msh_name='sph', coll_name='Spheres')
    s2.key(1)
    s2.loc = (2, 2, 2)
    s2.key(26)
    s2.scl = (1, 0.2, 1)
    s2.key(51)
    s2.scl = (1, 2, 0.2)
    s2.key(76)

    # chaining absolute values (same as above)
    s3 = bpn.new.sphere(name='sphere3', msh_name='sph', coll_name='Spheres')
    s3.key(1, 's').key(26, 's', [(0.5, 0.5, 1)]).key(51, 's', [(1, 3, 0.3)])

    # chaining transforms (relative)
    s4 = bpn.new.sphere(name='sphere4', msh_name='sph', coll_name='Spheres')
    s4.key(1).translate((0, 0, 2)).key(26).scale((1, 1, 0.3)).key(51).scale((1, 1, 4)).key(101)

def animate_dna():
    """
    Animate two strands of DNA
    """
    a = np.linspace(-2.0*np.pi, 2.0*np.pi, 100)
    f1 = lambda a, offset: np.sin(a+offset)
    x = f1(a, np.pi/2)
    y = f1(a, 0)
    z = a

    n = np.size(x)
    v2 = [(xv, yv, zv) for xv, yv, zv in zip(x, y, z)]
    e2 = [(i, i+1) for i in np.arange(0, n-1)]

    s1 = bpn.Msh(v=v2, e=e2, name='strand1', coll_name='plots')
    s2 = bpn.Msh(x=-x, y=-y, z=z, name='strand2', coll_name='plots')
    
    frames = (1, 50, 100, 150, 200)
    bpy.context.scene.frame_start = frames[0]
    bpy.context.scene.frame_end = frames[-1]

    for s in (s1, s2):
        s.key(frames[0], 'r')
        for i in np.arange(1, np.size(frames)):
            s.rotate((0, 0, 90))
            s.key(frames[i], 'r')
