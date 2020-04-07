"""
Input-output functions
"""
import os
import errno
import functools
import inspect

import numpy as np
import pandas as pd

import bpy #pylint: disable=import-error
import mathutils #pylint: disable=import-error

import pntools as pn

from . import new, env, utils

# File IO
@env.ReportDelta
def loadSTL(files):
    """
    Load STL files from disk into a blender scene.
    
    :param files: list. Full file paths.
    :param collection: str. Blender collection name to load the STL into.
    :returns: report of scene change

    Recommended use:
        Instead of directly using this function, use 
        p = bpn.core.Msh(stl=fname, name='mySTL', coll_name='myColl')
    """
    if isinstance(files, str):
        files = [files]
    for f in files:
        if not os.path.exists(f):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), f)
        bpy.ops.import_mesh.stl(filepath=f)

@env.ReportDelta
def loadSVG(svgfile, name=None, **kwargs):
    """
    import an svg file into the blender scene.
    Originally created to import latex text into blender.
    Create text using the commands:
        pdflatex testdoc.tex
        pdftocairo -svg testdoc.pdf testdoc.svg
    
    Example:
        io.loadSVG(os.path.join(utils.PATH['cache'], 'testdoc.svg'), color=utils.color_palette('blender_ax')['crd_k'])
    """
    if name is None:
        name = os.path.splitext(os.path.basename(svgfile))[0]
    kwargs_names, kwargs = utils.clean_names(name, kwargs, {'priority_curve': 'new'}, mode='curve')
    kwargs_def = {
        'remove_default_coll': True,
        'scale': (100, 100, 100), # svg imports are really small
        'color': (1.0, 1.0, 1.0, 1.0),
        'combine_curves': True, # this may not work!!
        'halign' : 'center', # 'center', 'left', 'right', None
        'valign' : 'middle', # 'top', 'middle', 'bottom', None
        }
    kwargs, _ = pn.clean_kwargs(kwargs, kwargs_def)

    @env.ReportDelta
    def _loadSVG(files):
        """
        Import an SVG file into the blender scene.
        Hidden. Use loadSVG.
        """
        if isinstance(files, str):
            files = [files]
        for f in files:
            if not os.path.exists(f):
                raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), f)
            bpy.ops.import_curve.svg(filepath=f)

    s = _loadSVG(svgfile)
    col_def = s['collections'][0]
    col = new.collection(kwargs_names['coll_name'])

    if kwargs['combine_curves']:
        utils.combine_curves(s['objects'], s['materials'])
        base_obj = s['objects'][0]
        base_curve = base_obj.data

        base_obj.name = kwargs_names['obj_name']
        base_curve.name = kwargs_names['curve_name']
        col.objects.link(base_obj)
        col_def.objects.unlink(base_obj)
        base_obj.scale = kwargs['scale']
        for mtrl in base_curve.materials:
            mtrl.diffuse_color = kwargs['color']
        
        # curve alignment
        utils.align_curve(base_obj.data, halign=kwargs['halign'], valign=kwargs['valign'])
    else:
        for obj in s['objects']:
            col.objects.link(obj)
            col_def.objects.unlink(obj)
            obj.scale = kwargs['scale']
            # utils.align_curve(obj.data, halign=kwargs['halign'], valign=kwargs['valign'])

        for mtrl in s['materials']:
            mtrl.diffuse_color = kwargs['color']

    if kwargs['remove_default_coll']:
        bpy.data.collections.remove(col_def)

    bpy.context.view_layer.update()

# Save manual work to excel, or read it in as a pandas dataframe (e.g. nutations in the anatomy project)
def readattr(names, frames=1, attrs='location', fname=False, sheet_name='animation', columns=('object', 'keyframe', 'attribute', 'value')):
    """
    Get location and rotation information of mesh objects from the current blender scene.
    
    Created to save weight in and weight out nutational positions of bones.
    Generalizes to saving location and rotation information for any mesh objects.

    Inputs:
        names: list of names in the blender file, ['Foot_R', 'Leg_R', 'Spine']
            each 'name' can be a blender collection, a parent object (empty), or the name of an object itself
        frames: keyframe numbers in the blender scene to grab location and rotation information from
        attrs: list of attributes ['location', 'rotation_euler', 'scale']
        fname: target file name 'somefile.xlsx'
    
    Returns:
        p: a pandas dataframe containing the name of the mesh, keyframe, location and rotation vectors
        To save contents to an excel file, supply strings to fname, and sheet_name variables

    Example:
        (load skeletalSystem.blend in blender)
        fname = 'D:\\Workspace\\blenderPython\\apps\\anatomy\\nutations.xlsx'
        p2 = bpn.io.readattr('Skeletal_Sys', [1, 100], ['location', 'rotation_euler'], fname)
    """
    if isinstance(names, str):
        names = [names] # convert to list if a string is passed
    if isinstance(frames, int):
        frames = [frames]
    if isinstance(attrs, str):
        attrs = [attrs]

    # make sure names has only valid things in it
    names = [i for i in names if env.Props()(i)]

    p = []
    for frame in frames:
        bpy.context.scene.frame_set(frame)
        for name in names:
            thisProp = env.Props().get(name)[0]
            if isinstance(thisProp, bpy.types.Collection):
                all_objects = bpy.data.collections[name].all_objects
            elif isinstance(thisProp, bpy.types.Object):
                all_objects = env.Props().get_children(name)

            all_objects = [o for o in all_objects if o.type == 'MESH']
            for obj in all_objects:
                for attr in attrs:
                    p.append([obj.name, frame, attr, list(getattr(obj, attr))])

    p = pd.DataFrame(p, columns=list(columns))
    if isinstance(fname, str):
        p.to_excel(fname, index=False, sheet_name=sheet_name)
    return p

