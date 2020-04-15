"""
Creation submodule for bpn.
Everything here should return instances of core classes.
"""
import os
import types
from functools import partial
import numpy as np

import pntools as pn

import bpy #pylint: disable=import-error
import bmesh #pylint: disable=import-error
import mathutils #pylint: disable=import-error

from . import vef, utils, core, turtle, trf, io

def empty(name=None, typ='PLAIN_AXES', size=0.25, coll_name='Collection'):
    """
    Create a new empty. Convenience wrapper for initalizing core.Object
    # typ ('PLAIN_AXES', 'ARROWS', 'SINGLE_ARROW', 'CIRCLE', 'CUBE', 'SPHERE', 'CONE', 'IMAGE')
    returns: core.Object
    """
    if name is None:
        name = utils.new_name('empty', [o.name for o in bpy.data.objects])
    s = core.Object(name, None, empty_display_type=typ, empty_display_size=size)
    s.to_coll(coll_name)
    return s

def greasepencil(gp_name='newGP'):
    """
    Creates a new blender grease pencil.
    Returns a reference to existing grease pencil if it already exists.
    """
    if gp_name in [g.name for g in bpy.data.grease_pencils]:
        return bpy.data.grease_pencils[gp_name]
    return bpy.data.grease_pencils.new(gp_name)

def obj(msh, col, obj_name='newObj'):
    """
    Creates an object with obj_name if it does not exist.
    If object with name exists, returns object.

    :param msh: (str, bpy.types.Mesh) mesh from blender
    :param col: (str, bpy.types.Collection) collection from blender
    
    DOES NOT: change collection of the object if col is different from the object's collection
    """
    if isinstance(msh, str):
        msh = bpy.data.meshes[msh]
    if isinstance(col, str):
        col = core.Collection(col)()

    if obj_name in [o.name for o in bpy.data.objects]:
        o = bpy.data.objects[obj_name]
    else:
        o = bpy.data.objects.new(obj_name, msh)
        col.objects.link(o)
    return o

def mesh(name=None, **kwargs): # formerly bpn.Msh
    """
    Create a mesh object from various types of input
    Returns core.MeshObject

    :param name: name='thing' (str) both the mesh and the object will receive this name
            name will get overwritten by msh_name or obj_name if present
    :param kwargs: (create mesh from vertices and faces, 2d array, or function)
        msh_name='new_mesh'  
            (str) name of the mesh loaded in blender
            (str) name of an object loaded in blender (get the associated mesh)
            (bpy.types.Mesh) the bpy mesh object
        obj_name='new_obj' (str) name of the object to assign the mesh
        coll_name='new_coll' (str) name of the collection to locate the object / to place the created object        
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
    
    Broadly, using this function, core.MeshObjects can be created from:
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
    Examples:
        # make a mesh from python data
        new.mesh(name=name, v=vertices, f=faces)
        new.mesh(v=v1, f=f1)
        new.mesh(v=v1, e=e1)
        new.mesh(v=v1, e=e1, f=f1)

        # make a mesh from an STL file
        new.mesh(stl=stlfile)
        new.mesh(stl=stlfile, name='awesome') # mesh and object get the same name
        new.mesh(stl=stlfile, coll_name='myColl') # put msh in a collection coll_name
        new.mesh(stlfile, name='awesome', msh_name='awesomeMesh', coll_name='myColl')
        new.mesh(stlfile, msh_name='awesomeMesh', obj_name='awesomeObj', coll_name='myColl')

        # get a mesh from the blender environment
        new.mesh(name=blender mesh name)
        new.mesh(name=blender obj name)
        new.mesh(name=blender mesh object) # works, but not recommended

        # make a mesh from a 2d function
        new.mesh(xyfun=lambda x, y: x*x+y*y, name='parabola')
    """
    def _make_mesh(msh_name, kwargs):
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
        return msh # blender mesh

    names, kwargs = utils.clean_names(name, kwargs, {'priority_msh': 'current', 'priority_obj': 'current'}, mode='msh')
    msh_name = names['msh_name']
    obj_name = names['obj_name']
    coll_name = names['coll_name']
    if 'stl' in kwargs:
        stlfile = kwargs['stl']
        assert os.path.isfile(stlfile)
        s = core.MeshObject(io.loadSTL([stlfile])['objects'][0])
        s.name = obj_name
        s.data.name = msh_name
        s.to_coll(coll_name)
        return s

    # if obj_name exists, use object and corresponding mesh
    if obj_name in [o.name for o in bpy.data.objects]:
        s = core.MeshObject(obj_name)
        s.to_coll(coll_name)
        return s

    # if mesh exists, assign it to the object, and put it in collection
    if msh_name in [m.name for m in bpy.data.meshes]:
        s = core.MeshObject(obj_name, bpy.data.meshes[msh_name])
        s.to_coll(coll_name)
        return s

    # if mesh doesn't exist, make it, make object, and put it in the collection
    s = core.MeshObject(obj_name, _make_mesh(msh_name, kwargs))
    s.to_coll(coll_name)
    return s

