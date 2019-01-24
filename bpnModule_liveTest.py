import os
import errno
import numpy as np
from mathutils import Vector #pylint: disable=import-error
import sys
import glob
import bpy #pylint: disable=import-error

def raiseNotFoundError(thisDirFiles):
    if isinstance(thisDirFiles, str):
        thisDirFiles = [thisDirFiles]
    for dirFile in thisDirFiles:
        if not os.path.exists(dirFile):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), dirFile)

def checkIfOutputExists(func):
    def checkedFunction(*args, **kwargs):
        output = func(*args, **kwargs)
        raiseNotFoundError(output)
        return output
    return checkedFunction

@checkIfOutputExists
def getFileName_full(fPath, fName):
    fullName = os.path.join(os.path.normpath(fPath), fName)
    return fullName

@checkIfOutputExists
def marmosetAtlasPath(src='bma'):
    if src=='bma':
        if sys.platform == 'linux':
            fPath = "/media/praneeth/Reservoir/GDrive Columbia/issalab_data/Marmoset brain/Woodward segmentation/meshes/"
        else:
            fPath = "D:\\GDrive Columbia\\issalab_data\\Marmoset brain\\Woodward segmentation\\meshes"
    return fPath

# function syntax for making a decorator
def baseNames(func):
    def baseModFunc(*args, **kwargs):
        # input validation code goes here
        fOut = func(*args, **kwargs)
        # output validation and modification code goes here
        fOutBase = [os.path.basename(k) for k in fOut]
        return fOutBase
    return baseModFunc

@baseNames
@checkIfOutputExists
def getMeshNames(fPath=marmosetAtlasPath(), searchStr='*smooth*.stl'):
    mshNames = glob.glob(fPath + searchStr)
    return mshNames


# Make some demo functions here! 
# Animating DNA, 
def demo_animateDNA():
    objList, _ = plotDNA()
    animateObj_whole(objList, np.arange(0, 101, 20))
# meshDance
# brainExplosion

# Blender usefulness exercise #1 - Plotting
# Plotting two strands of DNA
def plotDNA():
    """
    Plot DNA. Demonstrates how to plot in Blender.
    Use: objList, mshList = bpn.pn_plotDNA()
    """
    x = np.linspace(0, 2.0*np.pi, 100)
    y = lambda x, offset: np.sin(x+offset)
    h1, m1 = plot(y(x, np.pi/2), y(x, 0), x)
    h2, m2 = plot(y(x, -np.pi/2), -y(x, 0), x)
    return [h1, h2], [m1, m2] # objList, mshList

def plot(x, y, z=0):
    mshName = 'autoMshName'
    # create a mesh
    msh = genMesh(mshName, x, y, z)
    # instantiate an object
    obj = genObj(msh)
    return obj, msh

def genMesh(mshName, xVals, yVals, zVals=None):
    """Generates a mesh for plotting."""
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

def genObj(msh, name='autoObjName', location=(0.0,0.0,0.0)):
    """Generates an object fraom a mesh and attaches it to the current scene."""
    obj = bpy.data.objects.new(name, msh)
    # put that object in the scene
    obj.location = Vector(location)
    bpy.context.scene.collection.objects.link(obj)
    return obj

# Blender usefulness exercise #2 - animation
# Animate the two strands of DNA
def animateObj_whole(objList, frameList): # skeleton to transform the entire object
    scn = bpy.context.scene # assuming there is only one scene
    scn.frame_end = frameList[-1]+1 # assuming frameList is monotonically increasing
    for frameNum in frameList:
        scn.frame_set(frameNum+1) # because keyframes are 1-indexed in Blender
        for obj in objList:
            obj.rotation_euler = Vector((0, 0, 2*np.pi*frameNum/frameList[-1]))
            obj.keyframe_insert(data_path='rotation_euler', index=-1)

# Blender usefulness exercise #3 - importing marmoset brain meshes
def loadSTL(fPath=marmosetAtlasPath(), searchStr='*smooth*.stl'):
    fNames=getMeshNames(fPath, searchStr)
    for fName in fNames:
        bpy.ops.import_mesh.stl(filepath=getFileName_full(fPath, fName))

def getMshCenter(msh):
    msh = chkType(msh, 'Mesh')

# Blender usefulness exercise #4 - basic mesh access and manipulation
def getMshCoords(msh):
    msh = chkType(msh, 'Mesh')
    coords = np.array([v.co for v in msh.vertices])
    return coords

def setMshCoords(msh, coords):
    """
    Set vertex positions of a mesh using a numpy array of size nVertices x 3.
    Note that this will only work when blender 3D viewport is in object mode.
    Therefore, this code will temporarily change the 3D viewport mode to Object,
    change the mesh coordinates and switch it back.
    """
    msh = chkType(msh, 'Mesh')
    modeChangeFlag = False
    if not bpy.context.object.mode == 'OBJECT':
        current_mode = bpy.context.object.mode
        modeChangeFlag = True
        bpy.ops.object.mode_set(mode='OBJECT')

    for vertexCount, vertex in enumerate(msh.vertices):
        vertex.co = Vector(coords[vertexCount, :])

    if modeChangeFlag:
        bpy.ops.object.mode_set(mode=current_mode)

def getMesh(msh, mshProperty=None):
    """
    Return a mesh given its name.
    Given an object (or its name), return its mesh.
    """        
    return chkType(msh, 'Mesh')

def getObject(obj):
    """Return an object given its name."""
    return chkType(obj, 'Object')
    
def chkType(inp, inpType='Mesh'):
    """
    Check if a given input is a mesh or an object.
    inpType is either 'Mesh' or 'Object'
    If inp is the name of a mesh/object, then find and return the appropriate python object.
    If you requested a mesh but gave an object name, then return the mesh.
    If you input an object, but are looking for a mesh, return the associated mesh.
    """
    if inpType == 'Mesh':
        inpType_bpyData = 'meshes'
    elif inpType == 'Object':
        inpType_bpyData = 'objects'
    if isinstance(inp, str):
        if inp in [k.name for k in getattr(bpy.data, inpType_bpyData)]:
            return getattr(bpy.data, inpType_bpyData)[inp]
        elif (inpType == 'Mesh') and (inp in [k.name for k in bpy.data.objects]):
            # if you requested a mesh but gave an object name, then return the mesh
            return bpy.data.objects[inp].data
        else:
            raise ValueError("Could not find " + inp + " of type " + inpType)
    if isinstance(inp, bpy.types.Object) and inpType=='Mesh':
        return inp.data # in blender, obj.data points to the mesh corresponding to that object
    if not isinstance(inp, getattr(bpy.types, inpType)):
        # this will only happen if you didn't pass a mesh, object, or an appropriate string
        raise TypeError("Expected input of type bpy.types." + inpType + ", got, " + str(type(inp)) + " instead")
    return inp

# Blender usefulness exercise #5 - add primitives
def addPrimitive(type='monkey', location=(1.0, 3.0, 5.0)):
    """
    Add a primitive at a given location - just simplifies syntax
    type can be circle, cone, cube, cylinder, grid, ico_sphere, uv_sphere,
    monkey, plane, torus
    Adding a primitive while in edit mode will add the primitive to the
    mesh that is being edited in mesh mode! This means that you can inherit
    animations (and perhaps modifiers) by adding to a mesh!
    """
    funcName = 'primitive_'+type+'_add'
    if hasattr(bpy.ops.mesh, funcName):
        getattr(bpy.ops.mesh, funcName)(location=location)
    else:
        raise ValueError(f"{type} is not a valid argument")