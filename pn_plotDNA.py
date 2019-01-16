import bpy #pylint: disable=import-error
import numpy as np

bpy.ops.wm.read_homefile() # reset the scene

def pn_plotDNA(): # MATLAB style
    x = np.linspace(0, 2.0*np.pi, 100)
    y = lambda x, offset: np.sin(x+offset)
    h1, m1 = plot(x, y(x, np.pi/2))
    h2, m2 = plot(x, y(x, -np.pi/2))
    return [h1, h2], [m1, m2]

def plot(x, y):
    mshName = 'autoMshName'
    objName = 'autoObjName'
    # create a mesh
    msh = genMesh(mshName, x, y)
    # instantiate an object
    obj = genObj(objName, msh)
    # put that object in the scene
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

# using this syntax, we don't have to worry about forward declaration
# remember that in python, you need to define functions before using them
if __name__ == '__main__':
    pn_plotDNA()

    