# Insert data from an excel file into keyframes (counterpart of readattr)
def animate_simple(anim_data, columns=None, propfunc=None):
    """
    Simple keyframe animation in blender. 

    :param anim_data: (pandas.DataFrame)
        A pandas data frame with four columns
    :param columns: (list of strings)
        Pandas data frame is typically read from an excel file with these four columns
          - object <str> name of the object in blender
          - keyframe <int> frame number
          - attribute <str> attribute name, such as location, rotation_euler, scale
          - value <list> 3-element list in the case of location, rotation_euler and scale
    :param propfunc: (types.FunctionType)
        Function used to create an object if it does not exist
        Default: create a uv sphere
        Use functools.partial to pass default arguments to your favorite creation function.
        The object name is drawn from the excel file.
        Note: 
            If you supply 'msh_name' argument, then the same mesh will be used for all the objects created.
                propfunc=functools.partial(new.sphere, **{'coll_name':'Points', 'msh_name':'sph', 'u':16, 'v':8, 'r':0.1})
            If not, the mesh name is same as the object name.
                propfunc=functools.partial(new.sphere, **{'coll_name':'Points', 'u':16, 'v':8, 'r':0.1})
    Result:
        keyframe animation in the blend file
    
    Example:
        (load skeletalSystem_originAtCenter_bkp02.blend)
        fname = 'D:\\Workspace\\blenderPython\\apps\\anatomy\\nutations.xlsx'
        bpn.io.animate_simple(fname)
    """
    def get_obj_list(obj_name):
        prop_list = env.Props().get(obj_name) 
        if len(prop_list) > 1: # multiple props detected, only keep objects
            prop_list = [o for o in prop_list if isinstance(o, bpy.types.Object)]
        return prop_list

    if propfunc is None:
        propfunc = functools.partial(new.sphere, **{'coll_name':'Points', 'u':16, 'v':8, 'r':0.1})

    if columns is None:
        columns = ['object', 'keyframe', 'attribute', 'value']

    if isinstance(anim_data, str):
        if os.path.isfile(anim_data):
            anim_data = pd.read_excel(anim_data, sheet_name='animation')

    assert isinstance(anim_data, pd.DataFrame)
    for i in np.arange(0, len(anim_data)):
        this_obj_name = anim_data.iloc[i][columns[0]] # columns[0] = 'object'
        prop_list = get_obj_list(this_obj_name)
        
        if not prop_list: # object doesn't exist in the scene, create it!
            if isinstance(propfunc, functools.partial):
                inp_dict = [a[1] for a in inspect.getmembers(propfunc) if a[0] == 'keywords'][0]
                if 'msh_name' in inp_dict:
                    this_msh_name = inp_dict['msh_name']
                else: # if msh_name is not present, create a new mesh for each object
                    this_msh_name = this_obj_name

            propfunc(obj_name=this_obj_name, msh_name=this_msh_name)
            prop_list = get_obj_list(this_obj_name)
        
        assert len(prop_list) == 1 # there should really only be one object with that name

        obj = prop_list[0] 
        frame = anim_data.iloc[i][columns[1]] # columns[1] = 'keyframe'
        attr = anim_data.iloc[i][columns[2]]  # columns[2] = 'attribute'
        val = anim_data.iloc[i][columns[3]]   # columns[3] = 'value'
        if isinstance(val, str):
            val = eval(val) # pylint: disable=eval-used
        bpy.context.scene.frame_set(frame)
        setattr(obj, attr, val)
        obj.keyframe_insert(data_path=attr, frame=frame)
