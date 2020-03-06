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

def mat2mesh(z, x=[], y=[]):
    """
    z is a 2-D numpy array, 2D list or an anonymous function of 2 input numbers and one output number
    """
    if isinstance(z, types.FunctionType):
        if not x: # default ranges
            x = np.arange(-2, 2, 0.1)
        if not y:
            y = np.arange(-2, 2, 0.1)
        z = np.array([[z(xv, yv) for yv in y] for xv in x])
    else: # expecting a numpy array or a 2d list
        if not x:
            x = np.arange(0, np.shape(z)[0])
        if not y:
            y = np.arange(0, np.shape(z)[1])

    nX = len(x)
    nY = len(y)

    assert len(x) == np.shape(z)[0]
    assert len(y) == np.shape(z)[1]
    
    v = [(xv, yv, z[ix][iy]) for iy, yv in enumerate(y) for ix, xv in enumerate(x)]
    f = [(iy*nX+ix, iy*nX+ix+1, (iy+1)*nX+(ix+1), (iy+1)*nX+ix) for iy in np.arange(0, nY-1) for ix in np.arange(0, nX-1)]
    return v, f

xyfun = lambda x, y: np.sin(2*np.pi*2*x)
v1, f1 = mat2mesh(xyfun, list(np.arange(-2, 2, 0.02)), list(np.arange(-2, 2)))

#create mesh and object
mesh = bpy.data.meshes.new("wave")
obj = bpy.data.objects.new("wave", mesh)
bpy.data.collections['Collection'].objects.link(obj)
 
#create mesh from python data
mesh.from_pydata(v1, [], f1)
mesh.update(calc_edges=True)
