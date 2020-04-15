"""
Utility functions
"""
import os
import re

import numpy as np

import bpy # pylint: disable=import-error
import mathutils # pylint: disable=import-error

import pntools as pn

from . import core, env

PATH = {}
DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
PATH['cache'] = os.path.join(DEV_ROOT, '_temp')

plural = lambda string: string+'es' if string[-2:] in ('ch', 'sh') or string[-1] in ('s', 'x', 'z') else string+'s'

# perhaps the most useful function
def get(name=None, mode=None, priority='Object'):
    """
    Dispatcher for the bpn module.
    Takes as input the name of a prop in the blender environment.
    Returns a 'wrapped' version of the object.

    MESH bpy.types.Object - core.MeshObject
    Other bpy.types.Object - core.Object
    Prop in bpy.data.* - core.Thing
    
    bpn.obj('sphere')
    :param obj_name: (str) name of the object in blender's environment
    :param mode: (None, 'all') if 'all', returns all things with the name (priority given to objects)

    If there are objects and curves with the same name, then 
    utils.get(['x_label', 'y_label'], priority='Curve') will return the curves
    utils.get(['x_label', 'y_label']) will return the objects
    utils.get(['x_label', 'y_label'], 'all') will return both objects and curves
    utils.get('abe.*') to get all objects that contain 'abe'
    utils.get('abe.*', 'all') to get all items that contain 'abe'
    """
    assert mode in (None, 'all')
    assert isinstance(name, (str, list)) or name is None
    assert not (mode == 'all' and name is None)

    regex = re.compile('[.^$*+}{|)(]')
    if isinstance(name, str):
        if regex.search(name) is not None: # not a normal string
            name = env.Props().search(name)

    if isinstance(name, list): # if name is a list of regular expressions
        checked_name = []
        for this_name in name:
            if regex.search(this_name) is not None:
                checked_name += env.Props().search(this_name)
            else:
                checked_name += [this_name]
        name = list(np.unique(checked_name))
        name = [n for n in name if '/' not in n]
        if len(name) == 1:
            name = name[0]
    
    def _fix_type(thing_type):
        # lights cause an issue here
        if plural(thing_type.__name__.lower()) not in env.PROP_FIELDS:
            thing_type = [k for k in thing_type.__mro__[:-1] if plural(k.__name__.lower()) in env.PROP_FIELDS]
            if not thing_type:
                return [] # window manager caused issue when searching for ALL objects
            thing_type = thing_type[0]
        return thing_type

    def _enhance_item(item): # item is bpy.data.(sometype)
        thing_type = _fix_type(type(item))
        if not thing_type:
            return []
        thing_type = thing_type.__name__
        if thing_type == 'Object' and item.type == 'MESH':
            return check_core_item_exists(item.name, core.MeshObject)
        if hasattr(core, thing_type):
            return check_core_item_exists(item.name, getattr(core, thing_type))
        return check_core_item_exists(item.name, core.Thing)

    def _get_one_with_name(name):
        """Returns one dispatched object."""
        all_items = env.Props().get(name)
        if all_items: # at least one item found
            all_obj_items = [item for item in all_items if type(item).__name__ == priority]
            if all_obj_items: # one of the items was object item
                return _enhance_item(all_obj_items[0])
            return _enhance_item(all_items[0])
        print('No prop found with name: ' + name)
        return []
    
    def _get_all_with_name(name):
        """Returns a list of dispatched objects (even if there is only one)."""
        assert isinstance(name, str)
        return [_enhance_item(item) for item in env.Props().get(name) if _enhance_item(item)]

    if mode is None and name is None: # no inputs given, return the last object
        return _get_one_with_name([o.name for o in bpy.data.objects][-1])
    if mode is None and isinstance(name, str): # return one object
        return _get_one_with_name(name)
    if mode is None and isinstance(name, list):
        return [_get_one_with_name(this_name) for this_name in name]
    if mode == 'all' and isinstance(name, str):
        return _get_all_with_name(name)
    if mode == 'all' and isinstance(name, list): # here for completeness, don't recommend using it
        ret_list = []
        for this_name in name:
            ret_list += _get_all_with_name(this_name)
        return ret_list

def check_core_item_exists(item_name, item_enhanced_class):
    """
    Search for the enhanced item in the classes before creating them
    This can work because all the core classes are being tracked using pntools.tracker
    This way, the dispatcher won't create new enhanced objects every time it is called
    """
    this_item = [o for o in item_enhanced_class.all if o.name == item_name]
    if this_item:
        return this_item[0]
    return item_enhanced_class(item_name)

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

def bpy_type(type_name):
    """'Object' -> bpy.types.Object."""
    assert isinstance(type_name, str)
    if type_name[0].lower() == type_name[0]:
        type_name = type_name.title()
    exc = {'Greasepencil':'GreasePencil', 'Lightprobe':'LightProbe', 'Nodegroup':'NodeGroup'}
    type_name = exc.get(type_name, type_name)
    return getattr(bpy.types, type_name) # bpy.types.Object

