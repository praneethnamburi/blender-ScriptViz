"""
Core of the blender python module.

Msh class is the heart of the module. Think of a Msh object as a group
with a blender object (bpy.data.objects), mesh (bpy.data.meshes), and
collection (bpy.data.collection).
"""
import functools
import math
import os
import types
import copy

import numpy as np

import pntools as pn

import bpy #pylint: disable=import-error
import bmesh #pylint: disable=import-error
import mathutils #pylint: disable=import-error
from io_mesh_stl.stl_utils import write_stl #pylint: disable=import-error

from . import new, utils, vef, trf, io

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
        s = io.loadSTL([stlfile])
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
            col = Collection(kwargs['coll_name'])()
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
            self.bc = Collection(coll_name)() # create if it doesn't exist
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

    #PORTED
    @property
    def v(self):
        """Coordinates of a mesh as an nVx3 numpy array."""
        return np.array([v.co for v in self.bm.vertices])

    @property
    def v_world(self):
        """Return world coordinates as nVx3 numpy array."""
        bpy.context.view_layer.update()
        return trf.apply_matrix(self.bo.matrix_world, self.v) #apply_matrix from trf
    
    # PORTED
    @property
    def frame(self):
        """
        Unit frame of reference for the current mesh.
        """
        return trf.CoordFrame(self.bo.matrix_world, unit_vectors=False) # scaling is included in this?!

    # PORTED
    @frame.setter
    def frame(self, new_frame):
        """Points go with the frame! Simply changes matrix_world."""
        if type(new_frame).__name__ == 'CoordFrame':
            new_frame = new_frame.m
        self.bo.matrix_world = mathutils.Matrix(new_frame)
        bpy.context.view_layer.update()

    # MESH + OBJECT - PORTED
    @property
    def pts(self):
        """Return vertices as a trf.PointCloud object."""
        return trf.PointCloud(self.v, self.frame)

    @pts.setter
    def pts(self, new_pts):
        """
        Set the vertices AND the frame. In other words, transform the
        point cloud into the desired frame of reference before putting
        it here.
        """
        assert type(new_pts).__name__ == 'PointCloud'
        self.v = new_pts.co
        self.frame = new_pts.frame

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

    # PORTED
    @v.setter
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
        bpy.context.view_layer.update()

    # PORTED
    @property
    def center(self):
        """Return mesh center"""
        return np.mean(self.v, axis=0)

    @center.setter
    def center(self, new_center):
        self.v = self.v + new_center - self.center

    # Superseded by __neg__??
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

    def export(self, fName=None, fPath=None):
        """Export a Msh instance into an stl file."""
        if fPath is None:
            fPath = utils.PATH['cache']

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

    # MESH
    def shade(self, typ='smooth'):
        """
        Easy access to set shading.
        Extend this to mark sharpe edges, and define smoothing only for some faces
        """
        assert typ in ('smooth', 'flat')
        poly_smooth = True if typ == 'smooth' else False
        for p in self.bm.polygons:
            p.use_smooth = poly_smooth

    # OBJECT + MESH
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
    
    # MESH + OBJECT
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

    # MESH + OBJECT
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

    # OBJECT + MESH - use setter for swapping
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

    # MESH
    def update_normals(self):
        """Update face normals (for example, when updating the point locations!)"""
        bm = bmesh.new()
        bm.from_mesh(self.bm)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(self.bm)
        bm.clear()
        self.bm.update()
        bm.free()


