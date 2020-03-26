"""
Creation submodule for bpn.
"""
from functools import partial
import numpy as np

import pntools as pn

import bpn
import bpy #pylint: disable=import-error
import bmesh #pylint: disable=import-error
import mathutils #pylint: disable=import-error

from . import vef
from .utils import clean_names

def collection(coll_name='Collection'):
    """
    Create a new collection with name coll_name if it doesn't exist.
    Returns: (bpy.types.Collection)
    """
    if coll_name in [c.name for c in bpy.data.collections]:
        col = bpy.data.collections[coll_name]
    else:
        col = bpy.data.collections.new(coll_name)
        bpy.context.scene.collection.children.link(col)
    return col

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
        col = collection(col)

    if obj_name in [o.name for o in bpy.data.objects]:
        o = bpy.data.objects[obj_name]
    else:
        o = bpy.data.objects.new(obj_name, msh)
        col.objects.link(o)
    return o

# easy object creation
def easycreate(mshfunc, name=None, return_type='bpn.Msh', **kwargs):
    """
    **kwargs : u=16, v=8, r=0.5 for uv sphere
    **kwargs : size=0.5 for uv cube

    Warning: Avoid empty creates such as new.sphere()!
    """
    names, kwargs = clean_names(name, kwargs, {'priority_obj':'new', 'priority_msh':'current'})

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

    if 'bpn' in str(return_type) and 'Msh' in str(return_type):
        if names['msh_name'] in [m.name for m in bpy.data.meshes]:
            msh = bpy.data.meshes[names['msh_name']]
        else:
            msh = bpy.data.meshes.new(names['msh_name'])
            bm = bmesh.new()
            mshfunc(bm, **kwargs)
            bm.to_mesh(msh)
            bm.free()
            msh.update()
        return bpn.Msh(msh_name=msh.name, obj_name=names['obj_name'], coll_name=names['coll_name'], pargs=kwargs)
    elif 'BMesh' in str(return_type):
        bm = bmesh.new()
        mshfunc(bm, **kwargs)
        return bm

sphere = partial(easycreate, bmesh.ops.create_uvsphere)
monkey = partial(easycreate, bmesh.ops.create_monkey)
cube = partial(easycreate, bmesh.ops.create_cube)
cone = partial(easycreate, bmesh.ops.create_cone)
polygon = partial(cone, **{'d':0, 'cap_ends':False, 'cap_tris':False, 'r1':2.2, 'r2':1.8})

def ngon(**kwargs):
    """Create a new n-sided polygon with one face inscribed in a circle of radius r."""
    kwargs_def = {'n':6, 'r':1, 'theta_offset_deg':-1, 'fill':True, 'return_type':'bpn.Msh'}
    kwargs_alias = {'n':['segments', 'seg', 'u', 'n'], 'r':['radius', 'r'], 'theta_offset_deg':['theta_offset_deg', 'th', 'offset', 'th_off_deg'], 'fill':['fill'], 'return_type':['return_type', 'out']}
    kwargs_fun, kwargs_msh = pn.clean_kwargs(kwargs, kwargs_def, kwargs_alias)
    
    # if offset isn't specified, compute it
    if kwargs_fun['theta_offset_deg'] == kwargs_def['theta_offset_deg']:
        kwargs_fun['theta_offset_deg'] = _ngon_offset_deg(kwargs_fun['n'])
            
    v, e, f = vef.ngon(n=kwargs_fun['n'], r=kwargs_fun['r'], th_off_deg=kwargs_fun['theta_offset_deg'])
    if not kwargs_fun['fill']:
        f = []

    if 'bpn' in str(kwargs_fun['return_type']) and 'Msh' in str(kwargs_fun['return_type']):
        return bpn.Msh(v=v, e=e, f=f, **kwargs_msh)
    elif 'vef' in kwargs_fun['return_type']:
        return v, e, f

def _ngon_offset_deg(n):
    return ((n-2)*180/n)%90 if n%2 == 1 else 360/(2*n)


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
    names, kwargs = clean_names(name, kwargs, {'msh_name':'torus', 'obj_name':'torus', 'priority_msh':'current', 'priority_obj':'new'})

    kwargs_def = {'n_u':16, 'r_u':0.3, 'n_v':32, 'r_v':1, 'theta_offset_deg':-1}
    kwargs_alias = {'n_u':['n_u', 'u'], 'r_u':['r_u', 't', 'thickness'], 'n_v':['n_v', 'v'], 'r_v':['r_v', 'r'], 'theta_offset_deg':['theta_offset_deg', 'th', 'offset', 'th_off_deg', 'th_u']}
    kwargs, _ = pn.clean_kwargs(kwargs, kwargs_def, kwargs_alias)
    
    if kwargs['theta_offset_deg'] == kwargs_def['theta_offset_deg']:
        kwargs['theta_offset_deg'] = _ngon_offset_deg(kwargs['n_u'])

    a = bpn.Draw(**names)
    v, e, _ = bpn.vef.ngon(n=kwargs['n_u'], r=kwargs['r_u'], th_off_deg=kwargs['theta_offset_deg'])
    start = a.addvef(v, e, [])
    bmesh.ops.rotate(a.bm, verts=start.v, cent=(0, 0, 0), matrix=mathutils.Matrix.Rotation(np.radians(90.0), 3, 'Y'))
    for vert in start.v:
        vert.co += mathutils.Vector((0., -kwargs['r_v'], 0.))
    end = a.spin(angle=2*np.pi-2*np.pi/kwargs['n_v'], steps=kwargs['n_v']-1, axis='z', cent=(0., 0., 0.))
    a.join(start.e + end.e)
    tor = +a
    return tor

# convenience 
def spiral(n_rot=3, res=10, offset_rot=0, **kwargs):
    """
    Makes a spiral.
    :param n_rot: number of rotations
    :param res: resolution (degrees) between points
    """
    θ = np.radians(np.arange(360*offset_rot, 360*n_rot+res, res))
    x = θ*np.sin(θ)/(np.pi*2)
    y = θ*np.cos(θ)/(np.pi*2)
    z = np.zeros_like(θ)

    return bpn.Msh(x=x, y=y, z=z, **kwargs)
