"""
Old functions that are no longer required due to upgrades in bpn Msh class, and other bpn classes and modules

To improve and integrate:
    demo_animateDNA - the old version of the demo is here
"""
import functools
import os
import sys
import numpy as np

import bpy #pylint: disable=import-error
import bmesh #pylint: disable=import-error
import mathutils #pylint: disable=import-error

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

def demo_animateDNA():
    objList, _ = plotDNA()
    animateObj_whole(objList, np.arange(0, 101, 20))
# meshDance
# brainExplosion

## Blender usefulness exercise #1 - Plotting
# Plotting is now integrated into bpn.Msh class!
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

def plot(x, y, z=0, msh_name='autoMshName', coll_name='Collection'):
    if msh_name == 'autoMshName':
        obj_name = 'autoObjName'
    else:
        obj_name = msh_name
    # create a mesh
    msh = genPlotMsh(msh_name, x, y, z)
    # instantiate an object
    obj = genObj(msh, obj_name, coll_name=coll_name)
    return obj, msh

def genPlotMsh(msh_name, xVals, yVals, zVals=None):
    """Generates a mesh for plotting."""
    n = np.size(xVals)
    if zVals is None:
        zVals = np.zeros(n)
    msh = bpy.data.meshes.new(msh_name)
    
    v = [(x, y, z) for x, y, z in zip(xVals, yVals, zVals)]
    e = [(i, i+1) for i in np.arange(0, n-1)]
    msh.from_pydata(v, e, [])
    msh.update()

    return msh

def genObj(msh, name='autoObjName', location=(0.0, 0.0, 0.0), coll_name='Collection'):
    """Generates an object fraom a mesh and attaches it to the current scene."""
    obj = bpy.data.objects.new(name, msh)
    # put that object in the scene
    obj.location = mathutils.Vector(location)
    bpy.data.collections[coll_name].objects.link(obj)
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
        # raise TypeError("Expected input of type bpy.types." + inpType + ", got, " + str(type(inp)) + " instead")
        inp = None
    return inp

###--------- This stuff needs consideration
class Draw:
    """
    TODO: -----OLD----- delete? refactor? restart?
    Turtle-like access to bmesh functions.
    """
    def __init__(self, name_msh='autoMshName', name_obj='autoObjName', name_coll='Collection'):
        self.name_msh = name_msh
        self.name_obj = name_obj
        self.name_coll = name_coll
        self.bm = bmesh.new()
    def __neg__(self):
        bpyMsh = bpy.data.meshes.new(self.name_msh)
        self.bm.to_mesh(bpyMsh)
        self.bm.free()
        show(bpyMsh, name_obj='autoObjName', name_coll='Collection', name_scene='Scene')

def show(bpyMsh, name_obj='autoObjName', name_coll='Collection', name_scene='Scene'):
    """ 
    TODO: -----OLD----- delete? refactor?
    Add mesh to a collection in the current scene.
    
    :param bpyMsh: blender mesh 
        TODO: Add support for Msh class
    :param name_obj: Name of the object
    :param name_coll: Name of the collection. Put object in this collection. New one is made if it's not present.
    :returns: this is a description of what is returned
    """
    obj = bpy.data.objects.new(name_obj, bpyMsh)
    if name_scene not in [k.name for k in bpy.data.scenes]:
        # doesn't make a new scene!
        name_scene = bpy.context.scene.name
    if name_coll not in [k.name for k in bpy.data.collections]:
        myColl = bpy.data.collections.new(name_coll)
        bpy.context.scene.collection.children.link(myColl)
        del myColl
    bpy.data.collections[name_coll].objects.link(obj)

#----------- not fully working yet ----------------
class ModeSet:
    """
    Set the mode of blender's 3D viewport for executing a function func.
    This class is primarily meant to be used as a decorator.
    It can even be used for a setter like so:
    @v.setter
    @ModeSet(targetMode='OBJECT')
    def v(self, thisCoords): # v is the func
        # do stuff with thisCoords here

    Using this in practice has so far caused problems.
    **Archiving for now until the need for this decorator increases.**
    """
    def __init__(self, targetMode='OBJECT'):
        self.targetMode = targetMode

    def __call__(self, func):
        functools.update_wrapper(self, func)
        def wrapperFunc(*args, **kwargs):
            modeChangeFlag = False
            if not bpy.context.object.mode == self.targetMode:
                current_mode = bpy.context.object.mode
                modeChangeFlag = True
                bpy.ops.object.mode_set(mode=self.targetMode)

            funcOut = func(*args, **kwargs)

            if modeChangeFlag:
                bpy.ops.object.mode_set(mode=current_mode)
            return funcOut
        return wrapperFunc