def pencil(name=None, **kwargs):
    """
    Create a new grease pencil object.
    """
    names, kwargs = utils.clean_names(name, kwargs, {'layer_name':'main', 'priority_gp': 'current', 'priority_obj': 'current'}, mode='gp')
    gp_name = names['gp_name']
    obj_name = names['obj_name']
    coll_name = names['coll_name']
    layer_name = names['layer_name']

    s = core.GreasePencilObject(obj_name, core.GreasePencil(gp_name)())
    # if grease pencil doesn't exist, make it
    gp = s.data
    # create a layer (which also inserts a keyframe at 0)
    gp.layer = layer_name

    # set up the colors for grease_pencil drawing
    kwargs, _ = pn.clean_kwargs(kwargs, {
        'palette_list': ['MATLAB', 'blender_ax'], 
        'palette_prefix': ['MATLAB_', ''], 
        'palette_alpha': [1, 0.8],
        })
    this_palette = {}
    for pal_name, pal_pre, pal_alpha in zip(kwargs['palette_list'], kwargs['palette_prefix'], kwargs['palette_alpha']):
        this_palette = {**this_palette, **utils.color_palette(pal_name, pal_pre, pal_alpha)} # material library for this grease pencil
    for mtrl_name, rgba in this_palette.items(): # create material library
        gp.new_color(mtrl_name, rgba)

    s.color = 0
    s.to_coll(coll_name)
    return s


# easy object creation
def easycreate(mshfunc, name=None, **kwargs):
    """
    **kwargs : u=16, v=8, r=0.5 for uv sphere
    **kwargs : size=0.5 for uv cube

    Warning: Avoid empty creates such as new.sphere()!
    """
    names, kwargs = utils.clean_names(name, kwargs, {'priority_obj':'new', 'priority_msh':'current'})

    # input control
    if str(mshfunc) == str(bmesh.ops.create_uvsphere):
        kwargs_def = {'u_segments':16, 'v_segments':8, 'diameter':0.5}
        kwargs_alias = {'u_segments': ['u', 'u_segments'], 'v_segments': ['v', 'v_segments'], 'diameter': ['r', 'diameter']}
        kwargs, _ = pn.clean_kwargs(kwargs, kwargs_def, kwargs_alias)

    if str(mshfunc) == str(bmesh.ops.create_cube):
        kwargs_def = {'size':1}
        kwargs_alias = {'size': ['size', 'sz', 's', 'r']}
        kwargs, _ = pn.clean_kwargs(kwargs, kwargs_def, kwargs_alias)
    
    if str(mshfunc) == str(bmesh.ops.create_cone):
        kwargs_def = {'segments':12, 'diameter1':2, 'diameter2':0, 'depth':3, 'cap_ends':True, 'cap_tris':False}
        kwargs_alias = {'segments':['segments', 'seg', 'u', 'n'], 'diameter1':['diameter1', 'r1', 'r'], 'diameter2':['diameter2', 'r2'], 'depth':['depth', 'd', 'h'], 'cap_ends':['cap_ends', 'fill'], 'cap_tris':['cap_tris', 'fill_tri']}
        kwargs, _ = pn.clean_kwargs(kwargs, kwargs_def, kwargs_alias)

    if str(mshfunc) == str(bmesh.ops.create_circle):
        kwargs_def = {'segments':32, 'radius':1, 'cap_ends':False, 'cap_tris':False}
        kwargs_alias = {'segments':['segments', 'seg', 'u', 'n'], 'radius':['radius', 'r'], 'cap_ends':['cap_ends', 'fill'], 'cap_tris':['cap_tris', 'fill_tri']}
        kwargs, _ = pn.clean_kwargs(kwargs, kwargs_def, kwargs_alias)

    if str(mshfunc) == str(bmesh.ops.create_monkey):
        kwargs = {}

    if names['msh_name'] in [m.name for m in bpy.data.meshes]:
        msh = bpy.data.meshes[names['msh_name']]
    else:
        msh = bpy.data.meshes.new(names['msh_name'])
        bm = bmesh.new()
        mshfunc(bm, **kwargs)
        bm.to_mesh(msh)
        bm.free()
        msh.update()
    return mesh(msh_name=msh.name, obj_name=names['obj_name'], coll_name=names['coll_name'], pargs=kwargs)

