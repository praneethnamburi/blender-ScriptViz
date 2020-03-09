"""
Praneeth's blender python module
"""
import errno
import os
import functools
import sys
import types
import numpy as np
import pandas as pd

import bpy #pylint: disable=import-error
import bmesh #pylint: disable=import-error
import mathutils #pylint: disable=import-error

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '.'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

import pntools as pn

PATH = {}
PATH['blender'] = os.path.dirname(pn.locateCommand('blender', verbose=False))
PATH['blender_python'] = os.path.dirname(pn.locateCommand('python', 'blender', verbose=False))
PATH['blender_version'] = os.path.realpath(os.path.join(os.path.dirname(PATH['blender_python']), '../..'))
PATH['blender_scripts'] = os.path.join(PATH['blender_version'], 'scripts')
PATH['blender_addons'] = os.path.join(PATH['blender_scripts'], 'addons')
PATH['blender_addons_contrib'] = os.path.join(PATH['blender_scripts'], 'addons_contrib')
PATH['blender_modules'] = os.path.join(PATH['blender_scripts'], 'modules')
PATH['bpn'] = os.path.dirname(os.path.realpath(__file__))

for path in PATH.values():
    if path not in sys.path:
        sys.path.append(path)

PATH['cache'] = os.path.join(DEV_ROOT, '_temp')

from io_mesh_stl.stl_utils import write_stl #pylint: disable=import-error

PROP_FIELDS = [k for k in dir(bpy.data) if 'bpy_prop_collection' in str(type(getattr(bpy.data, k)))]

### adding whatever you want to execute inside the blender terminal in _blenderWksp.py
# Import bpy from bpn in all scripts from which you will launch blender
bpy.loadStr = ''.join([line for line in open(os.path.join(str(DEV_ROOT), '_blenderWksp.py')) if not '__bpnRemovesThisLine__' in line]).replace('__bpnModifyFilePath__', str(DEV_ROOT).replace('\\', '\\\\'))

### Blender functions
## Decorators for blender
class ReportDelta:
    """
    This class is primarily meant to be used as a decorator.
    This decorator reports changes to blender data (prop collections) after the decorated function is executed.
    Within a script, you can use the decorator syntax, for example
    @reportDelta
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
        self.monFieldNames = PROP_FIELDS

        # initialize generated report
        self.deltaReport = {
            'funcOut'         : [],                 # output of the function passed to this decorator
            'monitoredFields' : self.monFieldNames, # list of monitored fields in bpy.data
            'unchangedFields' : [],                 # list of fields unchanged by func
            'changedFields'   : [],                 # list of fields changed by func
        }

    def __call__(self, *args, **kwargs):
        # get the 'before' state
        propsBefore = Props().__dict__

        # evaluate the function that is going to change blender data, and stash its output
        self.deltaReport['funcOut'] = self.func(*args, **kwargs)

        # get the 'after' state
        propsAfter = Props().__dict__

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

    # def getProps():
    #     """
    #     References to all Props loaded into blender.
        
    #     :returns: Dictionary of prop instances in bpy.data
    #     """
    #     propDict = {}
    #     for fieldName in PROP_FIELDS:
    #         propDict[fieldName] = set(getattr(bpy.data, fieldName))
    #     return propDict


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

