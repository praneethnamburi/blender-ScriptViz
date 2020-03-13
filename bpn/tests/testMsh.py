"""
Demonstrates various uses of the bpn.Msh module
"""
import os
import sys
from importlib import reload
import types
import numpy as np # pylint: disable=unused-import

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../..'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

import bpn # pylint: disable=unused-import
import mathutils # pylint: disable=import-error

bpn = reload(bpn)

bpy = bpn.bpy


# # Turn a matrix into a callable function
# def callable_matrix(z):
#     return lambda ix, iy: z[ix][iy]
# zFunc = callable_matrix(z)

def fun2mat(xyfun, tx=np.array([]), ty=np.array([])):
    """
    This functionality is already in the bpn module.
    It is here only to illustrate the versatility of bpn.Msh creation
    """
    assert isinstance(xyfun, types.FunctionType)
    assert xyfun.__code__.co_argcount == 2 # function has two input arguments
    if tx is mat2mesh.__defaults__[0]: # default ranges
        tx = np.arange(-2, 2, 0.1)
    if ty is mat2mesh.__defaults__[1]:
        ty = np.arange(-2, 2, 0.1)
    return np.array([[xyfun(xv, yv) for yv in ty] for xv in tx])

def mat2mesh(tz, tx=np.array([]), ty=np.array([])):
    """
    z is a 2-D numpy array or a 2D list
    returns:
        v list of vertices
        f list of faces
    This is here only for demonstration. It is already in bpn module.
    """
    if tx is mat2mesh.__defaults__[0]:
        tx = np.arange(0, np.shape(tz)[0])
    if ty is mat2mesh.__defaults__[1]:
        ty = np.arange(0, np.shape(tz)[1])

    nX = len(tx)
    nY = len(ty)

    assert len(tx) == np.shape(tz)[0]
    assert len(ty) == np.shape(tz)[1]
    
    v = [(xv, yv, tz[ix][iy]) for iy, yv in enumerate(ty) for ix, xv in enumerate(tx)]
    f = [(iy*nX+ix, iy*nX+ix+1, (iy+1)*nX+(ix+1), (iy+1)*nX+ix) for iy in np.arange(0, nY-1) for ix in np.arange(0, nX-1)]
    return v, f

fun = lambda x, y: x*x+y*y
x1 = np.arange(-2, 2, 0.02)
y1 = np.arange(-2, 3, 0.2)
z1 = fun2mat(fun, x1, y1)
v1, f1 = mat2mesh(z1, tx=x1, ty=y1)

# # demonstrate different ways of using bpn msh
p = bpn.Msh(v=v1, f=f1, name='parabola1', msh_name='parabola', coll_name='surface')
p.loc = p.loc + mathutils.Vector((-4.0, -3.0, 0.0))
# m = bpn.Msh(v=v1, f=f1)
p2 = bpn.Msh(xyfun=fun, name='parabola2', coll_name='surface')
p2.loc = p2.loc + mathutils.Vector((4.0, -3.0, 0.0))
# m = bpn.Msh(z=z1) # not the parabola you're expecting
# m = bpn.Msh(z=z1, x=x1, y=y1) # better

def xyifun(alpha):
    return lambda x, y: np.sqrt(alpha-np.abs(x))

for i in np.arange(1, 7):
    rf = bpn.Msh(xyfun=xyifun(i), x=np.linspace(0, i, 60), y=[1, 2], msh_name='sqrt_1'+str(i), obj_name='sqrt_1'+str(i), coll_name='roof')
    rf.loc = rf.loc + mathutils.Vector((0.0, 3.0, 0.0))
    rf = bpn.Msh(xyfun=xyifun(i), x=np.linspace(-i, 0, 60), y=[1, 2], msh_name='sqrt_2'+str(i), obj_name='sqrt_2'+str(i), coll_name='roof')
    rf.loc = rf.loc + mathutils.Vector((0.0, 3.0, 0.0))

## 3D plots
# DNA
a = np.linspace(-2.0*np.pi, 2.0*np.pi, 100)
f1 = lambda a, offset: np.sin(a+offset)
x = f1(a, np.pi/2)
y = f1(a, 0)
z = a

n = np.size(x)
v2 = [(xv, yv, zv) for xv, yv, zv in zip(x, y, z)]
e2 = [(i, i+1) for i in np.arange(0, n-1)]

m = bpn.Msh(v=v2, e=e2, name='strand1', coll_name='plots')
m = bpn.Msh(x=-x, y=-y, z=z, name='strand2', coll_name='plots')

# heart
a = np.linspace(-1.0*np.pi, 1.0*np.pi, 100)
m = bpn.Msh(x=np.sqrt(np.abs(a))*np.sin(a), y=np.abs(a)*np.cos(a), z=np.zeros_like(a), name='heart', coll_name='plots')

## primitives
s1 = bpn.new.sphere(name='sphere01', msh_name='sphere', coll_name='primitives')
s1.loc = (0.0, 1.0, 0.0)
s2 = bpn.new.sphere(name='sphere02', msh_name='sphere', coll_name='primitives')
s2.loc = (2.0, 2.0, 0.0)

# implement turtle functions using grease pencil module
# see if you can 'attach' segments at specific points, faces
