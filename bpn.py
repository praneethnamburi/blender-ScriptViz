"""
Praneeth'a blender python module
"""
import errno
import os
import functools
import sys
import numpy as np

import bpy #pylint: disable=import-error
import mathutils #pylint: disable=import-error

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '.'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

BLENDER_ADDON_PATH = os.path.realpath(r'C:\blender\2.80.0\2.80\scripts\addons')
if BLENDER_ADDON_PATH not in sys.path:
    sys.path.append(BLENDER_ADDON_PATH)

CACHE_PATH = os.path.join(DEV_ROOT, '_temp')

from io_mesh_stl.stl_utils import write_stl #pylint: disable=import-error

### adding whatever you want to execute inside the blender terminal in _blenderWksp.py
# Import bpy from bpn in all scripts from which you will launch blender
BPN_DIR = str(os.path.dirname(os.path.realpath(__file__)))
bpy.loadStr = ''.join([line for line in open(os.path.join(BPN_DIR, '_blenderWksp.py')) if not '__bpnRemovesThisLine__' in line]).replace('__bpnModifyFilePath__', BPN_DIR.replace('\\', '\\\\'))

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
        """Dictionary of bpy.data objects"""
        props = {}
        for fieldName in self.monFieldNames:
            props[fieldName] = set(getattr(bpy.data, fieldName)) #[k.name for k in getattr(bpy.data, fieldName)]
        return props

