import bpy #pylint: disable=import-error
import numpy as np
from mathutils import Vector #pylint: disable=import-error

# bpy.ops.wm.read_homefile() # reset the scene

def pn_plotDNA(): # MATLAB style
    x = np.linspace(0, 2.0*np.pi, 100)
    y = lambda x, offset: np.sin(x+offset)
    h1, m1 = plot(y(x, np.pi/2), y(x, 0), x)
    h2, m2 = plot(y(x, -np.pi/2), -y(x, 0), x)
    return [h1, h2], [m1, m2] # objList, mshList

def pn_animateObj(objList, frameList):
    scn = bpy.context.scene # assuming there is only one scene
    scn.frame_end = frameList[-1] # assuming frameList is monotonically increasing
    for frameNum in frameList:
        scn.frame_set(frameNum)
        for obj in objList:
            obj.rotation_euler = Vector((0, 0, 2*np.pi*frameNum/frameList[-1]))
            obj.keyframe_insert(data_path="rotation_euler", index=-1)

def plot(x, y, z=0):
    mshName = 'autoMshName'
    objName = 'autoObjName'
    # create a mesh
    msh = genMesh(mshName, x, y, z)
    # instantiate an object
    obj = genObj(objName, msh)
    # put that object in the scene
    bpy.context.scene.collection.objects.link(obj)
    return obj, msh

def genObj(objName, msh): # generates a plot object
    obj = bpy.data.objects.new(objName, msh)
    return obj

def genMesh(mshName, xVals, yVals, zVals=None): # generate mesh for plotting
    n = np.size(xVals)
    if zVals is None:
        zVals = np.zeros(n)
    msh = bpy.data.meshes.new(mshName)
    msh.vertices.add(n)
    msh.edges.add(n-1)
    for i in range(n):
        msh.vertices[i].co = (xVals[i], yVals[i], zVals[i])
        if i < n-1:
            msh.edges[i].vertices = (i, i+1)
    return msh

# using this syntax, we don't have to worry about forward declaration
# remember that in python, you need to define functions before using them
if __name__ == '__main__':
    objList, mshList = pn_plotDNA()
    pn_animateObj(objList, np.arange(0, 101, 20))