class Pencil:
    """
    Does a fine job creating a new grease pencil custom object.
    What if I want to make one from an existing grease pencil object?

    Example:
        θ = np.radians(np.arange(0, 360*2+1, 1))
        x1 = θ/2
        z1 = np.sin(θ)
        y1 = np.cos(θ)

        pc1 = PC(np.vstack((x1, y1, z1)).T, trf.normal2tfmat((1, 1, 1)))
        pc2 = PC(np.vstack((x1, y1, z1)).T, trf.normal2tfmat((0, 0, 1)))

        gp = Pencil(gp_name='myGP', obj_name='myGPobj', coll_name='myColl', layer_name='sl1')
        gp.stroke(pc1, color=2, layer='sl1', keyframe=0)
        gp.stroke(pc2, color=1, layer='sl3', keyframe=10)
        gp.stroke(pc1, color=2, layer='sl1', keyframe=20, line_width=100)
        gp.keyframe = 30
    """
    def __init__(self, name=None, **kwargs):
        names, kwargs = utils.clean_names(name, kwargs, {'priority_gp':'new'}, 'gp')
        self.g = new.greasepencil(names['gp_name'])
        self.c = Collection(names['coll_name'])()
        self.o = new.obj(self.g, self.c, names['obj_name'])
        
        kwargs, _ = pn.clean_kwargs(kwargs, {
            'palette_list': ['MATLAB', 'blender_ax'], 
            'palette_prefix': ['MATLAB_', ''], 
            'palette_alpha': [1, 0.8],
            })
        this_palette = {}
        for pal_name, pal_pre, pal_alpha in zip(kwargs['palette_list'], kwargs['palette_prefix'], kwargs['palette_alpha']):
            this_palette = {**this_palette, **utils.color_palette(pal_name, pal_pre, pal_alpha)} # material library for this grease pencil
        for mtrl_name, rgba in this_palette.items(): # create material library
            self.new_color(mtrl_name, rgba)

        self._layer = None
        self._keyframe = None # current keyframe
        self.layer = names['layer_name'] # current layer (also makes a default keyframe at 0!)
        
        self._color = None # name of the current material
        self.color = 0 # initalize to the first one
        self.strokes = {} # easy access to stroke data
    
    @property
    def color_index(self):
        """Index of the current color."""
        return {m.name : i for i, m in enumerate(self.o.material_slots)}[self._color]

    @property
    def color(self):
        """Return the name of the current color."""
        return self._color

    @color.setter
    def color(self, this_color):
        """
        Set the current stroke material (self._color).
        this_color is either a string, a number, a dict, or a tuple.
        string - material name
        number - material index
        tuple - 4-element tuple : select the closest color
        dict - create new material
            one key, value pair {name: 4-tuple rgba}
            if material with that name exists, create a new name
        """
        if isinstance(this_color, int):
            assert this_color < len(self.o.material_slots)
            color_name = {i : m.name for i, m in enumerate(self.o.material_slots)}[this_color]
        if isinstance(this_color, dict):
            assert len(this_color) == 1 # supply only one color at a time?'
            key = list(this_color.keys())[0] # key is the name
            val = list(this_color.values())[0]
            # pick a new name if a material with current name exists
            this_color[utils.new_name(key, [m.name for m in bpy.data.materials])] = this_color.pop(key)
            assert len(val) == 4
            for v in val:
                assert 0.0 <= v <= 1.0
            self.new_color(key, val)
            color_name = key # convert it into a number 
        if isinstance(this_color, str):
            assert this_color in [m.name for m in self.o.material_slots]
            color_name = this_color

        self._color = color_name

    @property
    def layer(self):
        """Returns the current layer."""
        return self._layer
    
    @layer.setter
    def layer(self, layer_name):
        """
        Returns a reference to an existing layer.
        Creates a layer if it doesn't exist.
        """
        if layer_name in [l.info for l in self.g.layers]:
            self._layer = self.g.layers[layer_name]
        else:
            self._layer = self.g.layers.new(layer_name)
            self.keyframe = 0 # make a default keyframe at 0 with every new layer

    @property
    def keyframe(self):
        """Returns the current keyframe."""
        return self._keyframe
    
    @keyframe.setter
    def keyframe(self, keynum):
        """
        Returns reference to the keyframe given by keynum for the
        current layer.
        Inserts a keyframe in the current layer if there isn't one.
        """
        assert isinstance(keynum, int)
        if keynum not in [kf.frame_number for kf in self.layer.frames]:
            self._layer.frames.new(keynum)
        self._keyframe = [kf for kf in self.layer.frames if kf.frame_number == keynum][0]

    def new_color(self, mtrl_name, rgba):
        """
        Add a new color to the current object's material slot.
        Create the material if it doesn't exist.
        Update the rgba if material with mtrl_name already exists.
        Add it to the material slot of the current object.
        Returns:
            Material object (bpy.data.materials)
        """
        if mtrl_name in [m.name for m in bpy.data.materials]:
            mtrl = bpy.data.materials[mtrl_name]
        else:
            mtrl = bpy.data.materials.new(mtrl_name)
        bpy.data.materials.create_gpencil_data(mtrl)
        mtrl.grease_pencil.color = rgba
        if mtrl_name not in [m.name for m in self.g.materials if m is not None]:
            self.g.materials.append(mtrl)
        return mtrl
    
    def stroke(self, ptcloud, **kwargs):
        """
        Make a new stroke 
            1) in the current layer, 
            2) at the current keyframe,
            3) in the current color.
        Allow settings for color, layer, keyframe 
        (which change the current settings)
        Add pressure and strength arrays
        """
        kwargs, _ = pn.clean_kwargs(kwargs, {
            'pressure': 1.0, 
            'strength': 1.0, 
            'line_width': 40, 
            'layer': None, # defaults to layer in self._layer
            'color': None, # defaults to current color self._color
            'keyframe': None, # defaults to self._keyframe
            'display_mode': '3DSPACE',
            'name': 'stroke'
            })

        # set where, when and color
        if kwargs['layer'] is not None:
            self.layer = kwargs['layer']
        if kwargs['keyframe'] is not None:
            self.keyframe = kwargs['keyframe']
        if kwargs['color'] is not None:
            self.color = kwargs['color']

        assert type(ptcloud).__name__ == 'PointCloud'
        gp_stroke = self.keyframe.strokes.new()
        kwargs['name'] = utils.new_name(kwargs['name'], list(self.strokes.keys()))
        gp_stroke.display_mode = kwargs['display_mode']

        gp_stroke.points.add(count=ptcloud.n)
        gp_stroke.points.foreach_set('co', tuple(ptcloud.in_world().co.flatten())) # more efficient
        gp_stroke.material_index = self.color_index
        gp_stroke.line_width = kwargs['line_width']
        n_pts = len(gp_stroke.points[:])

        for attr in ('pressure', 'strength'):
            if isinstance(kwargs[attr], (int, float)):
                kwargs[attr] = kwargs[attr]*np.ones(n_pts)
            else:
                assert len(kwargs[attr]) == n_pts
            gp_stroke.points.foreach_set(attr, tuple(kwargs[attr]))
        self.strokes[kwargs['name']] = gp_stroke
        return gp_stroke

        # bpy.data.grease_pencils[0].layers['sl1'].frames[1].clear() # removes the stroke, but there is still a keyframe
        # bpy.data.grease_pencils[0].layers['sl1'].clear() # removes all keyframes and strokes