sphere = partial(easycreate, bmesh.ops.create_uvsphere)
monkey = partial(easycreate, bmesh.ops.create_monkey)
cube = partial(easycreate, bmesh.ops.create_cube)
cone = partial(easycreate, bmesh.ops.create_cone)
polygon = partial(cone, **{'d':0, 'cap_ends':False, 'cap_tris':False, 'r1':2.2, 'r2':1.8})

def ngon(name=None, **kwargs):
    """Create a new n-sided polygon with one face inscribed in a circle of radius r."""
    kwargs_def = {'n':6, 'r':1, 'theta_offset_deg':'auto', 'fill':True}
    kwargs_alias = {'n':['segments', 'seg', 'u', 'n'], 'r':['radius', 'r'], 'theta_offset_deg':['theta_offset_deg', 'th', 'offset', 'th_off_deg'], 'fill':['fill']}
    kwargs_fun, kwargs_msh = pn.clean_kwargs(kwargs, kwargs_def, kwargs_alias)
    
    v, e, f = vef.ngon(n=kwargs_fun['n'], r=kwargs_fun['r'], th_off_deg=kwargs_fun['theta_offset_deg'])
    if not kwargs_fun['fill']:
        f = []

    return mesh(name, v=v, e=e, f=f, **kwargs_msh)

plane = partial(ngon, **{'n':4, 'r':2/np.sqrt(2), 'theta_offset_deg':45})

# No faces, just edges - redundant now, just use ngon
circle = partial(easycreate, bmesh.ops.create_circle)

# other primitives:
# cylinder, grid, ico_sphere, torus

def torus(name=None, **kwargs):
    """
    Make a torus in the x-y plane
    torus('mytorus', u=6, v=32, r=1, t=0.3)
        u = number of subdivisions in a saggital section (small circle)
        v = number of subdivisions in the horizontal section (big circle)
        r = radius of the doughnut
        t = thickness (radius)
        th = degrees to rotate the small circle
    """
    names, kwargs = utils.clean_names(name, kwargs, {'msh_name':'torus', 'obj_name':'torus', 'priority_msh':'current', 'priority_obj':'new'})

    kwargs_def = {'n_u':16, 'r_u':0.3, 'n_v':32, 'r_v':1, 'theta_offset_deg':'auto'}
    kwargs_alias = {'n_u':['n_u', 'u'], 'r_u':['r_u', 't', 'thickness'], 'n_v':['n_v', 'v'], 'r_v':['r_v', 'r'], 'theta_offset_deg':['theta_offset_deg', 'th', 'offset', 'th_off_deg', 'th_u']}
    kwargs, _ = pn.clean_kwargs(kwargs, kwargs_def, kwargs_alias)
    
    a = turtle.Draw(**names)
    start = a.ngon(n=kwargs['n_u'], r=kwargs['r_u'], th_off_deg=kwargs['theta_offset_deg'])
    bmesh.ops.rotate(a.bm, verts=start.v, cent=(0, 0, 0), matrix=mathutils.Matrix.Rotation(np.radians(90.0), 3, 'Y'))
    for vert in start.v:
        vert.co += mathutils.Vector((0., -kwargs['r_v'], 0.))
    end = a.spin(angle=2*np.pi-2*np.pi/kwargs['n_v'], steps=kwargs['n_v']-1, axis='z', cent=(0., 0., 0.))
    a.join(start.e + end.e)
    tor = +a
    return tor

