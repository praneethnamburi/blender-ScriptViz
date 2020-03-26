"""
Praneeth's blender python module
"""
import errno
import functools
import inspect
import math
import os
import sys
import types
import numpy as np
import pandas as pd

import bpy #pylint: disable=import-error
import bmesh #pylint: disable=import-error
import mathutils #pylint: disable=import-error

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

import pntools as pn

if __package__ is not None:
    from . import new, env, demo, utils, turtle, vef, trf
    from .env import Props, ReportDelta
    from .turtle import Draw
    from .trf import CoordFrame

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

### add whatever you want to execute inside the blender terminal in _blenderwksp.py
# Import bpy from bpn in all scripts from which you will launch blender
loadStr = ''.join([line for line in open(os.path.join(str(DEV_ROOT), 'bpn\\_blenderwksp.py')) if not '__bpnRemovesThisLine__' in line]).replace('__bpnModifyFilePath__', str(DEV_ROOT).replace('\\', '\\\\'))

class Msh(pn.Track):
    """
    Numpy-like access to blender meshes.

    Think of an instance of this class as a bpy object, its corresponding mesh and the collection of the object.

    Properties: 
        m - blender mesh, p.m.name to get the name of the mesh
        o - blender object, p.o.name to get the name of the object
        c - blender collection, p.c.name to get the name of the collection
        inp - (dict) kwargs are stored here
        vInit - initial set of vertices for resetting
        vBkp - history of 1 action (mainly for switching back and forth)
        TODO: increase history to 10 actions with a buffer, but keep the first one
        TODO: also save edges and faces in history

        v - vertices (can be set, but only as a whole)
        v_world - vertices in world co-ordinates
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
    
    # Creation:
        Broadly, Msh objects can be created from:
        - (type=stl) an STL file import
        - (type=blend) the blender environment
        - (type=vfedata) creating vertex, faces, and edges from data
            - (type=fun) a 2d function that takes two floats as input and produces one output
                xyfun -> x (list), y (list), z (2D list) -> v, f (e=automatically calculated) -> mesh
                xyfun (function with two float inputs and one float output)
                    xyfun = lambda x, y: x*x+y*y
            - (type=mat) a 2d matrix or list
                - x (list), y(list), z (2D list) -> v, f (e=automatically created) -> mesh
            - (type=plot) a 3d plot
                - x (list), y(list), z (list) -> v, e (no faces) -> mesh
        - (type=primitive) a selected set of primitives (use bpn.new for this!)
            - sphere {'u':16, 'v':8, 'r':0.5}
            - cube {'size':0.5}
            - monkey {}
            - cone {'n':12, 'r1':2, 'r2':0, 'd':3, 'cap_ends':True, 'cap_tris':False}
            - ngon {'n':6, 'r1':2, 'r2':0, 'cap_ends':False, 'cap_tris':False}
            - polygon - alias for ngon
            - circle {n=32, r=1} (doesn't produce faces, use ngon for that)

    TODO: Update help and documentation for this:
    # make a mesh from python data
    Msh(name=name, v=vertices, f=faces)
    Msh(v=v1, f=f1)
    Msh(v=v1, e=e1)
    Msh(v=v1, e=e1, f=f1)
    # name, msh_name, obj_name, coll_name behave as usual

    # make a mesh from an STL file
    Msh(stl=stlfile)
    Msh(stl=stlfile, name='awesome') # mesh and object get the same name
    Msh(stl=stlfile, coll_name='myColl') # put msh in a collection coll_name
    Msh(stlfile, name='awesome', msh_name='awesomeMesh', coll_name='myColl')
    Msh(stlfile, msh_name='awesomeMesh', obj_name='awesomeObj', coll_name='myColl')

    # get a mesh from the blender environment
    Msh(name=blender mesh name)
    Msh(name=blender obj name)
    Msh(name=blender mesh object) # works, but not recommended

    # make a mesh from a 2d function
    Msh(xyfun=lambda x, y: x*x+y*y, name='parabola')

    TODO: Methods:
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
            coll_name='new_coll' (str) name of the collection to locate the object / to place the created object
            name='thing' (str) both the mesh and the object will receive this name
                name will get overwritten by msh_name or obj_name if present
            stl=stlfilename (str) name of stl file to import

            Create a mesh from a function:
                xyfun (function with two float inputs and one float output)
                    xyfun = lambda x, y: x*x+y*y
                    A 2d matrix, z, gets created if a function is supplied

            Create a mesh from 2d list or numpy array (xyz):
                z (2d list or matrix to render in blender)
                x (list) list or numpy array
                    x = np.arange(-2, 2, 0.02)
                y (list)
                    y = np.arange(-2, 3, 0.2)
            
            Create a mesh from vertices and faces (vef):
                v (numpy array of size nVx3, or a 2d list of size nV with 3 element lists of locations)
                    Vertices
                f (numpy array of face indices nFx4 is most common, but also a 2d list of size nF typically with 4-element faces)
                    Faces

            Create a 3d plot (xyz):
                z (list) with n elements
                x (list) with n elements
                y (list) with n elements
                
            Create a 'line' from vertices and edges (vef):
                v (numpy array of size nVx3, or a 2d list of size nV with 3 element lists of locations)
                    Vertices
                e (numpy array of size nEx2, or a 2d list of size nE with 2 element lists of vertex index)
                    Edges connecting vertices
            
            More generally, supply v=myVertices, e=myEdges, f=myFaces to create a mesh
        """
        self.bm = None # Initializing here, they will be set by one of the _setmoc functions
        self.bo = None
        self.bc = None
        if 'stl' in kwargs:
            self._setmoc_stl(kwargs['stl'], kwargs)
        else:
            self._setmoc(kwargs)
        # TODO: This system is vulnerable to renames, what about mesh and collection re-assignments?
        self.name = {'msh': self.bm.name, 'obj': self.bo.name, 'coll': self.bc.name}
        self.inp = kwargs
        self.vInit = self.v # for resetting
        self.vBkp = self.v  # for undoing (switching back and forth)
        super().__init__() # self.track(self)
    
    def _setmoc_stl(self, stlfile, kwargs):
        """
        Import from an stl file. Note that the bpn object will be created from  the first object in the file.
        """
        assert os.path.isfile(stlfile)
        s = loadSTL([stlfile])
        self.bm = s['meshes'][0] # bm - blender mesh bpy.data.meshes
        self.bo = s['objects'][0] # bo - blender object bpy.data.objects
        self.bc = s['objects'][0].users_collection[0] # bc - blender collection bpy.data.collections

        if 'name' in kwargs:
            self.bm.name = kwargs['name']
            self.bo.name = kwargs['name']

        if 'msh_name' in kwargs:
            self.bm.name = kwargs['msh_name']
        
        if 'obj_name' in kwargs:
            self.bo.name = kwargs['obj_name']
        
        if 'coll_name' in kwargs:
            col = new.collection(kwargs['coll_name'])
            col.objects.link(self.bo)
            self.bc.objects.unlink(self.bo)
            self.bc = col

    def _setmoc(self, kwargs):
        """
        Parse keyword arguments to set mesh, object and collection.
        """
        if 'msh_name' not in kwargs:
            msh_name = kwargs['name'] if 'name' in kwargs else 'new_mesh'
        else:
            msh_name = kwargs['msh_name']

        if 'obj_name' not in kwargs:
            obj_name = kwargs['name'] if 'name' in kwargs else 'new_obj'
        else:
            obj_name = kwargs['obj_name']

        if 'coll_name' not in kwargs:
            coll_name = 'Collection'            
        else:
            coll_name = kwargs['coll_name']
        
        # if obj_name exists, use object and corresponding mesh
        if obj_name in [o.name for o in bpy.data.objects]:
            self.bo = bpy.data.objects[obj_name]
            self.bm = self.bo.data
            self.bc = self.bo.users_collection[0]
            # if the object exists, but is in a different collection than coll_name, nothing happens
            # use Msh.to_coll(coll_name) explicitly to achieve this
        else:
            # if mesh exists, assign it to the object, and put it in collection
            if msh_name in [m.name for m in bpy.data.meshes]:
                self.bm = bpy.data.meshes[msh_name]
            else: # if mesh doesn't exist, make the mesh
                self.bm = self._make_mesh(msh_name, kwargs)
            # object doesn't exist, so make it and link it to the scene
            self.bo = bpy.data.objects.new(obj_name, self.bm)
            self.bc = new.collection(coll_name) # create if it doesn't exist
            self.bc.objects.link(self.bo)

    def _make_mesh(self, msh_name, kwargs):
        """
        This mesh creation function is invoked only if mesh specified by msh_name does not exist.
        """
        if 'z' in kwargs or 'xyfun' in kwargs:
            if 'x' not in kwargs:
                if 'z' in kwargs and len(np.shape(kwargs['z'])) == 2:
                    x = np.arange(0, np.shape(kwargs['z'])[0])
                elif 'xyfun' in kwargs:
                    x = np.arange(-2, 2, 0.1)
            else:
                x = kwargs['x']
            if 'y' not in kwargs:
                if 'z' in kwargs and len(np.shape(kwargs['z'])) == 2:
                    y = np.arange(0, np.shape(kwargs['z'])[1])
                elif 'xyfun' in kwargs:
                    y = np.arange(-2, 2, 0.1)
            else:
                y = kwargs['y']

        if 'xyfun' in kwargs:
            xyfun = kwargs['xyfun']
            assert isinstance(xyfun, types.FunctionType)
            assert xyfun.__code__.co_argcount == 2 # function has two input arguments
            kwargs['z'] = np.array([[xyfun(xv, yv) for yv in y] for xv in x])

        if 'z' in kwargs:
            z = np.array(kwargs['z'])
            if len(np.shape(z)) == 2: # 2D array, surface plot
                nX = len(x)
                nY = len(y)
                assert nX == np.shape(z)[0]
                assert nY == np.shape(z)[1]
                # matrix to vertices and faces
                kwargs['v'] = [(xv, yv, z[ix][iy]) for iy, yv in enumerate(y) for ix, xv in enumerate(x)]
                kwargs['f'] = [(iy*nX+ix, iy*nX+ix+1, (iy+1)*nX+(ix+1), (iy+1)*nX+ix) for iy in np.arange(0, nY-1) for ix in np.arange(0, nX-1)]
            if len(np.shape(z)) == 1: # 3D plot!
                kwargs['v'], kwargs['e'], _ = vef.xyz2vef(x, y, z)

        if 'v' in kwargs and ('f' in kwargs or 'e' in kwargs):
            if 'e' not in kwargs:
                kwargs['e'] = []
            if 'f' not in kwargs:
                kwargs['f'] = []
            msh = bpy.data.meshes.new(msh_name)
            msh.from_pydata(kwargs['v'], kwargs['e'], kwargs['f'])
            if not kwargs['e']:
                msh.update(calc_edges=True)
            else:
                msh.update()
        return msh

    @property
    def v(self):
        """Coordinates of a mesh as an nVx3 numpy array."""
        return np.array([v.co for v in self.bm.vertices])

    @property
    def v_world(self):
        """Return world coordinates as nVx3 numpy array."""
        bpy.context.view_layer.update()
        return trf.apply_matrix(self.bo.matrix_world, self.v) #apply_matrix from trf
    
    @property
    def frame(self):
        """
        Unit frame of reference for the current mesh.
        """
        return trf.CoordFrame(m=self.bo.matrix_world, unit_vectors=False) # scaling is included in this?!

    @property
    def vn(self):
        """Vertex normals as an nVx3 numpy array."""
        return np.array([v.normal[:] for v in self.bm.vertices])
    
    @property
    def f(self):
        """Faces as an nFx3 numpy array."""
        return np.array([polygon.vertices[:] for polygon in self.bm.polygons])

    @property
    def fn(self):
        """Face normals as an nFx3 numpy array."""
        return np.array([polygon.normal[:] for polygon in self.bm.polygons])
        
    @property
    def fa(self):
        """Area of faces as an nFx3 numpy array."""
        return np.array([polygon.area for polygon in self.bm.polygons])
    
    @property
    def fc(self):
        """Coordinates of face centers."""
        return np.array([polygon.center for polygon in self.bm.polygons])

    @property
    def e(self):
        """Vertex indices of edges."""
        return np.array([edge.vertices[:] for edge in self.bm.edges])

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
        for vertexCount, vertex in enumerate(self.bm.vertices):
            vertex.co = mathutils.Vector(thisCoords[vertexCount, :])

    @property
    def center(self):
        """Return mesh center"""
        return np.mean(self.v, axis=0)

    @center.setter
    def center(self, new_center):
        self.v = self.v + new_center - self.center

    def delete(self):
        """Remove the mesh and corresponding objects from blender."""
        bpy.data.meshes.remove(self.bm, do_unlink=True)

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
            fName = self.bm.name + '.stl'

        if fName.lower()[-4:] != '.stl':
            print('File name should end with a .stl')
            return

        # if the full path is supplied as the first argument
        if os.path.dirname(fName):
            if os.path.exists(os.path.dirname(fName)):
                fPath = os.path.dirname(fName)
        fName = os.path.basename(fName)

        v = [tuple(v.co) for v in self.bm.vertices]
        f = [tuple(polygon.vertices[:]) for polygon in self.bm.polygons]

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

    def refresh(self):
        """
        Refresh if blender does memory management and moves things.
        """
        if 'invalid' in str(self.bm).lower():
            self.bm = bpy.data.meshes[self.name['msh']] #pylint: disable=attribute-defined-outside-init
        if 'invalid' in str(self.bo).lower():
            self.bo = bpy.data.objects[self.name['obj']] #pylint: disable=attribute-defined-outside-init
        if 'invalid' in str(self.bc).lower():
            self.bc = bpy.data.collections[self.name['coll']] #pylint: disable=attribute-defined-outside-init

    # object properties
    @property
    def loc(self):
        """Object location (not mesh!)"""
        return self.bo.location
    @loc.setter
    def loc(self, new_loc):
        assert len(new_loc) == 3
        self.bo.location = new_loc
        bpy.context.view_layer.update()

    @property
    def rot(self):
        """Object rotation"""
        return self.bo.rotation_euler
    @rot.setter
    def rot(self, theta):
        self.bo.rotation_euler.x = theta[0]
        self.bo.rotation_euler.y = theta[1]
        self.bo.rotation_euler.z = theta[2]
        bpy.context.view_layer.update()

    @property
    def scl(self):
        """Object scale"""
        return self.bo.scale
    @scl.setter
    def scl(self, s):
        self.bo.scale = mathutils.Vector(s)
        bpy.context.view_layer.update()

    # object transforms - update view_layer after any transform operating on the object (bo)
    def translate(self, delta=0, x=0, y=0, z=0):
        """
        Move an object by delta.
        delta is a 3-element tuple, list, numpy array or Vector
        sph.translate((0, 0, 0.6))
        sph.translate(z=0.6)
        """
        if 'numpy' in str(type(delta)):
            delta = tuple(delta)
        if delta == 0:
            delta = (x, y, z)
        assert len(delta) == 3
        self.bo.location = self.bo.location + mathutils.Vector(delta)
        bpy.context.view_layer.update()
        return self
    
    def rotate(self, theta, inp_type='degrees', frame='global'):
        """
        Rotate an object.
        theta is a 3-element tuple, list, numpy array or Vector
        inp_type is 'degrees' (default) or 'radians'
        frame of reference is either 'global' or 'local'
        """
        assert len(theta) == 3
        if inp_type == 'degrees':
            theta = [math.radians(θ) for θ in theta]
        if frame == 'local':
            self.bo.rotation_euler.x = self.bo.rotation_euler.x + theta[0]
            self.bo.rotation_euler.y = self.bo.rotation_euler.y + theta[1]
            self.bo.rotation_euler.z = self.bo.rotation_euler.z + theta[2]
        else: #frame = global
            self.bo.rotation_euler.rotate(mathutils.Euler(tuple(theta)))
        bpy.context.view_layer.update()
        return self

    def scale(self, delta):
        """
        Scale an object.
        delta is a 3-element tuple, list, numpy array or Vector
        """
        if isinstance(delta, (int, float)):
            self.bo.scale = self.bo.scale*float(delta)
        else:
            assert np.size(delta) == 3
            self.bo.scale = mathutils.Vector(np.array(delta)*np.array(self.bo.scale))
        bpy.context.view_layer.update()
        return self

    def subsurf(self, levels=2, render_levels=3, name=None):
        """Subsurf modifier, because it is so common."""
        if not name:
            name = utils.new_name('subd', [m.name for m in self.bo.modifiers])
        self.bo.modifiers.new(name, type='SUBSURF')
        self.bo.modifiers[name].levels = levels
        self.bo.modifiers[name].render_levels = render_levels
    
    # transforms on mesh vertices
    def shade(self, typ='smooth'):
        """
        Easy access to set shading.
        Extend this to mark sharpe edges, and define smoothing only for some faces
        """
        assert typ in ('smooth', 'flat')
        poly_smooth = True if typ == 'smooth' else False
        for p in self.bm.polygons:
            p.use_smooth = poly_smooth

    def apply_matrix(self):
        """
        Apply world transformation coordinates to the mesh vertices.
        CAUTION: Applies matrix to the MESH directly and NOT the object!!
        It also resets matrix_world
        Note that this move will move the mesh center to origin.
        """
        self.vBkp = self.v # for undoing
        self.v = trf.apply_matrix(self.bo.matrix_world, self.v)
        self.bo.matrix_world = mathutils.Matrix(np.eye(4))
        bpy.context.view_layer.update()
        return self
    
    def slice_ax(self, axis='x', slice_dir='neg'):
        """
        Use a plane as a slicer and set all vertices below it to zero.
        """
        assert slice_dir in ('pos', 'neg')
        if isinstance(axis, str):
            axis = {'x':0, 'y':1, 'z':2}[axis]
        self.vBkp = self.v

        # apply matrix, do your thing, apply inverse, then put the original matrix back in
        m = self.bo.matrix_world.copy()
        mi = m.copy()
        mi.invert()
        self.apply_matrix()

        v = self.v
        if slice_dir == 'neg':
            v[v[:, axis] < 0, axis] = 0
        else:
            v[v[:, axis] > 0, axis] = 0
        self.v = v

        self.bo.matrix_world = mi
        self.apply_matrix()
        self.bo.matrix_world = m
        bpy.context.view_layer.update()
        return self

    slice_x = functools.partialmethod(slice_ax, axis='x')
    slice_y = functools.partialmethod(slice_ax, axis='y')
    slice_z = functools.partialmethod(slice_ax, axis='z')

    # animation
    def key(self, frame=None, target='lrs', values=None):
        """
        Easy keying. Useful for playing around in the command line, or iterating ideas while keeping history.
        :param frame: (int) Uses current frame number if nothing is specified.
        :param target: (str) recommended use - one of 'l', 'r', 's', 'lrs', 'lr', 'ls', 'rs'
        :param values: (list) each element of the list should be a 3-tuple
            If you have only one parameter to change, still supply [(1, 2, 3)] instead of (1, 2, 3)

        Note that if values are not specified, current numbers will be used.
        Example:
            s = bpn.new.sphere(name='sphere')
            s.key(1)
            s.loc = (2, 2, 2) # this location will be keyed into frame 26!
            s.key(26)
            s.scl = (1, 0.2, 1)
            s.key(51)
        """
        assert isinstance(target, str)
        target = target.lower()

        if target in ['l', 'loc', 'location']:
            attrs = ['location']
        if target in ['r', 'rot', 'rotation', 'rotation_euler']:
            attrs = ['rotation_euler']
        if target in ['s', 'scl', 'scale']:
            attrs = ['scale']
        if target in ['lrs', 'locrotscale', 'locrotscl']:
            attrs = ['location', 'rotation_euler', 'scale']
        if target in ['lr', 'locrot']:
            attrs = ['location', 'rotation_euler']
        if target in ['ls', 'locscl', 'locscale']:
            attrs = ['location', 'rotation_euler']
        if target in ['rs', 'rotscl', 'rotscale']:
            attrs = ['rotation_euler', 'scale']

        if not values:
            values = [tuple(getattr(self.bo, attr)) for attr in attrs]
            # for some reason, s.key() doesn't take current values if I don't use tuple
        
        frame_current = bpy.context.scene.frame_current
        if not frame:
            frame = frame_current
        bpy.context.scene.frame_set(frame)
        for attr, value in zip(attrs, values):
            setattr(self.bo, attr, value)
            self.bo.keyframe_insert(data_path=attr, frame=frame)
        # bpy.context.scene.frame_set(frame_current)

        return self # so you can chain keyings into one command

    def morph(self, n_frames=50, frame_start=1):
        """
        Morphs the mesh from initial vertex positions to current vertex positions.
        CAUTION: Using this multiple times on the same object can cause unpredictable behavior.
        """
        v_orig = self.vInit
        v_targ = self.v
        frame_end = frame_start + n_frames
        def my_handler(scene):
            p = (scene.frame_current-frame_start)/(frame_end-frame_start)
            self.v = (1-p)*v_orig + p*v_targ
        bpy.app.handlers.frame_change_pre.append(my_handler)

    def to_coll(self, coll_name, typ='move'):
        """
        Move this object to a collection.

        :param coll_name: (str)
            A collection will be created if a collection by coll_name doesn't exist
        :param typ: (str) 'copy' or 'move'
            Note that copy won't copy the object itself. It will simply keep the same object in both collections. 
            Use Msh.copy or Msh.deepcopy to achieve this.
        """
        assert isinstance(coll_name, (bpy.types.Collection, str))
        assert typ in ['copy', 'move']
        oldC = self.bc
        if isinstance(coll_name, str):
            self.bc = new.collection(coll_name)
        else:
            self.bc = coll_name
        if coll_name not in [c.name for c in self.bo.users_collection]: # link only if the object isn't in collection already
            self.bc.objects.link(self.bo)
            if typ == 'move':
                oldC.objects.unlink(self.bo)

    @property
    def m(self):
        """
        Easy access to blender mesh.
        """
        return self.bm
    
    @m.setter
    def m(self, new_m):
        """
        Objects can have animations. Use this property to change the mesh, but preserve all the animations
        """
        assert isinstance(new_m, str) or isinstance(new_m, bpy.types.Mesh)
        if isinstance(new_m, str):
            all_msh = [tm.name for tm in bpy.data.meshes]
            if new_m in all_msh:
                new_m = bpy.data.meshes[new_m]
            else:
                new_m = []

        if new_m: # set only if it exists
            self.bo.data = new_m
            self.bm = new_m
        else:
            print('Mesh does not exist!')

    @property
    def o(self):
        """
        Easy access to the object. Currenty, this cannot be set.
        """
        return self.bo

    @property
    def c(self):
        """
        Easy access to blender collection. When supplied with a new name, object moves into that collection.
        """
        return self.bc

    @c.setter
    def c(self, coll_name):
        self.to_coll(coll_name, 'move')

    def copy(self, obj_name=None, coll_name=None):
        """
        Make a copy of the object, keep the same mesh and put it in the same collection.
        Use the same animation data!
        """
        this_o = self.bo.copy()
        if isinstance(obj_name, str):
            this_o.name = obj_name
        if isinstance(coll_name, str):
            new.collection(coll_name).objects.link(this_o)
        else:
            self.bc.objects.link(this_o)
        return Msh(obj_name=this_o.name)

    def deepcopy(self, obj_name=None, coll_name=None, msh_name=None):
        """
        Make a copy of everything - object, mesh and animation
        """
        this_o = self.bo.copy()
        this_o.data = this_o.data.copy()
        if isinstance(obj_name, str):
            this_o.name = obj_name
        if isinstance(coll_name, str):
            new.collection(coll_name).objects.link(this_o)
        else:
            self.bc.objects.link(this_o)
        if isinstance(msh_name, str):
            this_o.data.name = msh_name
        return Msh(obj_name=this_o.name)