class Thing:
    """
    Wrapper around blender's bpy.data.*
    args are exclusively meant for the new() method.
    kwargs are attributes of the thing being created.
    Example:
        key_light = core.Thing('Key', 'Light', 'SUN', energy=2.5, angle=0.2, color=(0., 0., 0.))
    """
    def __init__(self, thing_name, thing_type, *args, **kwargs):
        if isinstance(thing_type, str):
            if thing_type[0].lower() == thing_type[0]:
                thing_type = thing_type.title()
            thing_type = getattr(bpy.types, thing_type) # bpy.types.Object
        if isinstance(thing_name, thing_type):
            thing_name = thing_name.name # in case you passed the object itself
        if len(args) >= 1 and isinstance(args[0], Thing):
            args = list(args)
            args[0] = args[0]()
            args = tuple(args)

        self.blend_type = thing_type # bpy.types.Object
        type_name = thing_type.__name__.lower()
        self.blend_coll = getattr(bpy.data, utils.plural(type_name)) # bpy.data.objects, bpy.data.meshes
        self.blend_name = thing_name
        self.created = False
        # if it is not in the collection, create a new one
        if thing_name not in [t.name for t in self.blend_coll]:
            self.blend_coll.new(thing_name, *args)
            self.created = True
        
        for key, val in kwargs.items():
            setattr(self(), key, val)

    def __call__(self):
        """Return the blender object."""
        return self.blend_coll[self.blend_name]
    
    def __neg__(self):
        """Remove that object."""
        self.blend_coll.remove(self())
    
    @property
    def name(self):
        """Return the name in blender. It is important to set the name through this setter for chaning names."""
        return self.blend_name
    
    @name.setter
    def name(self, new_name):
        self().name = new_name
        self.blend_name = new_name

