import os
import functools
import sys
import numpy as np

import bpy #pylint: disable=import-error
import mathutils #pylint: disable=import-error

if os.path.dirname(os.path.realpath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))

### adding whatever you want to execute inside the blender terminal in _blenderWksp.py
# Import bpy from bpn in all scripts from which you will launch blender
BPN_DIR = str(os.path.dirname(os.path.realpath(__file__)))
bpy.loadStr = ''.join([line for line in open(os.path.join(BPN_DIR, '_blenderWksp.py')) if not '__bpnRemovesThisLine__' in line]).replace('__bpnModifyFilePath__', BPN_DIR)

### Blender functions
## Decorators for blender
class ReportDelta:
    """
    This class is primarily meant to be used as a decorator.
    This decorator reports changes to blender data (prop collections) after the decorated function is executed.
    Within a script, you can use the decorator syntax, for example
    @reportDeltaData
    def demo_animateDNA():
        #animation code goes here
        pass
    deltaReport = demo_animateDNA()
    OR
    when using from a terminal, or from within a script, use
    deltaReport = bpy.b.reportDeltaData(bpy.b.demo_animateDNA)()
    This is useful in the console: [print(k, ':', out1[k]) for k in out1]
    """
    def __init__(self, func):
        self.func = func # a function that changes something in the blender data
        functools.update_wrapper(self, func) # to preserve original signatures

        # find all the things to monitor
        self.monFieldNames = [k for k in dir(bpy.data) if 'bpy_prop_collection' in str(type(getattr(bpy.data, k)))]

        # initialize generated report
        self.deltaReport = {
            'funcOut'         : [],                 # output of the function passed to this decorator
            'monitoredFields' : self.monFieldNames, # list of monitored fields in bpy.data
            'unchangedFields' : [],                 # list of fields unchanged by func
            'changedFields'   : [],                 # list of fields changed by func
        }

    def __call__(self, *args, **kwargs):
        # get the 'before' state
        propsBefore = self.getProps()

        # evaluate the function that is going to change blender data, and stash its output
        self.deltaReport['funcOut'] = self.func(*args, **kwargs)

        # get the 'after' state
        propsAfter = self.getProps()

        # find all the new things
        for fieldName in self.monFieldNames:
            thisDelta = propsAfter[fieldName] - propsBefore[fieldName]
            if not thisDelta == set(): # only if something changed
                self.deltaReport[fieldName] = list(thisDelta)
                self.deltaReport['changedFields'].append(fieldName)
            else:
                self.deltaReport['unchangedFields'].append(fieldName)

        # if an object is modified, then arrange meshes and groups according to the object order?
        return self.deltaReport

    def getProps(self):
        props = {}
        for fieldName in self.monFieldNames:
            props[fieldName] = set(getattr(bpy.data, fieldName)) #[k.name for k in getattr(bpy.data, fieldName)]
        return props

### Demo functions that demonstrate some ways to use this API
# Animating DNA
def demo_animateDNA():
    objList, _ = plotDNA()
    animateObj_whole(objList, np.arange(0, 101, 20))
# meshDance
# brainExplosion

## Blender usefulness exercise #1 - Plotting
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
    msh = genPlotMsh(mshName, x, y, z)
    # instantiate an object
    obj = genObj(msh)
    return obj, msh

def genPlotMsh(mshName, xVals, yVals, zVals=None):
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

def genObj(msh, name='autoObjName', location=(0.0, 0.0, 0.0)):
    """Generates an object fraom a mesh and attaches it to the current scene."""
    obj = bpy.data.objects.new(name, msh)
    # put that object in the scene
    obj.location = mathutils.Vector(location)
    bpy.context.scene.collection.objects.link(obj)
    return obj

## Blender usefulness exercise #2 - animation
# Animate the two strands of DNA
def animateObj_whole(objList, frameList): # skeleton to transform the entire object
    scn = bpy.context.scene # assuming there is only one scene
    scn.frame_end = frameList[-1]+1 # assuming frameList is monotonically increasing
    for frameNum in frameList:
        scn.frame_set(frameNum+1) # because keyframes are 1-indexed in Blender
        for obj in objList:
            obj.rotation_euler = mathutils.Vector((0, 0, 2*np.pi*frameNum/frameList[-1]))
            obj.keyframe_insert(data_path='rotation_euler', index=-1)

## Blender usefulness exercise #3 - importing marmoset brain meshes
# ported to marmosetAtlas.py

def getMshCenter(msh):
    msh = chkType(msh, 'Mesh')

## Blender usefulness exercise #4 - basic mesh access and manipulation
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
        vertex.co = mathutils.Vector(coords[vertexCount, :])

    if modeChangeFlag:
        bpy.ops.object.mode_set(mode=current_mode)

def getMsh(msh, mshProperty=None):
    """
    Return a mesh given its name.
    Given an object (or its name), return its mesh.
    """        
    return chkType(msh, 'Mesh')

def getObj(obj):
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
    if isinstance(inp, bpy.types.Object) and inpType == 'Mesh':
        return inp.data # in blender, obj.data points to the mesh corresponding to that object
    if not isinstance(inp, getattr(bpy.types, inpType)):
        # this will only happen if you didn't pass a mesh, object, or an appropriate string
        raise TypeError("Expected input of type bpy.types." + inpType + ", got, " + str(type(inp)) + " instead")
    return inp

# Blender usefulness exercise #5 - add primitives
def addPrimitive(pType='monkey', location=(1.0, 3.0, 5.0)):
    """
    Add a primitive at a given location - just simplifies syntax
    pType can be circle, cone, cube, cylinder, grid, ico_sphere, uv_sphere,
    monkey, plane, torus
    Adding a primitive while in edit mode will add the primitive to the
    mesh that is being edited in mesh mode! This means that you can inherit
    animations (and perhaps modifiers) by adding to a mesh!
    """
    funcName = 'primitive_'+pType+'_add'
    if hasattr(bpy.ops.mesh, funcName):
        getattr(bpy.ops.mesh, funcName)(location=location)
    else:
        raise ValueError(f"{pType} is not a valid argument")