def get(obj_name=None):
    """
    Create a bpn msh object from object name
    bpn.obj('sphere')
    :param obj_name: (str) name of the object in blender's environment
    """
    if not obj_name: # return the last objects
        return Msh(obj_name=[o.name for o in bpy.data.objects][-1])

    if isinstance(obj_name, str) and (obj_name not in [o.name for o in bpy.data.objects]):
        print('No object found with name: ' + obj_name)
        return []

    return Msh(obj_name=obj_name)

### Input-output functions
@ReportDelta
def loadSTL(files):
    """
    Load STL files from disk into a blender scene.
    
    :param files: list. Full file paths.
    :param collection: str. Blender collection name to load the STL into.
    :returns: report of scene change

    Recommended use:
        Instead of directly using this function, use 
        p = bpn.Msh(stl=fname, name='mySTL', coll_name='myColl')
    """
    if isinstance(files, str):
        files = [files]
    for f in files:
        if not os.path.exists(f):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), f)
        bpy.ops.import_mesh.stl(filepath=f)


### Demo functions that demonstrate some ways to use this API
# Animating DNA - re-do this part!

## Functions inspired by the anatomy project
def readattr(names, frames=1, attrs='location', fname=False, sheet_name='animation', columns=('object', 'keyframe', 'attribute', 'value')):
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
        fname = 'D:\\Workspace\\blenderPython\\apps\\anatomy\\nutations.xlsx'
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

    p = pd.DataFrame(p, columns=list(columns))
    if isinstance(fname, str):
        p.to_excel(fname, index=False, sheet_name=sheet_name)
    return p

