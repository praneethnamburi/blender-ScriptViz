"""
Utility functions
"""
import os

import bpy # pylint: disable=import-error

import bpn
import pntools as pn

PATH = {}
PATH['blender'] = os.path.dirname(pn.locateCommand('blender', verbose=False))
PATH['blender_python'] = os.path.dirname(pn.locateCommand('python', 'blender', verbose=False))
PATH['blender_version'] = os.path.realpath(os.path.join(os.path.dirname(PATH['blender_python']), '..'))
PATH['blender_scripts'] = os.path.join(PATH['blender_version'], 'scripts')
PATH['blender_addons'] = os.path.join(PATH['blender_scripts'], 'addons')
PATH['blender_addons_contrib'] = os.path.join(PATH['blender_scripts'], 'addons_contrib')
PATH['blender_modules'] = os.path.join(PATH['blender_scripts'], 'modules')

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
        return bpn.Msh(obj_name=[o.name for o in bpy.data.objects][-1])

    if isinstance(obj_name, str) and (obj_name not in [o.name for o in bpy.data.objects]):
        print('No object found with name: ' + obj_name)
        return []

    return bpn.Msh(obj_name=obj_name)

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

def clean_names(name, kwargs, kwargs_def=None):
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
    if isinstance(name, str):
        kwargs['msh_name'] = name if 'msh_name' not in kwargs else kwargs['msh_name']
        kwargs['obj_name'] = name if 'obj_name' not in kwargs else kwargs['obj_name']

    kwargs_defdef = {
        'msh_name' : 'new_msh', 
        'obj_name' : 'new_obj',
        'coll_name': 'Collection',
        'priority_obj': 'new',
        'priority_msh': 'current',
    }
    if not kwargs_def:
        kwargs_def = {}

    kwargs_def, _ = pn.clean_kwargs(kwargs_def, kwargs_defdef)
    kwargs_names, kwargs_other = pn.clean_kwargs(kwargs, kwargs_def)
    
    # what to do if 'obj_name' and/or 'msh_name' already exist in the blender workspace
    if kwargs_names['priority_obj'] == 'new':
        kwargs_names['obj_name'] = new_name(kwargs_names['obj_name'], [o.name for o in bpy.data.objects])
    
    if kwargs_names['priority_msh'] == 'new':
        kwargs_names['msh_name'] = new_name(kwargs_names['msh_name'], [m.name for m in bpy.data.meshes])

    return kwargs_names, kwargs_other
