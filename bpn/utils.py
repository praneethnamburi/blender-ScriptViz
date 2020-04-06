"""
Utility functions
"""
import os

import numpy as np

import bpy # pylint: disable=import-error

import pntools as pn

from . import core

PATH = {}
DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
PATH['cache'] = os.path.join(DEV_ROOT, '_temp')

# perhaps the most useful function
def get(obj_name=None):
    """
    Create a bpn msh object from object name
    bpn.obj('sphere')
    :param obj_name: (str) name of the object in blender's environment
    """
    if not obj_name: # return the last objects
        return core.Msh(obj_name=[o.name for o in bpy.data.objects][-1])

    if isinstance(obj_name, str) and (obj_name not in [o.name for o in bpy.data.objects]):
        print('No object found with name: ' + obj_name)
        return []

    return core.Msh(obj_name=obj_name)

### Name management
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

def clean_names(name, kwargs, kwargs_def=None, mode='msh'):
    """
    Use this for name cleanup!
    Splits keyword arguments into names as used by the bpn module, and other keyword arguments to be used by the function.
    
    This has a similar purpose to pntools.clean_kwargs (in terms of splitting up keyword arguments, and ensuring defaults).
    In addition, it implements some name checking int he blender-environment.
    In the future, we can extend this functionality to include scene names, etc. simply by adding to default arguments.
    Usage:
        def mydrawingfunc(name=None, **kwargs):
            kwargs_names, kwargs_forthisfunc = clean_names(name, kwargs, defaultsformydrawingfunc)
    See:
        Draw class in bpn.turtle
        torus function in bpn.new
    """
    assert mode in ('gp', 'msh', 'curve')
    if isinstance(name, str):
        kwargs[mode+'_name'] = name if mode+'_name' not in kwargs else kwargs[mode+'_name']
        kwargs['obj_name'] = name if 'obj_name' not in kwargs else kwargs['obj_name']

    kwargs_defdef = {
        mode+'_name' : 'new_'+mode, 
        'obj_name' : 'new_obj',
        'coll_name': 'Collection',
        'priority_obj': 'new',
        'priority_'+mode: 'current',
    }
    if mode == 'gp':
        kwargs_defdef['layer_name'] = 'new_layer'

    if not kwargs_def:
        kwargs_def = {}

    kwargs_def, _ = pn.clean_kwargs(kwargs_def, kwargs_defdef)
    kwargs_names, kwargs_other = pn.clean_kwargs(kwargs, kwargs_def)
    
    # what to do if 'obj_name' and/or 'msh_name' already exist in the blender workspace
    if kwargs_names['priority_obj'] == 'new':
        kwargs_names['obj_name'] = new_name(kwargs_names['obj_name'], [o.name for o in bpy.data.objects])
    
    if mode == 'msh':
        if kwargs_names['priority_msh'] == 'new':
            kwargs_names['msh_name'] = new_name(kwargs_names['msh_name'], [m.name for m in bpy.data.meshes])
    if mode == 'gp':
        if kwargs_names['priority_gp'] == 'new':
            kwargs_names['gp_name'] = new_name(kwargs_names['gp_name'], [g.name for g in bpy.data.grease_pencils])
    if mode == 'curve':
        if kwargs_names['priority_curve'] == 'new':
            kwargs_names['curve_name'] = new_name(kwargs_names['curve_name'], [g.name for g in bpy.data.curves])
    return kwargs_names, kwargs_other

# common color palettes
def color_palette(name='MATLAB', prefix='', alpha=0.8):
    """
    Commonly used color palettes for plotting.
    """
    def rgba2dict(rgba, names):
        n = np.shape(rgba)[0] # number of colors in the palette
        if isinstance(names, str): # names is a prefix instead of an array
            ndec = len(str(n))+1 # number of decimal places
            fstr = '{:0'+str(ndec)+'d}'
            names = [names+fstr.format(i) for i in range(n)]
        assert len(names) == n
        return {names[i] : rgba[i, :] for i in range(n)}

    alpha_broadcast = lambda n: alpha*np.ones(n) if isinstance(alpha, (int, float)) else alpha
    
    if name == 'MATLAB':
        α = alpha_broadcast(7)
        rgba = np.array([
            [0.000, 0.447, 0.741, α[0]],
            [0.850, 0.325, 0.098, α[1]],
            [0.929, 0.694, 0.125, α[2]],
            [0.494, 0.184, 0.556, α[3]],
            [0.466, 0.674, 0.188, α[4]],
            [0.301, 0.745, 0.933, α[5]],
            [0.635, 0.078, 0.184, α[6]],
        ])
        if not prefix:
            prefix = 'MATLAB_'
        return rgba2dict(rgba, prefix) 

    if name == 'blender_ax':
        α = alpha_broadcast(3)
        return {
            prefix+'crd_i': [1.000, 0.125, 0.400, α[0]],
            prefix+'crd_j': [0.400, 0.850, 0.125, α[1]],
            prefix+'crd_k': [0.055, 0.500, 1.000, α[2]],
        }

    return None