def animate_simple(anim_data, columns=None, propfunc=None):
    """
    Simple keyframe animation in blender. 

    :param anim_data: (pandas.DataFrame)
        A pandas data frame with four columns
    :param columns: (list of strings)
        Pandas data frame is typically read from an excel file with these four columns
          - object <str> name of the object in blender
          - keyframe <int> frame number
          - attribute <str> attribute name, such as location, rotation_euler, scale
          - value <list> 3-element list in the case of location, rotation_euler and scale
    :param propfunc: (types.FunctionType)
        Function used to create an object if it does not exist
        Default: create a uv sphere
        Use functools.partial to pass default arguments to your favorite creation function.
        The object name is drawn from the excel file.
        Note: 
            If you supply 'msh_name' argument, then the same mesh will be used for all the objects created.
                propfunc=functools.partial(new.sphere, **{'coll_name':'Points', 'msh_name':'sph', 'u':16, 'v':8, 'r':0.1})
            If not, the mesh name is same as the object name.
                propfunc=functools.partial(new.sphere, **{'coll_name':'Points', 'u':16, 'v':8, 'r':0.1})
    Result:
        keyframe animation in the blend file
    
    Example:
        (load skeletalSystem_originAtCenter_bkp02.blend)
        fname = 'D:\\Workspace\\blenderPython\\apps\\anatomy\\nutations.xlsx'
        bpn.animate_simple(fname)
    """
    def get_obj_list(obj_name):
        prop_list = Props().get(obj_name) 
        if len(prop_list) > 1: # multiple props detected, only keep objects
            prop_list = [o for o in prop_list if isinstance(o, bpy.types.Object)]
        return prop_list

    if propfunc is None:
        propfunc = functools.partial(new.sphere, **{'coll_name':'Points', 'u':16, 'v':8, 'r':0.1})

    if columns is None:
        columns = ['object', 'keyframe', 'attribute', 'value']

    if isinstance(anim_data, str):
        if os.path.isfile(anim_data):
            anim_data = pd.read_excel(anim_data, sheet_name='animation')

    assert isinstance(anim_data, pd.DataFrame)
    for i in np.arange(0, len(anim_data)):
        this_obj_name = anim_data.iloc[i][columns[0]] # columns[0] = 'object'
        prop_list = get_obj_list(this_obj_name)
        
        if not prop_list: # object doesn't exist in the scene, create it!
            if isinstance(propfunc, functools.partial):
                inp_dict = [a[1] for a in inspect.getmembers(propfunc) if a[0] == 'keywords'][0]
                if 'msh_name' in inp_dict:
                    this_msh_name = inp_dict['msh_name']
                else: # if msh_name is not present, create a new mesh for each object
                    this_msh_name = this_obj_name

            propfunc(obj_name=this_obj_name, msh_name=this_msh_name)
            prop_list = get_obj_list(this_obj_name)
        
        assert len(prop_list) == 1 # there should really only be one object with that name

        obj = prop_list[0] 
        frame = anim_data.iloc[i][columns[1]] # columns[1] = 'keyframe'
        attr = anim_data.iloc[i][columns[2]]  # columns[2] = 'attribute'
        val = anim_data.iloc[i][columns[3]]   # columns[3] = 'value'
        if isinstance(val, str):
            val = eval(val) # pylint: disable=eval-used
        bpy.context.scene.frame_set(frame)
        setattr(obj, attr, val)
        obj.keyframe_insert(data_path=attr, frame=frame)