class Collection(Thing):
    """Wrapper around a bpy.types.Collection thing"""
    def __init__(self, name):
        super().__init__(name, 'Collection')
        if self.created:
            bpy.context.scene.collection.children.link(self())
    
    def hide(self):
        """Hide collection from the viewport, and from rendering."""
        bpy.context.scene.view_layers[0].layer_collection.children[self.name].hide_viewport = True
        bpy.context.scene.view_layers[0].layer_collection.children[self.name].exclude = True
    
    def show(self):
        """Show collection in the viewport, and enable rendering."""
        bpy.context.scene.view_layers[0].layer_collection.children[self.name].hide_viewport = False
        bpy.context.scene.view_layers[0].layer_collection.children[self.name].exclude = False
    
    # Group transformations for objects in a collection!

class Object(Thing):
    """
    Wrapper around a bpy.types.Object thing
    args is for new
    kwargs is to set options
    Object('empty_obj', None)
    """
    def __init__(self, name, *args, **kwargs):
        super().__init__(name, 'Object', *args)
        self.frame_orig = self.frame
        kwargs, kwargs_blobject = pn.clean_kwargs(kwargs, {'coll_name': 'Collection'})
        if not self().users_collection:
            col = Collection(kwargs['coll_name'])
            col().objects.link(self())

        # set blender object attributes useful for initialization
        for key, val in kwargs_blobject.items():
            setattr(self(), key, val)

        self.container = self().parent.name if self().parent else None

        all_constraints = ('CAMERA_SOLVER', 'FOLLOW_TRACK', 'OBJECT_SOLVER', 'COPY_LOCATION', 'COPY_ROTATION', 'COPY_SCALE', 'COPY_TRANSFORMS', 'LIMIT_DISTANCE', 'LIMIT_LOCATION', 'LIMIT_ROTATION', 'LIMIT_SCALE', 'MAINTAIN_VOLUME', 'TRANSFORM', 'TRANSFORM_CACHE', 'CLAMP_TO', 'DAMPED_TRACK', 'IK', 'LOCKED_TRACK', 'SPLINE_IK', 'STRETCH_TO', 'TRACK_TO', 'ACTION', 'ARMATURE', 'CHILD_OF', 'FLOOR', 'FOLLOW_PATH', 'PIVOT', 'SHRINKWRAP')
        self.constraint_list = {cn.lower() : None for cn in all_constraints}
        for con in self().constraints[:]: # if they are already there, then add them to the name list
            self.constraint_list[con.type.lower()] = con.name
        
        all_modifiers = ('DATA_TRANSFER', 'MESH_CACHE', 'MESH_SEQUENCE_CACHE', 'NORMAL_EDIT', 'WEIGHTED_NORMAL', 'UV_PROJECT', 'UV_WARP', 'VERTEX_WEIGHT_EDIT', 'VERTEX_WEIGHT_MIX', 'VERTEX_WEIGHT_PROXIMITY', 'ARRAY', 'BEVEL', 'BOOLEAN', 'BUILD', 'DECIMATE', 'EDGE_SPLIT', 'MASK', 'MIRROR', 'MULTIRES', 'REMESH', 'SCREW', 'SKIN', 'SOLIDIFY', 'SUBSURF', 'TRIANGULATE', 'WELD', 'WIREFRAME', 'ARMATURE', 'CAST', 'CURVE', 'DISPLACE', 'HOOK', 'LAPLACIANDEFORM', 'LATTICE', 'MESH_DEFORM', 'SHRINKWRAP', 'SIMPLE_DEFORM', 'SMOOTH', 'CORRECTIVE_SMOOTH', 'LAPLACIANSMOOTH', 'SURFACE_DEFORM', 'WARP', 'WAVE', 'CLOTH', 'COLLISION', 'DYNAMIC_PAINT', 'EXPLODE', 'FLUID', 'OCEAN', 'PARTICLE_INSTANCE', 'PARTICLE_SYSTEM', 'SOFT_BODY', 'SURFACE')
        self.modifier_list = {mod.lower() : None for mod in all_modifiers}
        for mod in self().modifiers[:]: # if they are already there, then add them to the modifier list
            self.modifier_list[mod.type.lower()] = mod.name

    @property
    def frame(self):
        """Object frame expressed as trf.CoordFrame"""
        return trf.CoordFrame(self().matrix_world, unit_vectors=False)
    
    @frame.setter
    def frame(self, new_frame):
        self().matrix_world = new_frame.m if type(new_frame).__name__ == 'CoordFrame' else new_frame
        bpy.context.view_layer.update()

    def frame_reset(self):
        """Reset matrix_world to what it was when created."""
        self.frame = self.frame_orig

    @property
    def normal(self):
        """By definition, normal is the z-direction."""
        return self.frame.k

    @normal.setter
    def normal(self, new_normal):
        new_normal = np.array(new_normal)
        assert len(new_normal) == 3
        tfmat = trf.m4(trf.normal2tfmat(new_normal))
        self.frame = self.frame_orig.transform(tfmat)
        bpy.context.view_layer.update()

    # transformations
    @property
    def loc(self):
        """Object location (not mesh!)"""
        return self().location
    @loc.setter
    def loc(self, new_loc):
        assert len(new_loc) == 3
        self().location = mathutils.Vector(new_loc)
        bpy.context.view_layer.update()

    @property
    def rot(self):
        """Object rotation"""
        return self().rotation_euler
    @rot.setter
    def rot(self, theta):
        self().rotation_euler.x = theta[0]
        self().rotation_euler.y = theta[1]
        self().rotation_euler.z = theta[2]
        bpy.context.view_layer.update()

    @property
    def scl(self):
        """Object scale"""
        return self().scale
    @scl.setter
    def scl(self, s):
        if isinstance(s, (int, float)):
            s = np.array([1, 1, 1])*s
        else:
            assert np.size(s) == 3
            self().scale = mathutils.Vector(s)
        bpy.context.view_layer.update()

        self().scale = mathutils.Vector(s)
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
        self().location = self().location + mathutils.Vector(delta)
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
            self().rotation_euler.x = self().rotation_euler.x + theta[0]
            self().rotation_euler.y = self().rotation_euler.y + theta[1]
            self().rotation_euler.z = self().rotation_euler.z + theta[2]
        else: #frame = global
            self().rotation_euler.rotate(mathutils.Euler(tuple(theta)))
        bpy.context.view_layer.update()
        return self

    def scale(self, delta):
        """
        Scale an object.
        delta is a 3-element tuple, list, numpy array or Vector
        """
        if isinstance(delta, (int, float)):
            self().scale = self().scale*float(delta)
        else:
            assert np.size(delta) == 3
            self().scale = mathutils.Vector(np.array(delta)*np.array(self().scale))
        bpy.context.view_layer.update()
        return self

    # animation
    def hide(self, keyframe=None):
        """Hide object at keyframe."""
        if keyframe is None:
            keyframe = bpy.context.scene.frame_current
        self().hide_render = True
        self().keyframe_insert('hide_render', frame=keyframe)
        self().hide_viewport = True
        self().keyframe_insert('hide_viewport', frame=keyframe)
    
    def show(self, keyframe=None):
        """Show object at keyframe."""
        if keyframe is None:
            keyframe = bpy.context.scene.frame_current
        self().hide_render = False
        self().keyframe_insert('hide_render', frame=keyframe)
        self().hide_viewport = False
        self().keyframe_insert('hide_viewport', frame=keyframe)
    
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

        if values is None:
            values = [tuple(getattr(self(), attr)) for attr in attrs]
            # for some reason, s.key() doesn't take current values if I don't use tuple
        
        frame_current = bpy.context.scene.frame_current
        if not frame:
            frame = frame_current
        bpy.context.scene.frame_set(frame)
        for attr, value in zip(attrs, values):
            setattr(self(), attr, value)
            self().keyframe_insert(data_path=attr, frame=frame)
        # bpy.context.scene.frame_set(frame_current)

        return self # so you can chain keyings into one command
    
    # parenting
    def add_container(self, container_name=None, typ='CUBE', size=0.25):
        """
        Add a container (parent object).
        By default, set container_name to <obj_name>+'_container'
        """
        if container_name is None:
            container_name = self.name+'_container'
        self.container = new.empty(container_name, typ, size=size, coll_name=self().users_collection[0].name)
        self().parent = self.container() # container is a core.Object
    
    @property
    def coll(self):
        """
        Collection of the object.
        If the object is in multiple collections, return the last one
        """
        this_coll = self().users_collection
        assert this_coll # make sure there is at least one element
        return Collection(this_coll[-1].name)

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
        oldC = self.coll
        if not isinstance(coll_name, str):
            coll_name = coll_name.name
        newC = Collection(coll_name)
        if coll_name not in [c.name for c in self().users_collection]: # link only if the object isn't in collection already
            newC().objects.link(self())
            if typ == 'move':
                oldC().objects.unlink(self())
    
    # modifiers
    def get_modifier(self, modifier_type):
        """Returns bpy.types.Modifier, or makes a new one if a modifier does not exist."""
        if self.modifier_list[modifier_type.lower()] is not None:
            return self().modifiers[self.modifier_list[modifier_type.lower()]]
        modifier_name = modifier_type.lower().replace('_', ' ').title()
        return self().modifiers.new(modifier_name, modifier_type.upper())

    def subsurf(self, levels=2, render_levels=3, **kwargs):
        """Subdivision surface modifier."""
        # get a subsurf modifier if it already exists
        subsurf_modifier = self.get_modifier('subsurf')
        
        # update important attributes
        subsurf_modifier.levels = levels
        subsurf_modifier.render_levels = render_levels

        # update optional attributes
            # kwargs_other: if you didn't specify, don't change
            # kwargs_impose: if you didn't specify, impose a certain value
        kwargs_impose, kwargs_keep = pn.clean_kwargs(kwargs, {
            'subdivision_type' : 'CATMULL_CLARK' #('CATMULL_CLARK', 'SIMPLE')
        })
        for key, val in {**kwargs_impose, **kwargs_keep}.items():
            setattr(subsurf_modifier, key, val)

        # update modifier list
        self.modifier_list['subsurf'] = subsurf_modifier.name

    # constraints
    def get_constraint(self, constraint_type):
        """Returns the bpy.types.Constraint, or makes a new one if a constraint doesn't exist."""
        if self.constraint_list[constraint_type.lower()] is not None:
            return self().constratints[self.constraint_list[constraint_type.lower()]]
        return self().constraints.new(constraint_type.upper())

    def follow_path(self, path_obj=None, **kwargs):
        """
        Add a FOLLOW PATH constraint to parametrically control object flow.
        obj.follow_path(r=3) to add a bezier circle path constraint
        obj.follow_path(functools.partial(new.bezier, r=3)) also does the same.
        Give any function or partial that returs a bpy.types.Object of type CURVE, OR its wrapper, core.Object
        """
        if path_obj is None:
            path_obj = functools.partial(new.bezier_circle, r=kwargs['r'] if 'r' in kwargs else 2)
        if isinstance(path_obj, functools.partial) or type(path_obj).__name__ == 'function': # give a function or a partial function that returns a core.Object or a bpy.types.Object of type CURVE
            path_obj = path_obj(curve_name=self.name+'Path', obj_name=self.name+'_path', coll_name=self().users_collection[0].name)
        if isinstance(path_obj, Thing):
            path_obj = path_obj()
        assert isinstance(path_obj, bpy.types.Object)
        assert path_obj.type == 'CURVE'

        path_constraint = self.get_constraint('follow_path')
        path_constraint.target = path_obj
        kwargs, _ = pn.clean_kwargs(kwargs, {
            'use_curve_follow': True,
            'use_curve_radius': False,
            'use_fixed_location': True,
            'up_axis': 'UP_Z', # ('UP_X', 'UP_Y', 'UP_Z')
            'forward_axis': 'FORWARD_Y', # ('FORWARD_X', 'FORWARD_Y', 'FORWARD_Z', 'TRACK_NEGATIVE_X', 'TRACK_NEGATIVE_Y', 'TRACK_NEGATIVE_Z')
        })
        for key, val in kwargs.items():
            setattr(path_constraint, key, val)
        self.constraint_list['follow_path'] = path_constraint.name
    
    def track_to(self, targ_obj, **kwargs):
        """
        Add a TRACK TO constraint
        """
        if isinstance(targ_obj, Thing):
            targ_obj = targ_obj()
        assert isinstance(targ_obj, bpy.types.Object)

        track_constraint = self.get_constraint('track_to')
        track_constraint.target = targ_obj
        kwargs, _ = pn.clean_kwargs(kwargs, {
            'up_axis': 'UP_Y', # ('UP_X', 'UP_Y', 'UP_Z')
            'track_axis': 'TRACK_NEGATIVE_Z', # ('TRACK_X', 'TRACK_Y', 'TRACK_Z', 'TRACK_NEGATIVE_X', 'TRACK_NEGATIVE_Y', 'TRACK_NEGATIVE_Z')
        })
        for key, val in kwargs.items():
            setattr(track_constraint, key, val)
    
    def copy(self, obj_name=None, coll_name=None):
        """
        Make a copy of the object, keep the same mesh and put it in the same collection.
        Use the same animation data!
        """
        this_o = self().copy()
        if isinstance(obj_name, str):
            this_o.name = obj_name
        if isinstance(coll_name, str):
            Collection(coll_name)().objects.link(this_o)
        else:
            self.coll().objects.link(this_o)
        return utils.get(this_o.name) # use the dispatcher!

    def deepcopy(self, obj_name=None, coll_name=None, msh_name=None):
        """
        Make a copy of everything - object, mesh and animation
        """
        this_o = self().copy()
        this_o.data = this_o.data.copy()
        if isinstance(obj_name, str):
            this_o.name = obj_name
        if isinstance(coll_name, str):
            Collection(coll_name)().objects.link(this_o)
        else:
            self.coll().objects.link(this_o)
        if isinstance(msh_name, str):
            this_o.data.name = msh_name
        return utils.get(this_o.name)


