"""
Utility functions
"""
import os
import sys
import numpy as np

import bpy # pylint: disable=import-error
import bmesh # pylint: disable=import-error

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

import pntools as pn

def apply_matrix(vert, mat):
    """
    Apply matrix transformation to a set of vertices.
    """
    v4 = np.concatenate((vert, np.ones([np.shape(vert)[0], 1])), axis=1)
    return np.matmul(mat, v4.T).T[:, 0:3]
 
def geom2vef(geom):
    """
    Split geometry into vertex, edge, and faces. Important when using bmesh.
    """
    v = [ele for ele in geom if isinstance(ele, bmesh.types.BMVert)]
    e = [ele for ele in geom if isinstance(ele, bmesh.types.BMEdge)]
    f = [ele for ele in geom if isinstance(ele, bmesh.types.BMFace)]
    return v, e, f

def clean_names(func, name, msh_name, obj_name, coll_name, priority='new', priority_msh='current'):
    """
    Naming convention for blender python module.

    name gets copied into mesh and object names, unless a msh_name is specified.
    In case name, msh_name and obj_name are specified, name becomes irrelevant.

    If the function's priority to create a new object (e.g. all creation functions), then:
        If obj_name exists in blender environment, then make a new object name.
    """
    assert priority in ('new', 'current')
    func_defaults = pn.get_func_inputs(func)
    if isinstance(name, str):
        if obj_name is func_defaults['obj_name']:
            obj_name = name
        if msh_name is func_defaults['msh_name']:
            msh_name = name

    if priority == 'new':
        obj_name = new_name(obj_name, [o.name for o in bpy.data.objects])
    
    if priority_msh == 'new':
        msh_name = new_name(msh_name, [m.name for m in bpy.data.meshes])
    
    return name, msh_name, obj_name, coll_name

def new_name(name, curr_names):
    """
    Blender-style name conflict resolution.

    Appends .001 if name is in curr_names
    If name+'.001' exists, then returns name+'.002' and so on

    Example:
        obj_name = new_name(obj_name, [o.name for o in bpy.data.objects])
    """
    i = 0
    tmp_name = name
    while tmp_name in curr_names:
        i += 1
        tmp_name = name + '.{:03d}'.format(i)
    return tmp_name