class Msh:
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
        undo - Msh().v to values before last modification
        reset - Msh().v to values on object creation

        inflate - inflate Msh().v towards a sphere

        fnv - slow. faces containing vertex i (Msh().f, vertex index i) -> face neighbors of i
        vnv - slow. vertices connected to vertex i (Msh().e, vertex index i) -> vertex neighbors of i
    
    TODO: Add versatility to creation:
    # make a mesh from python data
    Msh(name=name, v=vertices, f=faces)
    Msh(name, v, f)
    Msh(v, f, name='awesomeMesh')
    Msh(v, f)

    # make a mesh from an STL file
    Msh(stlfile, 'awesomeMesh')
    Msh('awesomeMesh', stlfile)
    Msh(stlfile)
    Msh(stlfile, name='awesomeMesh')

    # get a mesh from the blender environment
    Msh(blender mesh name)
    Msh(blender mesh object)
    Msh(blender obj name)

    TODO: Methods:
    m.objects - list of objects employing the current mesh. property
    m.merge(list of meshes) # subsume a collection of meshes, assign vertex groups to keep track of originals
    Note: Use this only with triangular meshes
    """
    def __init__(self, **kwargs):
        """
        :param kwargs: (create mesh from vertices and faces, 2d array, or function)
            msh_name='new_mesh'  
                (str) name of the mesh loaded in blender
                (str) name of an object loaded in blender (get the associated mesh)
                (bpy.types.Mesh) the bpy mesh object
            obj_name='new_obj' (str) name of the object to assign the mesh
            coll_name='new_coll' (str) name of the collection to locate the object
            name='thing' (str) both the mesh and the object will receive this name

            create a mesh from a function:
                xyfun (function with two float inputs and one float output)
                    xyfun = lambda x, y: x*x+y*y
                    A 2d matrix, z, gets created if a function is supplied

            Create a mesh from 2d list or numpy array:
                z (2d list or matrix to render in blender)
                x (list) list or numpy array
                    x = np.arange(-2, 2, 0.02)
                y (list)
                    y = np.arange(-2, 3, 0.2)

            create mesh from vertices and faces:
                v (numpy array of size nVx3, or a 2d list of size nV with 3 element lists of locations)
                f (numpy array of face indices nFx4 is most common, but also a 2d list of size nF typically with 4-element faces)

        """
        if 'msh_name' not in kwargs:
            msh_name = 'new_mesh'
        else:
            msh_name = kwargs.pop('msh_name')

        if 'obj_name' not in kwargs:
            obj_name = 'new_obj'
        else:
            obj_name = kwargs.pop('obj_name')

        if 'name' in kwargs:
            msh_name = kwargs['name']
            obj_name = kwargs['name']

        if 'coll_name' not in kwargs:
            coll_name = 'new_coll'            
        else:
            coll_name = kwargs.pop('coll_name')
        new.collection(coll_name) # create if it doesn't exist

        if 'z' in kwargs or 'xyfun' in kwargs:
            if 'x' not in kwargs:
                if 'z' in kwargs:
                    x = np.arange(0, np.shape(kwargs['z'])[0])
                elif 'xyfun' in kwargs:
                    x = np.arange(-2, 2, 0.1)
            else:
                x = kwargs.pop('x')
            if 'y' not in kwargs:
                if 'z' in kwargs:
                    y = np.arange(0, np.shape(kwargs['z'])[1])
                elif 'xyfun' in kwargs:
                    y = np.arange(-2, 2, 0.1)
            else:
                y = kwargs.pop('y')

        if 'xyfun' in kwargs:
            xyfun = kwargs.pop('xyfun')
            assert isinstance(xyfun, types.FunctionType)
            assert xyfun.__code__.co_argcount == 2 # function has two input arguments
            kwargs['z'] = np.array([[xyfun(xv, yv) for yv in y] for xv in x])

        if 'z' in kwargs:
            z = np.array(kwargs['z'])
            nX = len(x)
            nY = len(y)
            assert nX == np.shape(z)[0]
            assert nY == np.shape(z)[1]
            # matrix to vertices and faces
            kwargs['v'] = [(xv, yv, z[ix][iy]) for iy, yv in enumerate(y) for ix, xv in enumerate(x)]
            kwargs['f'] = [(iy*nX+ix, iy*nX+ix+1, (iy+1)*nX+(ix+1), (iy+1)*nX+ix) for iy in np.arange(0, nY-1) for ix in np.arange(0, nX-1)]

        if 'v' in kwargs and 'f' in kwargs:
            v = kwargs.pop('v')
            f = kwargs.pop('f')

        if 'v' in locals() and 'f' in locals():    
            self.init_from_py(v, f, msh_name, obj_name, coll_name)

        self.init_from_bpy(chkType(msh_name, 'Mesh'))
        self.vInit = self.v # for resetting
        self.vBkp = self.v  # for undoing (switching back and forth)
    
    def init_from_bpy(self, bpy_msh):
        """
        Initialize a bpn mesh from a bpy mesh.
        This is here to increase input flexibility to bpn.Msh's
        __init__ while preserving code readability.
        """
        self.bpy_msh = bpy_msh

    def init_from_py(self, v, f, msh_name, obj_name, coll_name):
        """
        Create a blender mesh from python data, assign it to an object, and put it in a collection.
        :param v: (numpy array of size nVx3, or a 2d list of size nV with 3 element lists of locations)
            3D vertex locations
        :param f: (numpy array of face indices nFx4 is most common, but also a 2d list of size nF typically with 4-element faces)
            Faces
        :param obj_name: (str) name of the object to assign the mesh
        :param coll_name: (str) name of the collection to locate the object
        """
        mesh = bpy.data.meshes.new(msh_name)
        mesh.from_pydata(v, [], f)
        mesh.update(calc_edges=True)
        self.bpy_msh = mesh
        
        obj = bpy.data.objects.new(obj_name, mesh)
        bpy.data.collections[coll_name].objects.link(obj)

    @property
    def v(self):
        """Coordinates of a mesh as an nVx3 numpy array."""
        return np.array([v.co for v in self.bpy_msh.vertices])

    @property
    def vn(self):
        """Vertex normals as an nVx3 numpy array."""
        return np.array([v.normal[:] for v in self.bpy_msh.vertices])
    
    @property
    def f(self):
        """Faces as an nFx3 numpy array."""
        return np.array([polygon.vertices[:] for polygon in self.bpy_msh.polygons])

    @property
    def fn(self):
        """Face normals as an nFx3 numpy array."""
        return np.array([polygon.normal[:] for polygon in self.bpy_msh.polygons])
        
    @property
    def fa(self):
        """Area of faces as an nFx3 numpy array."""
        return np.array([polygon.area for polygon in self.bpy_msh.polygons])
    
    @property
    def fc(self):
        """Coordinates of face centers."""
        return np.array([polygon.center for polygon in self.bpy_msh.polygons])

    @property
    def e(self):
        """Vertex indices of edges."""
        return np.array([edge.vertices[:] for edge in self.bpy_msh.edges])

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
        for vertexCount, vertex in enumerate(self.bpy_msh.vertices):
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
        bpy.data.meshes.remove(self.bpy_msh, do_unlink=True)

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

    def export(self, fName=None, fPath=PATH['cache']):
        """Export a Msh instance into an stl file."""
        if fName is None:
            fName = self.bpy_msh.name + '.stl'

        if fName.lower()[-4:] != '.stl':
            print('File name should end with a .stl')
            return

        # if the full path is supplied as the first argument
        if os.path.dirname(fName):
            if os.path.exists(os.path.dirname(fName)):
                fPath = os.path.dirname(fName)
        fName = os.path.basename(fName)

        v = [tuple(v.co) for v in self.bpy_msh.vertices]
        f = [tuple(polygon.vertices[:]) for polygon in self.bpy_msh.polygons]

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
        return loadSTL([stlfile])['meshes'][0]

class new:
    @staticmethod
    def collection(coll_name='newColl'):
        if coll_name in [c.name for c in bpy.data.collections]:
            col = bpy.data.collections[coll_name]
        else:
            col = bpy.data.collections.new(coll_name)
            bpy.context.scene.collection.children.link(col)
        return col

    @staticmethod
    def obj(msh, col, obj_name='newObj'):
        if isinstance(msh, str):
            msh = bpy.data.meshes[msh]
        if isinstance(col, str):
            col = bpy.data.collections[col]

        if obj_name in [o.name for o in bpy.data.objects]:
            obj = bpy.data.objects[obj_name]
        else:
            obj = bpy.data.objects.new(obj_name, msh)
            col.objects.link(obj)
        return obj

    # Meshes
    @staticmethod
    def msh_sphere(msh_name='newMsh', u=16, v=8, r=0.5):
        if msh_name in [m.name for m in bpy.data.meshes]:
            msh = bpy.data.meshes[msh_name]
        else:
            msh = bpy.data.meshes.new(msh_name)
            bm = bmesh.new()
            bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, diameter=r)
            bm.to_mesh(msh)
            bm.free()
        return msh

    # easy object creation
    @classmethod
    def sphere(cls, obj_name='newObj', msh_name='newMsh', coll_name='newColl', u=16, v=8, r=0.5):
        col = cls.collection(coll_name)
        msh = cls.msh_sphere(msh_name, u=u, v=v, r=r)
        obj = cls.obj(msh, col, obj_name)
        return obj

class Draw:
    """Turtle-like access to bmesh functions."""
    def __init__(self, name_msh='autoMshName', name_obj='autoObjName', name_coll='Collection', name_scene='Scene'):
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
class Props:
    """
    Snapshot of prop collections in blender's data.

    This is an easy way to get references to all Props when you're
    working in blender.

    Construction:
        :param inp_dict: dict. Meant for internal use by operators.

    Usage:
        Props() -> new Props object. Access everything with Props().__dict__
        Props(inpDict) -> turn a dictionary into Props object. Used by
            add and subtract. User shouldn't need to worry about this.
        a = Props()
        # make changes to the scene
        b = Props()
        (b-a)() -> call prop objects to return a dictionary reporting only the changes!
        diff1 = b-a
        # add another mesh to the scene
        c = Props()
        diff2 = c-b
        diff2 | diff1 -> object summarizing all changes
        (b-a).names() -> dictionary of names of changes
        b('Cube') -> Find all Props named 'Cube', returns 
                    dict of {prop type: list of Props with name}
                    {'meshes': [bpy.data.meshes['Cube']], 'objects': [bpy.data.objects['Cube']]}
        b.get('Cube') -> Find all Props named 'Cube', returns 
                    list of Props with 'Cube' in their name, irrespective of prop type
                    [bpy.data.meshes['Cube'], bpy.data.objects['Cube']]
        Props().get('Cube') -> calling this way, as opposed to b.get('Cube') 
                    doesn't seem to have any difference in performance. So, make
                    Props objects only to store states.
    
    Dev note:
        Don't add any properties to this object. Keep it limited to PROP_FIELDS.
        TODO: Change to slots?
    """
    def __init__(self, inp_dict=None):
        if not inp_dict:
            self.__dict__ = {p : set(getattr(bpy.data, p)) for p in PROP_FIELDS}
        else:
            self.__dict__ = inp_dict
    def __or__(self, other): # union
        self.clean()
        return Props({p:self.__dict__[p].union(other.__dict__[p]) for p in PROP_FIELDS})
    def __and__(self, other): # intersection
        self.clean()
        return Props({p:self.__dict__[p].intersection(other.__dict__[p]) for p in PROP_FIELDS})
    def __sub__(self, other): # setdiff
        self.clean()
        return Props({p:self.__dict__[p] - other.__dict__[p] for p in PROP_FIELDS})
    def __xor__(self, other): # exclusive or
        return (self | other) - (self & other)
    def __call__(self, names=None):
        """Dictionary of lists of objects, skip empty collections."""
        self.clean()
        if isinstance(names, str):
            names = [names]
        if not names:
            return {p:list(propset) for p, propset in self.__dict__.items() if propset != set()}
        else: # list of names
            res = {}
            for p, propset in self.__dict__.items():
                if propset != set():
                    res[p] = [prop for prop in propset if prop.name in names]
            return {p:proplist for p, proplist in res.items() if proplist}
    def clean(self):
        """Remove invalid objects (i.e., deleted from blender)."""
        self.__dict__ = {p : {k for k in self.__dict__[p] if 'invalid' not in  str(k)} for p in PROP_FIELDS}
    def get(self, name=''):
        """Get an object by its name."""
        assert isinstance(name, str)
        return [k[0] for k in self(name).values()]
    def names(self, discard_empty=True):
        """Return only the names, and not references to objects."""
        self.clean()
        allNames = {p: {k.name for k in self.__dict__[p]} for p in PROP_FIELDS}
        if discard_empty:
            return {k:v for k, v in allNames.items() if v}
        else:
            return allNames
    def getChildren(self, obj_name):
        """
        Return children of a given object.
        Note that this function will only return children at the bottom most level.
        Example:
            c = bpn.Props().getChildren('Foot_Bones_R')
        """
        if not self.get(obj_name):
            return set() # return empty set if the object isn't found
        children = set((self.get(obj_name)[0],))
        iterFlag = True
        while iterFlag:
            iterFlag = False
            for obj in children:
                if obj.children: # if children exist, remove object, and put children into the set
                    children = children.union(set(obj.children)) - set((obj,))
                    iterFlag = True
        return children

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
    for bpy_data_iter in (bpy.data.objects, bpy.data.meshes, bpy.data.collections):
        # may not work for collections - blender bug
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

    # # if I make a mesh this way, plots don't show up unless I go to edit mode
    # msh.vertices.add(n)
    # msh.edges.add(n-1)
    # for i in range(n):
    #     msh.vertices[i].co = (xVals[i], yVals[i], zVals[i])
    #     if i < n-1:
    #         msh.edges[i].vertices = (i, i+1)
    # return msh

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

## Functions inspired by the anatomy project
def readattr(names, frames=1, attrs='location', fname=False, sheet_name='animation', columns=['object', 'keyframe', 'attribute', 'value']):
    """
    Get location and rotation information of mesh objects from the current blender scene.
    
    Created to save weight in and weight out nutational positions of bones.
    Generalizes to saving location and rotation information for any mesh objects.

    Inputs:
        names: list of names in the blender file, ['Foot_R', 'Leg_R', 'Spine']
            each 'name' can be a blender collection, a parent object (empty), or the name of an object itself
        frames: keyframe numbers in the blender scene to grab location and rotation information from
        attrs: list of attributes ['location', 'rotation_euler', 'scale']
        fname: target file name 'somefile.xlsx'
    
    Returns:
        p: a pandas dataframe containing the name of the mesh, keyframe, location and rotation vectors
        To save contents to an excel file, supply strings to fname, and sheet_name variables

    Example:
        (load skeletalSystem.blend in blender)
        fname = r'D:\Workspace\blenderPython\apps\anatomy\nutations.xlsx'
        p2 = bpn.readattr('Skeletal_Sys', [1, 100], ['location', 'rotation_euler'], fname)
    """
    if isinstance(names, str):
        names = [names] # convert to list if a string is passed
    if isinstance(frames, int):
        frames = [frames]
    if isinstance(attrs, str):
        attrs = [attrs]

    # make sure names has only valid things in it
    names = [i for i in names if Props()(i)]

    p = []
    for frame in frames:
        bpy.context.scene.frame_set(frame)
        for name in names:
            thisProp = Props().get(name)[0]
            if isinstance(thisProp, bpy.types.Collection):
                all_objects = bpy.data.collections[name].all_objects
            elif isinstance(thisProp, bpy.types.Object):
                all_objects = Props().getChildren(name)

            all_objects = [o for o in all_objects if o.type == 'MESH']
            for obj in all_objects:
                for attr in attrs:
                    p.append([obj.name, frame, attr, list(getattr(obj, attr))])

    p = pd.DataFrame(p, columns=columns)
    if isinstance(fname, str):
        p.to_excel(fname, index=False, sheet_name=sheet_name)
    return p

def animate_simple(anim_data, columns=['object', 'keyframe', 'attribute', 'value']):
    """
    Simple keyframe animation in blender. 

    Input:
        anim_data, a pandas data frame with four columns
        Pandas data frame is typically read from an excel file with these four columns
          - object <str> name of the object in blender
          - keyframe <int> frame number
          - attribute <str> attribute name, such as location, rotation_euler, scale
          - value <list> 3-element list in the case of location, rotation_euler and scale

    Result:
        keyframe animation in the blend file
    
    Example:
        (load skeletalSystem_originAtCenter_bkp02.blend)
        fname = r'D:\Workspace\blenderPython\apps\anatomy\nutations.xlsx'
        bpn.animate_simple(fname)
    """
    if isinstance(anim_data, str):
        if os.path.isfile(anim_data):
            anim_data = pd.read_excel(anim_data, sheet_name='animation')

    assert isinstance(anim_data, pd.DataFrame)
    for i in np.arange(0, len(anim_data)):
        propList = Props().get(anim_data.iloc[i][columns[0]]) # columns[0] = 'object'
         
        if len(propList) > 1: # multiple props detected, only keep objects
            propList = [o for o in propList if isinstance(o, bpy.types.Object)]
        
        if not propList: # object doesn't exist in the scene, so skip
            continue
        
        assert len(propList) == 1 # there should really only be one object with that name

        obj = propList[0] 
        frame = anim_data.iloc[i][columns[1]] # columns[1] = 'keyframe'
        attr = anim_data.iloc[i][columns[2]]  # columns[2] = 'attribute'
        val = anim_data.iloc[i][columns[3]]   # columns[3] = 'value'
        if isinstance(val, str):
            val = eval(val) # pylint: disable=eval-used
        bpy.context.scene.frame_set(frame)
        setattr(obj, attr, val)
        obj.keyframe_insert(data_path=attr, frame=frame)

def demo_animate_sphere():
    obj = new.sphere(obj_name='sphere', msh_name='sph', coll_name='myColl')
    frameID = [1, 50, 100]
    loc = [(1, 1, 1), (1, 2, 1), (2, 2, 1)]
    attrs = ['location', 'rotation_euler', 'scale']
    for thisFrame, thisLoc in zip(frameID, loc):
        bpy.context.scene.frame_set(thisFrame)
        for attr in attrs:
            setattr(obj, attr, thisLoc)
            obj.keyframe_insert(data_path=attr, frame=thisFrame)
