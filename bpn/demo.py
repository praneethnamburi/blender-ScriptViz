"""
Demonstrations using the bpn module

Functions:
    spheres - keyframe animation
    dna     - animated plots
    heart   - plot a heart
    arch    - surface plots with 2d functions
    zoo     - creates a zoo of primitive objects
    spiral  - animates an object along a spiral path
"""
import os
import sys
import numpy as np

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

import pntools as pn

import bpn
import bpy #pylint: disable=import-error
import bmesh  #pylint: disable=import-error
import mathutils #pylint: disable=import-error

def spheres():
    """
    Demonstration for animating a sphere using blender's functions.
    """
    # Animation with blender's keyframe_insert
    s1 = bpn.new.sphere(obj_name='sphere1', msh_name='sph', coll_name='Spheres')
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
    
    bpn.env.Key().auto_lim()

def dna():
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

    s1 = bpn.Msh(v=v2, e=e2, name='strand1', coll_name='Plots')
    s2 = bpn.Msh(x=-x, y=-y, z=z, name='strand2', coll_name='Plots')
    
    frames = (1, 50, 100, 150, 200)

    for s in (s1, s2):
        s.key(frames[0], 'r')
        for i in np.arange(1, np.size(frames)):
            s.rotate((0, 0, 90))
            s.key(frames[i], 'r')

    bpn.env.Key().auto_lim()

def heart():
    """Plot a heart"""
    a = np.linspace(-1.0*np.pi, 1.0*np.pi, 100)
    bpn.Msh(x=np.sqrt(np.abs(a))*np.sin(a), y=np.abs(a)*np.cos(a), z=np.zeros_like(a), name='heart', coll_name='Plots')

def arch():
    """2D surface plots"""
    def xyifun(alpha):
        return lambda x, y: np.sqrt(alpha-np.abs(x))

    for i in np.arange(1, 7):
        rf = bpn.Msh(xyfun=xyifun(i), x=np.linspace(0, i, 60), y=[1, 2], msh_name='sqrt_1'+str(i), obj_name='sqrt_1'+str(i), coll_name='Arch')
        rf.loc = rf.loc + mathutils.Vector((0.0, 3.0, 0.0))
        rf = bpn.Msh(xyfun=xyifun(i), x=np.linspace(-i, 0, 60), y=[1, 2], msh_name='sqrt_2'+str(i), obj_name='sqrt_2'+str(i), coll_name='Arch')
        rf.loc = rf.loc + mathutils.Vector((0.0, 3.0, 0.0))

def zoo():
    """
    Create a zoo of primitives. 
    """
    bpn.Msh.track_start()
    bpn.new.sphere(obj_name='sph30', msh_name='sp30', r=0.7, u=3, v=2, coll_name='zoo')
    bpn.new.monkey(name='L', msh_name='M', coll_name='zoo')
    bpn.new.sphere(name='Sph', r=2, u=6, v=8, coll_name='zoo')
    bpn.new.cube(name='de', msh_name='e', size=0.4, coll_name='zoo')
    bpn.new.cone(name='mycone', segments=4, diameter1=2, diameter2=2, depth=2*np.sqrt(2), cap_ends=True, cap_tris=False, coll_name='zoo')
    bpn.new.cone(name='mycone1', coll_name='zoo')
    bpn.new.cone(name='mycone2', seg=3, d=1, coll_name='zoo')
    bpn.new.cone(name='mycone3', seg=3, r1=3, r2=2, d=0, cap_ends=False, coll_name='zoo')

    bpn.new.polygon(name='hex', seg=6, coll_name='zoo')
    bpn.new.ngon(name='circle', n=32, r1=1, r2=0, coll_name='zoo')

    bpn.new.polygon(name='hex', seg=6, coll_name='zoo')

    for obj in bpn.Msh.all:
        obj.translate(np.random.randint(-6, 6, 3))
        obj.to_coll('zoo')

    bpn.Msh.track_end()

def spiral():
    """
    Animating along a path with a few lines of code.
    """
    sp = bpn.new.spiral(name='spiral')
    sp.rotate((0, 30, 0))

    s = bpn.new.sphere(name='sphere', r=0.3, u=4, v=2)
    s.key(1, 'l')
    for idx, loc in enumerate(list(sp.v_world)):
        s.key(idx+2, 'l', [tuple(loc)])

def plane_slice():
    """
    Using the plane slicer to 'sculpt' simple objects.
    """
    r = 1
    n = 4
    sph = bpn.new.sphere(name='sphere', r=r)

    subtended_angle = 2*np.pi/n
    trans = r*np.cos(subtended_angle/2)
    sph.translate(z=trans)

    for _ in range(n-1):
        sph.slice_z().rotate(np.degrees((subtended_angle, 0, 0)))

    len_z = np.max(sph.v[:, -1]) - np.min(sph.v[:, -1])
    sph.translate(z=-0.8*len_z)
    sph.slice_z(slice_dir='pos')
    len_z = np.max(sph.v[:, -1]) - np.min(sph.v[:, -1])
    sph.translate(z=len_z)
    sph.morph(frame_start=151)
    return sph

def draw_basic():
    """Draw a loopy thing."""
    a = bpn.Draw('link')
    bmesh.ops.create_circle(a.bm, radius=0.2, segments=6)
    for vert in a.bm.verts[:]:
        vert.co += mathutils.Vector((0., -1., 0))
    a.spin(angle=np.pi, steps=3, axis='x', cent=(0., 0., 0.))
    for i in range(5):
        a.spin(angle=np.pi, steps=3, axis=(1., 1.0-2.0*(i%2), 0), cent=(2*i+1.0, 0., 0))
    return +a

def main():
    """
    Runs all the demos. Avoid using this!
    """
    all_mem = pn.get_mod_members(sys.modules[__name__], False)
    all_func = [eval(name) for name, typ in all_mem.items() if typ == 'function' and name != 'main'] #pylint: disable=eval-used
    for func in all_func:
        func()
