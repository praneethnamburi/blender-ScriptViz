"""
Creation submodule for bpn.
"""
from functools import partial
import os
import sys
import numpy as np

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

import pntools as pn

import bpn
import bpy #pylint: disable=import-error
import bmesh #pylint: disable=import-error

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
def easycreate(mshfunc, name=None, msh_name='newMsh', obj_name='newObj', coll_name='Collection', **kwargs):
    """
    **kwargs : u=16, v=8, r=0.5 for uv sphere
    **kwargs : size=0.5 for uv cube

    Warning: Avoid empty creates such as new.sphere()!
    """
    name, msh_name, obj_name, coll_name = clean_names(easycreate, name, msh_name, obj_name, coll_name, 'new', 'current')

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

    if msh_name in [m.name for m in bpy.data.meshes]:
        msh = bpy.data.meshes[msh_name]
    else:
        msh = bpy.data.meshes.new(msh_name)
        bm = bmesh.new()
        mshfunc(bm, **kwargs)
        bm.to_mesh(msh)
        bm.free()
        msh.update()

    return bpn.Msh(msh_name=msh.name, obj_name=obj_name, coll_name=coll_name, pargs=kwargs)

sphere = partial(easycreate, bmesh.ops.create_uvsphere)
monkey = partial(easycreate, bmesh.ops.create_monkey)
cube = partial(easycreate, bmesh.ops.create_cube)
cone = partial(easycreate, bmesh.ops.create_cone)
polygon = partial(cone, **{'d':0, 'cap_ends':False, 'cap_tris':False, 'r1':2.2, 'r2':1.8})

def ngon(**kwargs):
    """Create a new n-sided polygon with one face inscribed in a circle of radius r."""
    kwargs_def = {'n':6, 'r':1, 'theta_offset_deg':-1, 'fill':True}
    kwargs_alias = {'n':['segments', 'seg', 'u', 'n'], 'r':['radius', 'r'], 'theta_offset_deg':['theta_offset_deg', 'th', 'offset', 'th_off_deg'], 'fill':['fill']}
    kwargs_fun, kwargs_msh = pn.clean_kwargs(kwargs, kwargs_def, kwargs_alias)
    
    # if offset isn't specified, compute it
    if kwargs_fun['theta_offset_deg'] == kwargs_def['theta_offset_deg']:
        n = kwargs_fun['n']
        if n%2 == 1: # odd number of faces
            kwargs_fun['theta_offset_deg'] = ((n-2)*180/n)%90
        else:
            kwargs_fun['theta_offset_deg'] = 360/(2*n)
            
    v, e, f = vef.ngon(n=kwargs_fun['n'], r=kwargs_fun['r'], th_off_deg=kwargs_fun['theta_offset_deg'])
    if not kwargs_fun['fill']:
        f = []

    return bpn.Msh(v=v, e=e, f=f, **kwargs_msh)

plane = partial(ngon, **{'n':4, 'r':2/np.sqrt(2), 'theta_offset_deg':45})

# No faces, just edges - redundant now, just use ngon
circle = partial(easycreate, bmesh.ops.create_circle)

# other primitives:
# cylinder, grid, ico_sphere, torus

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