# bezier curves
def bezier_circle(name=None, **kwargs):
    """
    Bezier circle of radius r.
    Returns core.Object
    """
    names, kwargs = utils.clean_names(name, kwargs, {'curve_name':'Bezier', 'obj_name':'bezier', 'priority_curve':'current', 'priority_obj':'new'}, 'curve')
    kwargs, _ = pn.clean_kwargs(kwargs, {'r':1, 'h':None})
    r = kwargs['r']
    h = kwargs['h']
    if h is None:
        h = r*(np.sqrt(2)/2 - 4*(0.5**3))/(3*(0.5**3)) # handle length for cubic bezier approx. of a circle

    col = core.Collection(names['coll_name'])()
    path = bpy.data.curves.new(names['curve_name'], 'CURVE')
    path_obj = bpy.data.objects.new(names['obj_name'], path)
    col.objects.link(path_obj)

    spl = path.splines.new(type='BEZIER')
    spl.bezier_points.add(3)
    spl.bezier_points[0].co = (-r, 0, 0)
    spl.bezier_points[1].co = (0, r, 0)
    spl.bezier_points[2].co = (r, 0, 0)
    spl.bezier_points[3].co = (0, -r, 0)

    spl.bezier_points[0].handle_right = (-r, h, 0)
    spl.bezier_points[0].handle_left = (-r, -h, 0)

    spl.bezier_points[1].handle_right = (h, r, 0)
    spl.bezier_points[1].handle_left = (-h, r, 0)

    spl.bezier_points[2].handle_right = (r, -h, 0)
    spl.bezier_points[2].handle_left = (r, h, 0)

    spl.bezier_points[3].handle_right = (-h, -r, 0)
    spl.bezier_points[3].handle_left = (h, -r, 0)

    spl.use_cyclic_u = True
    spl.order_u = 4
    spl.order_v = 4
    spl.resolution_u = 12
    spl.resolution_v = 12
    spl.tilt_interpolation = 'LINEAR' #('LINEAR', 'CARDINAL', 'BSPLINE', 'EASE')

    return utils.get(path_obj.name)


# convenience 
def spiral(name=None, n_rot=3, res=10, offset_rot=0, **kwargs):
    """
    Makes a spiral.
    :param n_rot: number of rotations
    :param res: resolution (degrees) between points
    """
    θ = np.radians(np.arange(360*offset_rot, 360*n_rot+res, res))
    x = θ*np.sin(θ)/(np.pi*2)
    y = θ*np.cos(θ)/(np.pi*2)
    z = np.zeros_like(θ)

    return mesh(name, x=x, y=y, z=z, **kwargs)

# Enhanced meshes
class Tube(core.MeshObject):
    """
    Creates a 'Tube' object with a specified number of cross sections
    and vertical sections.
    """
    def __init__(self, name=None, x=0, y=0, z=0, **kwargs):
        names, kwargs = utils.clean_names(name, kwargs, {'msh_name':'tube_msh', 'obj_name':'tube_obj', 'priority_obj':'new', 'priority_msh':'new'})
        kwargs_ngon, _ = pn.clean_kwargs(kwargs, {'n':6, 'r':0.3, 'theta_offset_deg':-1}, {'n':['segments', 'seg', 'u', 'n'], 'r':['radius', 'r'], 'theta_offset_deg':['theta_offset_deg', 'th', 'offset', 'th_off_deg']})
        
        spine = np.array([np.array((tx, ty, tz)) for tx, ty, tz in zip(x, y, z)])
        normals = np.vstack((spine[1, :] - spine[0, :], spine[2:, :] - spine[:-2, :], spine[-1, :] - spine[-2, :]))

        a = turtle.Draw(**names)
        a.skin(spine, **kwargs_ngon)
        a_exp = a.export()
        this_obj = +a
        super().__init__(this_obj.name, this_obj.data)

        self.xsec = self.XSec(self, normals, a_exp)

    class XSec:
        """Cross sections of a tube: a collection of DirectedSubMsh's"""
        def __init__(self, parent, normals, draw_export):
            self.all = [turtle.DirectedSubMsh(parent, normals[i, :], **s) for i, s in enumerate(draw_export)]
            self._normals = normals

        @property
        def n(self):
            """Number of cross sections."""
            return len(self.all)

        @property
        def centers(self):
            """The 'spine' of the tube. nCrossSections X 3 numpy array."""
            return np.array([x.origin for x in self.all])
        
        @centers.setter
        def centers(self, new_centers):
            new_centers = np.array(new_centers)
            assert np.shape(new_centers) == (self.n, 3)
            for i in range(self.n):
                self.all[i].origin = trf.PointCloud(new_centers[i, :], np.eye(4))

        def update_normals(self):
            """Update normals based on the location of the centers."""
            spine = self.centers
            self.normals = np.vstack((spine[1, :] - spine[0, :], spine[2:, :] - spine[:-2, :], spine[-1, :] - spine[-2, :]))

        @property
        def normals(self):
            """
            Normals of each x-section.
            Returns direction in world
            """
            return np.array([self.all[i].normal for i in range(self.n)])

        @normals.setter
        def normals(self, new_normal_dir):
            """
            Directions are origin-agnostic.
            """
            new_normal_dir = np.array(new_normal_dir)
            assert np.shape(new_normal_dir) == (self.n, 3)
            for i in range(np.shape(new_normal_dir)[0]):
                self.all[i].normal = trf.PointCloud(new_normal_dir[i, :]+self.all[i].origin, np.eye(4))