class Mesh(Thing):
    """Wrapper around a bpy.types.Mesh object."""
    def __init__(self, name):
        super().__init__(name, 'Mesh')
        self.v_init = copy.deepcopy(self.v)
        self.v_bkp = copy.deepcopy(self.v)
    
    @property
    def v(self):
        """Coordinates of a mesh as an nVx3 numpy array."""
        return np.array([v.co for v in self().vertices])
    
    @v.setter
    def v(self, thisCoords):
        """
        Set vertex positions of a mesh using a numpy array of size nVertices x 3.
        Note that this will only work when blender 3D viewport is in object mode.
        Therefore, this code will temporarily change the 3D viewport mode to Object,
        change the mesh coordinates and switch it back.
        """
        self.v_bkp = copy.deepcopy(self.v) # for undo
        for vertexCount, vertex in enumerate(self().vertices):
            vertex.co = mathutils.Vector(thisCoords[vertexCount, :])
        bpy.context.view_layer.update()
    
    @property
    def center(self):
        """Return mesh center"""
        return np.mean(self.v, axis=0)

    @center.setter
    def center(self, new_center):
        self.v = self.v + new_center - self.center

    @property
    def vn(self):
        """Vertex normals as an nVx3 numpy array."""
        return np.array([vert.normal[:] for vert in self().vertices])
    
    @property
    def f(self):
        """Faces as an nFx3 numpy array."""
        return np.array([polygon.vertices[:] for polygon in self().polygons])

    @property
    def fn(self):
        """Face normals as an nFx3 numpy array."""
        return np.array([polygon.normal[:] for polygon in self().polygons])
        
    @property
    def fa(self):
        """Area of faces as an nFx3 numpy array."""
        return np.array([polygon.area for polygon in self().polygons])
    
    @property
    def fc(self):
        """Coordinates of face centers."""
        return np.array([polygon.center for polygon in self().polygons])

    @property
    def e(self):
        """Vertex indices of edges."""
        return np.array([edge.vertices[:] for edge in self().edges])

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

    def dummy(self, inp=2):
        print(self.__class__)
        print(inp)