def bpy_data_coll(this_type):
    """
    bpy.types.Object -> bpy.data.objects
    'Object' -> bpy.data.objects

    Useful:
        [k for k in dir(bpy.data) if hasattr(getattr(bpy.data, k), 'new')]
    """
    if isinstance(this_type, str):
        this_type = bpy_type(this_type)
    thing_coll_name = plural(this_type.__name__.lower())
    if thing_coll_name == 'greasepencils':
        thing_coll_name = 'grease_pencils'
    if thing_coll_name == 'nodegroups':
        thing_coll_name = 'node_groups'
    return getattr(bpy.data, thing_coll_name)

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

def align_curve(bez_curve, halign='center', valign='middle'):
    """
    Align a bezier curve.
    In the future, if there is a bezier curve class, this will move there.
    """
    all_pt = []
    for spl in bez_curve.splines:
        for pt in spl.bezier_points:
            all_pt.append(np.array(pt.co))
    all_pt = np.array(all_pt)
    
    trans = np.array([0., 0., 0.]) # amount of translation
    if halign == 'center':
        trans[0] = np.mean(all_pt[:, 0])
    if halign == 'left':
        trans[0] = np.min(all_pt[:, 0])
    if halign == 'right':
        trans[0] = np.max(all_pt[:, 0])

    if valign == 'middle':
        trans[1] = np.mean(all_pt[:, 1])
    if valign == 'bottom':
        trans[1] = np.min(all_pt[:, 1])
    if valign == 'top':
        trans[1] = np.max(all_pt[:, 1])

    trans = mathutils.Vector(trans)
    for spl in bez_curve.splines:
        for pt in spl.bezier_points:
            pt.co -= trans
            pt.handle_left -= trans
            pt.handle_right -= trans

def combine_curves(obj_list, mtrl_list=None):
    """Combine bezier curves into one object."""
    copied_curves = []
    base_obj = obj_list[0]
    base_curve = base_obj.data
    all_materials = base_curve.materials[:]
    attrs_pts = ['co', 'handle_left', 'handle_right', 'handle_left_type', 'handle_right_type']
    attrs_spline = ['order_u', 'order_v', 'resolution_u', 'resolution_v', 'tilt_interpolation', 'use_bezier_u', 'use_bezier_v', 'use_cyclic_u', 'use_cyclic_v', 'use_endpoint_u', 'use_endpoint_v', 'use_smooth']
    for obj in obj_list[1:]:
        curve = obj.data
        copied_curves.append(curve)
        all_materials += curve.materials[:]
        for spl in curve.splines:
            if spl.type != 'BEZIER':
                continue # only bezier splines are copied for now!
            spl_targ = base_curve.splines.new(type='BEZIER')
            spl_targ.bezier_points.add(len(spl.bezier_points)-1)
            for pt_targ, pt in zip(spl_targ.bezier_points[:], spl.bezier_points[:]):
                for attr in attrs_pts:
                    setattr(pt_targ, attr, getattr(pt, attr))
            for attr in attrs_spline:
                setattr(spl_targ, attr, getattr(spl, attr))
    
    # cleanup
    for obj in obj_list[1:]:
        bpy.data.objects.remove(obj)
    for curve in copied_curves:
        bpy.data.curves.remove(curve)
    base_materials = [ml.name for ml in base_curve.materials]
    if mtrl_list is not None:
        for mtrl in mtrl_list:
            if mtrl.name not in base_materials:
                bpy.data.materials.remove(mtrl)

def copy_curve(curve_src):
    """Used to check Bezier curve anomaly."""
    attrs_pts = ['co', 'handle_left', 'handle_right', 'handle_left_type', 'handle_right_type']
    attrs_spline = ['order_u', 'order_v', 'resolution_u', 'resolution_v', 'tilt_interpolation', 'use_bezier_u', 'use_bezier_v', 'use_cyclic_u', 'use_cyclic_v', 'use_endpoint_u', 'use_endpoint_v', 'use_smooth']

    curve_targ = bpy.data.curves.new(curve_src.name, 'CURVE')
    for spl in curve_src.splines:
        if spl.type != 'BEZIER':
            continue # only bezier splines are copied for now!
        spl_targ = curve_targ.splines.new(type='BEZIER')
        spl_targ.bezier_points.add(len(spl.bezier_points)-1)
        for pt_targ, pt in zip(spl_targ.bezier_points[:], spl.bezier_points[:]):
            for attr in attrs_pts:
                setattr(pt_targ, attr, getattr(pt, attr))
        for attr in attrs_spline:
            setattr(spl_targ, attr, getattr(spl, attr))
    return curve_targ