class Text(core.Object):
    """
    Convert a LaTeX expression into an svg and import that into blender.
    :param expr: (str) latex string to be converted into text.
    :param name: (str) defaults to 'new_text.00n'
    Possible keyword arguments:
        Set by text:
            FUTURE - Option to add packages to the tex document?
            FUTURE - Option to use an existing tex document
        Set by utils.clean_names:
            'curve_name' : 'new_curve', 
            'obj_name' : 'new_obj',
            'coll_name': 'Collection',
            'priority_obj': 'new',
            'priority_curve': 'new',
        Set by io.loadSVG:
            'remove_default_coll': True,
            'scale': (100, 100, 100), # svg imports are really small
            'color': (1.0, 1.0, 1.0, 1.0), # rgba
            'combine_curves': True, # this may not work!!
            'halign' : 'center', # 'center', 'left', 'right', None
            'valign' : 'middle', # 'top', 'middle', 'bottom', None
    """
    def __init__(self, expr, name=None, **kwargs):
        if name is None:
            name = utils.new_name('new_text', [o.name for o in bpy.data.objects])
        kwargs_names, _ = utils.clean_names(name, kwargs, {'priority_curve': 'new'}, mode='curve')
        def write_tex_file(fname):
            try:
                f = open(fname, 'w')
                f.write(r"\documentclass{standalone}" + "\n")
                f.write(r"\usepackage{amsthm, amssymb, amsfonts, amsmath}" + "\n")
                f.write(r"\begin{document}" + "\n")
                f.write(expr + "\n")
                f.write(r"\end{document}" + "\n")
            finally:
                f.close()

        tmp_name = name
        orig_dir = os.getcwd()
        os.chdir(utils.PATH['cache'])
        write_tex_file(tmp_name + '.tex')
        os.system("pdflatex " + tmp_name + '.tex')
        os.system("pdftocairo -svg " + tmp_name + '.pdf ' + tmp_name + '.svg')
        os.chdir(orig_dir)

        svgfile = os.path.join(utils.PATH['cache'], tmp_name + '.svg')
        delta = io.loadSVG(svgfile, name, **kwargs)
        self.delta = {key:val for key, val in delta.items() if key in delta['changedFields']}
        self.obj_names = [o.name for o in self.delta['objects']]
        self.obj_names.sort()
        if len(self.obj_names) == 1:
            self.base_obj_name = self.obj_names[0]
        else: # make an empty and parent everything
            emp = bpy.data.objects.new(kwargs_names['obj_name'], None)
            col = core.Collection('coll_name')()
            col.objects.link(emp)
            for o in [bpy.data.objects[obj_name] for obj_name in self.obj_names]:
                o.parent = emp
            self.base_obj_name = emp.name
        
        super().__init__(self.base_obj_name)
