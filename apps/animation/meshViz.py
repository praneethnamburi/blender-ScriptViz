import os
import sys
from importlib import reload
import numpy as np # pylint: disable=unused-import
import pandas as pd 
import types

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../..'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

import bpn # pylint: disable=unused-import

bpn = reload(bpn)

bpy = bpn.bpy


# # Turn a matrix into a callable function
# def callable_matrix(z):
#     return lambda ix, iy: z[ix][iy]
# zFunc = callable_matrix(z)

def fun2mat(xyfun, x=[], y=[]):
    """
    This functionality is already in the bpn module.
    It is here only to illustrate the versatility of bpn.Msh creation
    """
    assert isinstance(xyfun, types.FunctionType)
    assert xyfun.__code__.co_argcount == 2 # function has two input arguments
    if x is mat2mesh.__defaults__[0]: # default ranges
        x = np.arange(-2, 2, 0.1)
    if y is mat2mesh.__defaults__[1]:
        y = np.arange(-2, 2, 0.1)
    return np.array([[xyfun(xv, yv) for yv in y] for xv in x])

def mat2mesh(z, x=[], y=[]):
    """
    z is a 2-D numpy array or a 2D list
    returns:
        v list of vertices
        f list of faces
    This is here only for demonstration. It is already in bpn module.
    """
    if x is mat2mesh.__defaults__[0]:
        x = np.arange(0, np.shape(z)[0])
    if y is mat2mesh.__defaults__[1]:
        y = np.arange(0, np.shape(z)[1])

    nX = len(x)
    nY = len(y)

    assert len(x) == np.shape(z)[0]
    assert len(y) == np.shape(z)[1]
    
    v = [(xv, yv, z[ix][iy]) for iy, yv in enumerate(y) for ix, xv in enumerate(x)]
    f = [(iy*nX+ix, iy*nX+ix+1, (iy+1)*nX+(ix+1), (iy+1)*nX+ix) for iy in np.arange(0, nY-1) for ix in np.arange(0, nX-1)]
    return v, f

fun = lambda x, y: x*x+y*y
x1 = np.arange(-2, 2, 0.02)
y1 = np.arange(-2, 3, 0.2)
z1 = fun2mat(fun, x1, y1)
v1, f1 = mat2mesh(z1, x=x1, y=y1)

# # demonstrate different ways of using bpn msh
# m = bpn.Msh(v=v1, f=f1, obj_name='parabola1', coll_name='Collection')
# m = bpn.Msh(v=v1, f=f1)
# m = bpn.Msh(xyfun=fun)
# m = bpn.Msh(z=z1) # not the parabola you're expecting
# m = bpn.Msh(z=z1, x=x1, y=y1) # better

# def xyifun(alpha):
#     return lambda x, y: np.sqrt(alpha-np.abs(x))

# for i in np.arange(1, 7):
#     bpn.Msh(xyfun=xyifun(i), x=np.linspace(0, i, 60), y=[1, 2], name='sqrt_1', coll_name='roof')
#     bpn.Msh(xyfun=xyifun(i), x=np.linspace(-i, 0, 60), y=[1, 2], name='sqrt_2', coll_name='roof')

a = np.linspace(0, 2.0*np.pi, 100)
f = lambda a, offset: np.sin(a+offset)
x = f(a, np.pi/2)
y = f(a, 0)
z = a

n = np.size(x)
v2 = [(xv, yv, zv) for xv, yv, zv in zip(x, y, z)]
e2 = [(i, i+1) for i in np.arange(0, n-1)]

# bpn.plotDNA()
m = bpn.Msh(v=v2, e=e2, name='strand1')
m = bpn.Msh(x=-x, y=-y, z=z, name='strand2')
