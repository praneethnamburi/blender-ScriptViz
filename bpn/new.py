"""
Creation submodule for bpn.
"""
from functools import partial

import bpy #pylint: disable=import-error
import bmesh #pylint: disable=import-error

def collection(coll_name='newColl'):
    if coll_name in [c.name for c in bpy.data.collections]:
        col = bpy.data.collections[coll_name]
    else:
        col = bpy.data.collections.new(coll_name)
        bpy.context.scene.collection.children.link(col)
    return col

def obj(msh, col, obj_name='newObj'):
    """
    Creates an object with obj_name if it does not exist.
    If object with name exists, returns object
    
    DOES NOT: change collection of the object if col is different from the object's collection
    """
    if isinstance(msh, str):
        msh = bpy.data.meshes[msh]
    if isinstance(col, str):
        col = bpy.data.collections[col]

    if obj_name in [o.name for o in bpy.data.objects]:
        o = bpy.data.objects[obj_name]
    else:
        o = bpy.data.objects.new(obj_name, msh)
        col.objects.link(o)
    return o

# easy object creation
def easycreate(mshfunc, obj_name='newObj', msh_name='newMsh', coll_name='newColl', name=None, **kwargs):
    """
    **kwargs : u=16, v=8, r=0.5 for uv sphere
    **kwargs : size=0.5 for uv cube
    """
    if isinstance(name, str):
        if obj_name is easycreate.__defaults__[0]:
            obj_name = name
        if msh_name is easycreate.__defaults__[1]:
            msh_name = name
    col = collection(coll_name)

    # input control for sphere
    if str(mshfunc) == str(bmesh.ops.create_uvsphere):
        if 'u' in kwargs:
            kwargs['u_segments'] = kwargs.pop('u')
        if 'v' in kwargs:
            kwargs['v_segments'] = kwargs.pop('v')
        if 'r' in kwargs:
            kwargs['diameter'] = kwargs.pop('r')
        if 'u_segments' not in kwargs:
            kwargs['u_segments'] = 16
        if 'v_semgents' not in kwargs:
            kwargs['v_segments'] = 8
        if 'diameter' not in kwargs:
            kwargs['diameter'] = 0.5

    if msh_name in [m.name for m in bpy.data.meshes]:
        msh = bpy.data.meshes[msh_name]
    else:
        msh = bpy.data.meshes.new(msh_name)
        bm = bmesh.new()
        mshfunc(bm, **kwargs)
        bm.to_mesh(msh)
        bm.free()

    o = obj(msh, col, obj_name)
    return o

sphere = partial(easycreate, bmesh.ops.create_uvsphere)
monkey = partial(easycreate, bmesh.ops.create_monkey)
cube = partial(easycreate, bmesh.ops.create_cube)
cone = partial(easycreate, bmesh.ops.create_cone)

def primitive(pType='monkey', location=(1.0, 3.0, 5.0)):
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