@pn.PortProperties(Mesh, 'data') # instance of MeshObject MUST have 'data' attribute/property
class MeshObject(Object):
    """
    This is an object. Automatically calls the appropriate methods and
    properties from Object and Mesh classes.
    For example:
        new.sphere('sph')
        s = MeshObject('sph')
        s.v -> automatically returns vertices from them mesh
    """
    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        assert self().type == 'MESH'
        self._data = Mesh(self().data) # self() returns bpy.data.objects[obj_name] and self().data acts on that blender object

    @property
    def data(self):
        """Mesh data. Initalized at the time of object creation."""
        return self._data

    @data.setter
    def data(self, new_data):
        if not isinstance(new_data, str):
            assert hasattr(new_data, 'name')
            new_data = new_data.name
        self._data = Mesh(new_data)
        self().data = self.data() # replace the blender data
        bpy.context.view_layer.update()

    @property
    def pts(self):
        """Return vertices as a trf.PointCloud object."""
        return trf.PointCloud(self.v, self.frame)

    @pts.setter
    def pts(self, new_pts):
        """
        Set the vertices AND the frame. In other words, transform the
        point cloud into the desired frame of reference before putting
        it here.
        """
        assert type(new_pts).__name__ == 'PointCloud'
        self.v = new_pts.co
        self.frame = new_pts.frame

# MeshObject = utils.port_properties(Mesh, MeshObject, 'data')
