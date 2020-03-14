"""
Creation submodule for bpn.
"""
import os
import sys
from functools import partial

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

import pntools as pn

import bpn
import bpy #pylint: disable=import-error
import bmesh #pylint: disable=import-error

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
def easycreate(mshfunc, obj_name='newObj', msh_name='newMsh', coll_name='Collection', name=None, **kwargs):
    """
    **kwargs : u=16, v=8, r=0.5 for uv sphere
    **kwargs : size=0.5 for uv cube
    """
    if isinstance(name, str):
        if obj_name is easycreate.__defaults__[0]:
            obj_name = name
        if msh_name is easycreate.__defaults__[1]:
            msh_name = name

    # input control
    if str(mshfunc) == str(bmesh.ops.create_uvsphere):
        kwargs_def = {'u_segments':16, 'v_segments':8, 'diameter':0.5}
        kwargs_alias = {'u_segments': ['u', 'u_segments'], 'v_segments': ['v', 'v_segments'], 'diameter': ['r', 'diameter']}
        kwargs = pn.clean_kwargs(kwargs, kwargs_def, kwargs_alias)

    if str(mshfunc) == str(bmesh.ops.create_cube):
        kwargs_def = {'size':1}
        kwargs_alias = {'size': ['size', 'sz', 's', 'r']}
        kwargs = pn.clean_kwargs(kwargs, kwargs_def, kwargs_alias)
    
    if str(mshfunc) == str(bmesh.ops.create_cone):
        kwargs_def = {'segments':12, 'diameter1':2, 'diameter2':0, 'depth':3, 'cap_ends':True, 'cap_tris':False}
        kwargs_alias = {'segments':['segments', 'seg', 'u', 'n'], 'diameter1':['diameter1', 'r1', 'r'], 'diameter2':['diameter2', 'r2'], 'depth':['depth', 'd', 'h'], 'cap_ends':['cap_ends', 'fill'], 'cap_tris':['cap_tris', 'fill_tri']}
        kwargs = pn.clean_kwargs(kwargs, kwargs_def, kwargs_alias)

    if str(mshfunc) == str(bmesh.ops.create_circle):
        kwargs_def = {'segments':32, 'radius':1, 'cap_ends':False, 'cap_tris':False}
        kwargs_alias = {'segments':['segments', 'seg', 'u', 'n'], 'radius':['radius', 'r'], 'cap_ends':['cap_ends', 'fill'], 'cap_tris':['cap_tris', 'fill_tri']}
        kwargs = pn.clean_kwargs(kwargs, kwargs_def, kwargs_alias)

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
ngon = polygon

# No faces, just edges
circle = partial(easycreate, bmesh.ops.create_circle)

# other primitives:
# cylinder, grid, ico_sphere, plane, torus