class ModeSet:
    """
    Set the mode of blender's 3D viewport for executing a function func.
    This class is primarily meant to be used as a decorator.
    It can even be used for a setter like so:
    @v.setter
    @ModeSet(targetMode='OBJECT')
    def v(self, thisCoords): # v is the func
        # do stuff with thisCoords here
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

class msh:
    """
    Numpy-like access to blender meshes.

    Properties: 
        v - vertices (can be set, but only as a whole)
        vn - vertex normals
        f - faces (vertex indices)
        fn - face normals
        fc - face centers
        fa - area of each face
        e - edges (vertex indices)
        eL - edge length

        nV - number of vertices
        nF - number of faces
        nE - number of edges

        center - center of the mesh (property object)

        delete - remove a mesh from the blender scene
        undo - msh.v to values before last modification
        reset - msh.v to values on object creation

        inflate - inflate msh.v towards a sphere

        fnv - slow. faces containing vertex i (msh.f, vertex index i) -> face neighbors of i
        vnv - slow. vertices connected to vertex i (msh.e, vertex index i) -> vertex neighbors of i
    
    TODO: Add versatility to creation:
    # make a mesh from python data
    msh(name=name, v=vertices, f=faces)
    msh(name, v, f)
    msh(v, f, name='awesomeMesh')
    msh(v, f)

    # make a mesh from an STL file
    msh(stlfile, 'awesomeMesh')
    msh('awesomeMesh', stlfile)
    msh(stlfile)
    msh(stlfile, name='awesomeMesh')

    # get a mesh from the blender environment
    msh(blender mesh name)
    msh(blender mesh object)
    msh(blender obj name)

    TODO: Methods:
    m.objects - list of objects employing the current mesh. property
    m.merge(list of meshes) # subsume a collection of meshes, assign vertex groups to keep track of originals
    Note: Use this only with triangular meshes
    """
    def __init__(self, *args, **kwargs):
        """
        :param args: (str, bpy.types.Mesh, dict)
                (str) name of a mesh loaded in blender (or object?)
                (bpy.types.Mesh) the bpy mesh object
                (name:str, v:numpy array of nVx3, f:numpy array of nFx3)
        :param kwargs:
            name
        """
        self.init_from_bpy(chkType(bpyMsh, 'Mesh'))
        self.vInit = self.v # for resetting
        self.vBkp = self.v  # for undoing (switching back and forth)
    
    def init_from_bpy(self, bpyMsh):
        """
        Initialize a bpn mesh from a bpy mesh.
        This is here to increase input flexibility to bpn.msh's
        __init__ while preserving code readability.
        """
        self.bpyMsh = bpyMsh

    @property
    def v(self):
        """Coordinates of a mesh as an nVx3 numpy array."""
        return np.array([v.co for v in self.bpyMsh.vertices])

    @property
    def vn(self):
        """Vertex normals as an nVx3 numpy array."""
        return np.array([v.normal[:] for v in self.bpyMsh.vertices])
    
    @property
    def f(self):
        """Faces as an nFx3 numpy array."""
        return np.array([polygon.vertices[:] for polygon in self.bpyMsh.polygons])

    @property
    def fn(self):
        """Face normals as an nFx3 numpy array."""
        return np.array([polygon.normal[:] for polygon in self.bpyMsh.polygons])
        
    @property
    def fa(self):
        """Area of faces as an nFx3 numpy array."""
        return np.array([polygon.area for polygon in self.bpyMsh.polygons])
    
    @property
    def fc(self):
        """Coordinates of face centers."""
        return np.array([polygon.center for polygon in self.bpyMsh.polygons])

    @property
    def e(self):
        """Vertex indices of edges."""
        return np.array([edge.vertices[:] for edge in self.bpyMsh.edges])

    @property
    def eL(self):
        """Edge lengths."""
        e = self.e
        v = self.v
        # This will take forever! Need a better way
        return [np.sqrt(np.sum(np.diff(v[k], axis=0)**2)) for k in e]

    @property
    def nV(self):
        """Number of vertices."""
        return np.shape(self.v)[0]

    @property
    def nF(self):
        """Number of faces."""
        return np.shape(self.f)[0]

    @property
    def nE(self):
        """Number of edges."""
        return np.shape(self.e)[0]

    @v.setter
    # @ModeSet(targetMode='OBJECT') # causing problems - perhaps deselect everything before doing this
    def v(self, thisCoords):
        """
        Set vertex positions of a mesh using a numpy array of size nVertices x 3.
        Note that this will only work when blender 3D viewport is in object mode.
        Therefore, this code will temporarily change the 3D viewport mode to Object,
        change the mesh coordinates and switch it back.
        """
        self.vBkp = self.v # for undo
        for vertexCount, vertex in enumerate(self.bpyMsh.vertices):
            vertex.co = mathutils.Vector(thisCoords[vertexCount, :])

    @property
    def center(self):
        """Return mesh center"""
        return np.mean(self.v, axis=0)

    @center.setter
    def center(self, newCenter):
        self.v = self.v + newCenter - self.center

    def delete(self):
        """Remove the mesh and corresponding objects from blender."""
        bpy.data.meshes.remove(self.bpyMsh, do_unlink=True)

    def undo(self):
        """
        Undo the last change to coords.
        Repeated application of undo will keep switching between the
        last two views.
        """
        self.v, self.vBkp = self.vBkp, self.v

    def reset(self):
        """Reset the mesh to its initalized state"""
        self.v = self.vInit

    def inflate(self, pres=0.2, elas=0.1, delta=0.05, nIter=20):
        """
        Inflate a mesh towards a sphere

        Try this sequence on Suzanne:
        m.inflate(0.2, 0.1, 0.05, 300)
        m.inflate(0.02, 0.1, 0.01, 300)
        m.inflate(0.05, 0.1, 0.01, 300)
        m.inflate(0.1, 0.1, 0.01, 300)
        m.inflate(0.15, 0.1, 0.02, 600)

        Don't normalize pressure vector by area:
        F_p = np.sum(fn[tNei[i]], 0)
        Then, try
        m.inflate(1, 0.1, 0.5, 150)
        """
        newV = self.v
        f = self.f
        e = self.e
        nV = self.nV

        fnv = [self.fnv(f, i) for i in range(nV)] # face neighbors of vertices
        vnv = [self.vnv(e, i) for i in range(nV)] # vertex neighbors of vertices
        for _ in range(nIter):
            fn = self.fn
            fa = self.fa
            for i in range(self.nV):
                F_el = np.sum(newV[vnv[i]] - newV[i], 0) # elastic force vector
                F_p = np.sum(fn[fnv[i]].T*fa[fnv[i]], 1) # pressure force vector
                F = elas*F_el + pres*F_p # sum of elastic and pressure forces
                newV[i] = newV[i] + delta*F
            self.v = newV
        
    def fnv(self, f, i):
        """Face neighbors of a vertex i.
        Faces attached to vertex i, given faces f."""
        return np.flatnonzero(np.sum(f == i, 1))
    
    def vnv(self, e, i):
        """Vertex neighbors of vertex i.
        Vertex indices attached to vertex i, given edges e."""
        return [np.setdiff1d(k, i)[0] for k in e if i in k]

    def export(self, fName='currentOutput.STL', fPath=CACHE_PATH):
        if fName.lower()[-4:] != '.stl':
            print('File name should end with a .stl')
            return

        # if the full path is supplied as the first argument
        if os.path.dirname(fName):
            if os.path.exists(os.path.dirname(fName)):
                fPath = os.path.dirname(fName)
        fName = os.path.basename(fName)

        v = [tuple(v.co) for v in self.bpyMsh.vertices]
        f = [tuple(polygon.vertices[:]) for polygon in self.bpyMsh.polygons]

        # generate faces for blender's write_stl function
        # faces: iterable of tuple of 3 vertex, vertex is tuple of 3 coordinates as float
        # faces = [f1: (v1:(p11, p12, p13), v2:(p21, p22, p23), v3:(p31, p32, p33)), f2:...]
        faces = []
        for face in f:
            thisFace = []
            for vPos in face:
                thisFace.append(v[vPos])
            faces.append(tuple(thisFace))
        write_stl(filepath=os.path.join(fPath, fName), faces=faces, ascii=False)

    def _loadstl(self, stlfile, collection=None):
        return loadSTL([file])['meshes'][0]


### Input-output functions
@ReportDelta
def loadSTL(files, collection=None):
    """
    Load STL files from disk into a blender scene.
    
    :param files: list. Full file paths.
    :param collection: str. Blender collection name to load the STL into.
    :returns: report of scene change
    """
    if isinstance(files, str):
        files = [files]
    for f in files:
        if not os.path.exists(f):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), f)
        bpy.ops.import_mesh.stl(filepath=f)

### Manage blender resources
def get(name):
    pass # TODO: find prop by name, return a reference to that

def rename(old_name, new_name):
    pass # TODO: rename a prop

def reset_blender():
    """
    Reset the current scene programatically.

    Script adapted from:
    https://developer.blender.org/T47418
    """
    # bpy.ops.wm.read_factory_settings()

    for scene in bpy.data.scenes:
        for obj in scene.objects:
            try:
                scene.objects.unlink(obj)
            except:
                pass

    # only worry about data in the startup scene
    for bpy_data_iter in (bpy.data.objects, bpy.data.meshes):
        for id_data in bpy_data_iter:
            try:
                bpy_data_iter.remove(id_data)
            except:
                pass

### Control appearance
def shade(shading='WIREFRAME', area='Layout'):
    """Set shading in the 3D viewport"""
    my_areas = bpy.data.screens[area].areas
    assert shading in ['WIREFRAME', 'SOLID', 'MATERIAL', 'RENDERED']

    for area in my_areas:
        for space in area.spaces:
            if space.type == 'VIEW_3D' and area.type == 'VIEW_3D':
                space.shading.type = shading

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

def plot(x, y, z=0, mshName='autoMshName'):
    if mshName == 'autoMshName':
        objName = 'autoObjName'
    else:
        objName = mshName
    # create a mesh
    msh = genPlotMsh(mshName, x, y, z)
    # instantiate an object
    obj = genObj(msh, objName)
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
