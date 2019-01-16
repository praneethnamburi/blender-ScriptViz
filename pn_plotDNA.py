import bpy #pylint: disable=import-error
import numpy as np
from math import sin

bpy.ops.wm.read_homefile() # reset the scene

x = np.linspace(0, 2.0*np.pi, 100)
y = lambda x, offset: np.sin(x+offset)
h1, m1 = plot(x, y(x, np.pi/2))
h2, m2 = plot(x, y(x, -np.pi/2))


def plot(x, y):
    mshName = 'autoMshName'
    objName = 'autoObjName'
    msh = genMesh(mshName, x, y)
    obj = genObj(objName, msh)
    bpy.context.scene.collection.objects.link(obj)
    return obj, msh

def genObj(objName, msh): # generates a plot object
    obj = bpy.data.objects.new(objName, msh)
    return obj

def genMesh(mshName, xVals, yVals): # generate mesh for plotting
    n = np.size(xVals)
    msh = bpy.data.meshes.new(mshName)
    msh.vertices.add(n)
    msh.edges.add(n-1)
    for i in range(n):
        msh.vertices[i].co = (xVals[i], yVals[i], 0)
        if i < n-1:
            msh.edges[i].vertices = (i, i+1)
    return msh
