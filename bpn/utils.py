"""
Utility functions

Dispatchers: get, enhance
    get will return either one bpn.core object, or a list of bpn.core objects
    Use get in the blender console.
    When developing software, stick to enhance and avoid get.

Name management:
    new_name      - blender-style name conflict resolution
    clean_names   - name management for creation functions
    bpy_type      - string -> blender class name ('Object' -> bpy.types.Object)
    bpy_data_coll - string -> blend data collection ('Object' -> bpy.data.objects)

Color management:
    color_palette - preset color palettes, returns {color_name: rgba}
    new_gp_color  - create a new grease pencil color
"""
import os
import re

import numpy as np
import matplotlib.colors as mc

import bpy # pylint: disable=import-error
import mathutils # pylint: disable=import-error

import pntools as pn

from bpn import core, env

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

    If there are objects and curves with the same name, then use
        utils.get(['x_label', 'y_label'], priority='Curve') to get the curves
        utils.get(['x_label', 'y_label']) to get the objects
        utils.get(['x_label', 'y_label'], 'all') to get both objects and curves

    Regular expressions: (With regular expression input, generic 'Thing' objects are filtered out.)
        utils.get('abe.*') to get all objects that contain 'abe'
        utils.get('abe.*', 'all') to get all items that contain 'abe'
        utils.get('^z') to get things starting with 'z'
        utils.get('^z') to get things ending with '_R'
        utils.get(['^my', '_R$']) to get things starting with my OR ending with '_R$'    

    Return all objects of a certain type:
        utils.get('collections')
    """
    def _input_check(name, mode):
        assert mode in (None, 'all')
        assert isinstance(name, (str, list)) or name is None
        assert not (mode == 'all' and name is None)

        regex_flag = False
        regex = re.compile('[.^$*+}{|)(]')
        if isinstance(name, str):
            if regex.search(name) is not None: # not a normal string
                name = env.Props().search(name)
                regex_flag = True

        if isinstance(name, list): # if name is a list of regular expressions
            checked_name = []
            for this_name in name:
                if regex.search(this_name) is not None:
                    checked_name += env.Props().search(this_name)
                    regex_flag = True
                else:
                    checked_name += [this_name]
            name = list(np.unique(checked_name))
            name = [n for n in name if '/' not in n]
            if len(name) == 1:
                name = name[0]
        return name, mode, regex_flag
    
    def _get_one_with_name(name):
        """Returns one dispatched object."""
        all_items = env.Props().get(name)
        if all_items: # at least one item found
            all_obj_items = [item for item in all_items if type(item).__name__ == priority]
            if all_obj_items: # one of the items was object item
                return enhance(all_obj_items[0])
            return enhance(all_items[0])
        # print('No prop found with name: ' + name) # can throw too many warnings in practice
        return []
    
    def _get_all_with_name(name):
        """Returns a list of dispatched objects (even if there is only one)."""
        assert isinstance(name, str)
        return [enhance(item) for item in env.Props().get(name) if enhance(item)]

    def _dispatcher(name, mode):
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
        return [] # In theory, this statement should never be reached
    
    if isinstance(name, str) and name in env.PROP_FIELDS: # special case: return all items of a given type
        return [enhance(t) for t in env.Props()(return_empty=True)[name]]

    name, mode, regex_flag = _input_check(name, mode)
    ret_list = _dispatcher(name, mode)
    if regex_flag and isinstance(ret_list, list):
        ret_list = [o for o in ret_list if o.__class__.__name__ != 'Thing']
        if len(ret_list) == 1: # after filtering, there was only one element
            ret_list = ret_list[0]
    return ret_list


def enhance(item): # item is bpy.data.(sometype)
    """
    Turns a bpy.data.(sometype) into a bpn.core object

    Heart of the dispatcher. Use the dispatcher (get) for getting things
    by name. Use this for converting a bpy.types.ID to bpn.core object.

    get is useful when you're in blender's python console
    enhance is useful when developing code
    """
    assert isinstance(item, bpy.types.ID)
    def _fix_type(thing_type): # thing_type is bpy.types.(sometype)
        # lights cause an issue here
        if plural(thing_type.__name__.lower()) not in env.PROP_FIELDS:
            thing_type = [k for k in thing_type.__mro__[:-1] if plural(k.__name__.lower()) in env.PROP_FIELDS]
            if not thing_type:
                return [] # window manager caused issue when searching for ALL objects
            thing_type = thing_type[0]
        return thing_type

    thing_type = _fix_type(type(item))
    if not thing_type:
        return []
    thing_type = thing_type.__name__
    if thing_type == 'Object' and item.type == 'MESH':
        return core.MeshObject(item.name)
    if thing_type == 'Object' and item.type == 'GPENCIL':
        return core.GreasePencilObject(item.name)
    if thing_type == 'Object' and item.type == 'CURVE':
        return core.CurveObject(item.name)
    if thing_type == 'Object' and item.type == 'EMPTY':
        return core.ContainerObject(item.name)
    if hasattr(core, thing_type):
        return getattr(core, thing_type)(item.name)
    return core.Thing(item.name, thing_type)

### Name management
def new_name(name, curr_names=None):
    """
    Blender-style name conflict resolution.

    Appends .001 if name is in curr_names
    If name+'.001' exists, then returns name+'.002' and so on

    Example:
        obj_name = new_name(obj_name, [o.name for o in bpy.data.objects])
    """
    if curr_names is None:
        curr_names = [o.name for o in bpy.data.objects]
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

def bpy_coll_name(this_type):
    """
    bpy.types.Object -> 'objects'
    'Object' -> 'objects'
    Useful for going from bpy.types.(Something) to bpy.data.(something)
    """
    if isinstance(this_type, str):
        this_type = bpy_type(this_type)
    thing_coll_name = plural(this_type.__name__.lower())
    if thing_coll_name == 'greasepencils':
        thing_coll_name = 'grease_pencils'
    if thing_coll_name == 'nodegroups':
        thing_coll_name = 'node_groups'
    return thing_coll_name


# color management
def color_palette(name='all', prefix='', alpha=0.8):
    """
    Commonly used color palettes for plotting.
    """
    assert name in ('MATLAB', 'blender_ax', 'mpl', 'all')

    alpha_broadcast = lambda n: alpha*np.ones(n) if isinstance(alpha, (int, float)) else alpha
    
    if name == 'MATLAB':
        α = alpha_broadcast(7)
        if not prefix:
            prefix = 'MATLAB_'
        return {
            prefix+'00': (0.000, 0.447, 0.741, α[0]),
            prefix+'01': (0.850, 0.325, 0.098, α[1]),
            prefix+'02': (0.929, 0.694, 0.125, α[2]),
            prefix+'03': (0.494, 0.184, 0.556, α[3]),
            prefix+'04': (0.466, 0.674, 0.188, α[4]),
            prefix+'05': (0.301, 0.745, 0.933, α[5]),
            prefix+'06': (0.635, 0.078, 0.184, α[6]),
        }

    if name == 'blender_ax':
        α = alpha_broadcast(3)
        return {
            prefix+'crd_i': (1.000, 0.125, 0.400, α[0]),
            prefix+'crd_j': (0.400, 0.850, 0.125, α[1]),
            prefix+'crd_k': (0.055, 0.500, 1.000, α[2]),
        }
    
    if name == 'mpl': # matplotlib        
        return {c: mc.to_rgba(c, alpha) for c in mc.cnames} # does it make sense to broadcast alpha?
    
    if name == 'all':
        return {**color_palette('MATLAB', alpha=alpha), **color_palette('blender_ax', alpha=alpha), **color_palette('mpl', alpha=alpha)}

    return None

colors = color_palette('all', alpha=1)

def new_gp_color(mtrl_name, rgba=None):
    """
    Create a new grease pencil color.
    Create the material if it doesn't exist.
    Return an existing one if it exists.
    Update the rgba if material with mtrl_name already exists.
    Returns:
        Material object (bpy.data.materials)
    """
    if rgba is None:
        rgba = mc.to_rgba(mtrl_name)
    if mtrl_name in [m.name for m in bpy.data.materials]:
        mtrl = bpy.data.materials[mtrl_name]
    else:
        mtrl = bpy.data.materials.new(mtrl_name)
    bpy.data.materials.create_gpencil_data(mtrl)
    mtrl.grease_pencil.color = rgba
    return mtrl


# Curve management - move this to core.Curve?
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
