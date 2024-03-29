"""
Core of the blender python module.

'Thing' is a wrapper around a blender prop (e.g., meshes, objects, materials, etc bpy.data.*)
Wrappers add functionality to a blender prop. They also:
1) provide easy access to blender props through calling thing() will retrieve a blender prop
2) maintain their internal states by using a database (ThingDB)
    - a new 'Thing' is created only if it doesn't already exist in the database
"""
import functools
import json
import math
import os
import copy

import numpy as np
import blinker
from matplotlib.pyplot import rcParams
COLOR_LIST = rcParams['axes.prop_cycle'].by_key()['color']

import pntools as pn

import bpy #pylint: disable=import-error
import bmesh #pylint: disable=import-error
import mathutils #pylint: disable=import-error
from io_mesh_stl.stl_utils import write_stl #pylint: disable=import-error

from bpn import new, utils, trf

class _ThingDB(dict):
    """
    Database of things.
    With this database, the dispatcher returns the same python object.
    a = new.empty('emp')
    a is utils.get('emp') # True if this is working.

    Something similar will be useful to keep track of handlers and relationships between objects.
    """
    def clean(self):
        """Remove objects not in blender's environment."""
        for coll in self.values():
            for thing in coll:
                if not self.thing_in_blend(thing):
                    self.remove(thing) # remove from database
    def thing_in_blend(self, thing):
        """Return True if thing is in blender's environment."""
        try:
            thing()
            return True
        except KeyError:
            return False
    def remove(self, thing):
        """Remove an object from database"""
        self[thing.__class__.__name__] = [t for t in self[thing.__class__.__name__] if t.name != thing.name]
    def add(self, thing):
        """
        Add a thing to the database. DOES NOT CHECK IF IT ALREADY EXISTS.
        The parent class of this module 'Thing' tries to retrieve an object, 
        and summons this add functionality if the retrieval fails.
        """
        self[thing.__class__.__name__].append(thing)
    def retrieve(self, thing_name, cls_name):
        """If thing_name of class cls_name is in the database, return it. Else return None"""
        this_class_objs = self.setdefault(cls_name, [])
        this_class_dict = {t.name: t for t in this_class_objs}
        if thing_name in this_class_dict:
            thing = this_class_dict[thing_name]
            if self.thing_in_blend(thing):
                # a retrieved object must exist in blender's environment (if not, create a new one)
                return thing
            self.remove(thing)
        return None

ThingDB = _ThingDB()


class _HandlerDB(blinker.base.Namespace):
    """
    Create a separate namespace for handlers in the bpn core class
    handler id blueprint: mode-module-class-attribute(instance)
    """
    def delete_receivers(self):
        """Remove all receivers"""
        for s in self:
            self.signal(s).receivers = {}
    def split_keys(self, ret_vals=None):
        """Split each key into meaningful parts, and return as a list of tuples"""
        ret = {}
        if ret_vals is None:
            ret_vals = ['mode', 'module', 'class', 'attr', 'instance']
        for k in self:
            idd = pn.handler_id2dict(k)
            ret[tuple([idd[r] for r in ret_vals])] = k
        return ret

HandlerDB = _HandlerDB()


class Thing:
    """
    Wrapper around blender's bpy.data.*
    args are exclusively meant for the new() method.
    kwargs are attributes of the thing being created.
    Example:
        key_light = core.Thing('Key', 'Light', 'SUN', energy=2.5, angle=0.2, color=(0., 0., 0.))
    """
    def __new__(cls, thing_name, *args, **kwargs): #pylint: disable=unused-argument
        if hasattr(thing_name, 'name'):
            thing_name = thing_name.name
        # retrieve instance if it exists
        this_instance = ThingDB.retrieve(thing_name, cls.__name__)
        if not this_instance:
            this_instance = super().__new__(cls) # make a new instance
            ThingDB.add(this_instance) # add it to the database
            return this_instance # send it for initialization
        # Create a new instance if it doesn't exist
        return this_instance
        
    def __init__(self, thing_name, thing_type, *args, **kwargs):
        if isinstance(thing_type, str):
            thing_type = utils.bpy_type(thing_type)
        if isinstance(thing_name, thing_type):
            thing_name = thing_name.name # in case you passed the object itself - don't do this!
        if len(args) >= 1 and isinstance(args[0], Thing): # if you passed core.Mesh instead of bpy.types.Mesh when creating an object
            args = list(args)
            args[0] = args[0]()
            args = tuple(args)
    
        self.blend_name = thing_name
        self.blend_type = thing_type # bpy.types.Object

        # if it is not in the blend_coll, create a new one
        if thing_name not in [t.name for t in self.blend_coll]:
            self.blend_coll.new(thing_name, *args)
        
        for key, val in kwargs.items():
            setattr(self(), key, val)

    @property
    def blend_coll(self): # bpy.data.objects, bpy.data.meshes
        """Get the blender collection on demand."""
        return getattr(bpy.data, utils.bpy_coll_name(self.blend_type))

    def __call__(self):
        """Return the blender object."""
        return self.blend_coll[self.blend_name]
    
    def __neg__(self):
        """Remove that object."""
        # remove from blender (if it is there)
        try:
            self.blend_coll.remove(self())
        except KeyError:
            pass
        # remove from local database
        ThingDB.remove(self)

    def __str__(self):
        return object.__repr__(self)
    
    def __repr__(self):
        return self.__module__+"."+self.__class__.__name__+"('"+self.name+"')"
    
    @property
    def name(self):
        """Return the name in blender. It is important to set the name through this setter for chaning names."""
        return self.blend_name
    
    @name.setter
    def name(self, new_name):
        if new_name != self().name:
            new_name_checked = utils.new_name(new_name, [t.name for t in self.blend_coll]) # in case you rename it to something that is already present
            self().name = new_name_checked
            self.blend_name = new_name_checked
            if new_name_checked != new_name:
                print(new_name+' already present. Used '+new_name_checked)

    def add_handler(self, attr, receiver_func, mode='post'):
        """Add an event handler"""
        h = pn.Handler(self, attr, mode, HandlerDB.signal)
        h.broadcast()
        h.add_receiver(receiver_func)
        return h

    @property
    def handlers(self):
        """Return a list of pn.Handler objects associated with this thing"""
        h_ref = pn.Handler(self, 'name') # dummy handler
        class Ret(list):
            """Change the list representation for handlers to summarize handlers nicely. Debug/summary tool."""
            def __repr__(self):
                ret_str = ''
                for h in self:
                    ret_str += h.__repr__() + '\n\n'
                return ret_str
        ret = Ret()
        # add object-level handlers
        h_ref_desc = (h_ref.mod_name, h_ref.instance_name)
        signal_id_list = [pn.handler_id2dict(v) for k, v in HandlerDB.split_keys(['module', 'instance']).items() if k == h_ref_desc]
        ret += [pn.Handler(self, d['attr'], d['mode'], HandlerDB.signal) for d in signal_id_list]
        # add class-level handlers
        h_class_desc = (h_ref.mod_name, h_ref.thing_class.__name__, '')
        signal_id_list = [pn.handler_id2dict(v) for k, v in HandlerDB.split_keys(['module', 'class', 'attr', 'instance']).items() if (k[0], k[1], k[3]) == h_class_desc]
        ret += [pn.Handler(self.__class__, d['attr'], d['mode'], HandlerDB.signal) for d in signal_id_list]
        return ret


class Collection(Thing):
    """Wrapper around a bpy.types.Collection thing"""
    def __new__(cls, name, **kwargs): #pylint: disable=arguments-differ
        return super().__new__(cls, name, **kwargs)

    def __init__(self, name, **kwargs):
        super().__init__(name, 'Collection', **kwargs)
        self.link()
    
    def hide(self):
        """Hide collection from the viewport, and from rendering."""
        bpy.context.scene.view_layers[0].layer_collection.children[self.name].hide_viewport = True
        bpy.context.scene.view_layers[0].layer_collection.children[self.name].exclude = True
    
    def show(self):
        """Show collection in the viewport, and enable rendering."""
        bpy.context.scene.view_layers[0].layer_collection.children[self.name].hide_viewport = False
        bpy.context.scene.view_layers[0].layer_collection.children[self.name].exclude = False
    
    def __getitem__(self, key):
        """
        Try:
            demo.zoo() # create a bunch of objects
            get('zoo')[:]
            get('zoo')['L'] # get object named 'L' from collection 'zoo'
            get('zoo')[0] # get the first object in collection 'zoo' (not recommended)
        """
        all_blobj = self().objects[key]
        if isinstance(all_blobj, bpy.types.ID):
            return utils.enhance(all_blobj)
        return [utils.enhance(o) for o in all_blobj]

    def link(self):
        """Link collection to the current scene"""
        if not self.in_scene:
            bpy.context.scene.collection.children.link(self())
    
    def unlink(self):
        """Unlink collection to the current scene"""
        if self.in_scene:
            bpy.context.scene.collection.children.unlink(self())
    
    @property
    def in_scene(self):
        """Is the collection in the current scene?"""
        return self.name in [c.name for c in bpy.context.scene.collection.children[:]]
    # Group transformations for objects in a collection!


class Object(Thing):
    """
    Wrapper around a bpy.types.Object thing
    args is for new
    kwargs is to set options
    Object('empty_obj', None)

    DOES NOT put it in a collection. That is the job of functions in the new module.
    """
    def __new__(cls, name, *args, **kwargs):
        return super().__new__(cls, name, *args, **kwargs)

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, 'Object', *args, **kwargs)
        # don't over-write internal states if object was retrieved from database
        if not hasattr(self, 'frame_gp'):
            self.frame_gp = None # grease pencil object that displays the frame
        if not hasattr(self, 'frame_orig'):
            self.frame_orig = self.frame

        # internal states determined by blender: re-initialize even if object is retrieved from the database
        self.container = self().parent.name if self().parent else None

        all_constraints = ('CAMERA_SOLVER', 'FOLLOW_TRACK', 'OBJECT_SOLVER', 'COPY_LOCATION', 'COPY_ROTATION', 'COPY_SCALE', 'COPY_TRANSFORMS', 'LIMIT_DISTANCE', 'LIMIT_LOCATION', 'LIMIT_ROTATION', 'LIMIT_SCALE', 'MAINTAIN_VOLUME', 'TRANSFORM', 'TRANSFORM_CACHE', 'CLAMP_TO', 'DAMPED_TRACK', 'IK', 'LOCKED_TRACK', 'SPLINE_IK', 'STRETCH_TO', 'TRACK_TO', 'ACTION', 'ARMATURE', 'CHILD_OF', 'FLOOR', 'FOLLOW_PATH', 'PIVOT', 'SHRINKWRAP')
        self.constraint_list = {cn.lower() : None for cn in all_constraints}
        for con in self().constraints[:]: # if they are already there, then add them to the name list
            self.constraint_list[con.type.lower()] = con.name
        
        all_modifiers = ('DATA_TRANSFER', 'MESH_CACHE', 'MESH_SEQUENCE_CACHE', 'NORMAL_EDIT', 'WEIGHTED_NORMAL', 'UV_PROJECT', 'UV_WARP', 'VERTEX_WEIGHT_EDIT', 'VERTEX_WEIGHT_MIX', 'VERTEX_WEIGHT_PROXIMITY', 'ARRAY', 'BEVEL', 'BOOLEAN', 'BUILD', 'DECIMATE', 'EDGE_SPLIT', 'MASK', 'MIRROR', 'MULTIRES', 'REMESH', 'SCREW', 'SKIN', 'SOLIDIFY', 'SUBSURF', 'TRIANGULATE', 'WELD', 'WIREFRAME', 'ARMATURE', 'CAST', 'CURVE', 'DISPLACE', 'HOOK', 'LAPLACIANDEFORM', 'LATTICE', 'MESH_DEFORM', 'SHRINKWRAP', 'SIMPLE_DEFORM', 'SMOOTH', 'CORRECTIVE_SMOOTH', 'LAPLACIANSMOOTH', 'SURFACE_DEFORM', 'WARP', 'WAVE', 'CLOTH', 'COLLISION', 'DYNAMIC_PAINT', 'EXPLODE', 'FLUID', 'OCEAN', 'PARTICLE_INSTANCE', 'PARTICLE_SYSTEM', 'SOFT_BODY', 'SURFACE')
        self.modifier_list = {mod.lower() : None for mod in all_modifiers}
        for mod in self().modifiers[:]: # if they are already there, then add them to the modifier list
            self.modifier_list[mod.type.lower()] = mod.name

    @property
    def frame(self):
        """Object frame expressed as trf.CoordFrame"""
        return trf.CoordFrame(self().matrix_world, unit_vectors=False)
    
    @frame.setter
    def frame(self, new_frame):
        m = new_frame.m if isinstance(new_frame, trf.CoordFrame) else new_frame
        self().matrix_world = mathutils.Matrix(m)
        bpy.context.view_layer.update()

    def frame_reset(self):
        """Reset matrix_world to what it was when created."""
        self.frame = self.frame_orig

    @property
    def normal(self):
        """By definition, normal is the z-direction."""
        return self.frame.k

    @normal.setter
    def normal(self, new_normal):
        """
        Only direction information is taken from new_normal. To scale,
        explicitly set the scale, or use the scale transform.
        """
        new_normal = np.array(new_normal)
        assert len(new_normal) == 3
        # Using Quaternions
        n1 = trf.norm_vec(self.normal)
        n2 = trf.norm_vec(new_normal)
        q = trf.Quat(np.cross(n1, n2), np.arccos(np.dot(n1, n2)), trf.CoordFrame(origin=self.frame.origin))
        self.frame = q*self.frame # quaternion direction specified in world frame, origin at origin of the object
        bpy.context.view_layer.update()

    def show_frame(self, name=None, **kwargs):
        """
        Display the coordinate frame.
        Create one if it does not exist.
        Update if it exists.
        """
        names, kwargs = utils.clean_names(name, kwargs, {
            'gp_name': 'Frame',
            'obj_name': self.name+'_frame',
            'coll_name': 'CoordFrames',
            'layer_name': 'crd',
            'priority_obj': 'new',
            'priority_gp': 'new'
            }, 'gp')
        kwargs, _ = pn.clean_kwargs(kwargs, {
            'palette_list': ['blender_ax'], 
            'palette_prefix': [''],
            'palette_alpha': [0.8],
            'line_width': 80,
            'scale': 1,
            })
        pcf = trf.CoordFrame(self.frame.m, unit_vectors=True).as_points().transform(trf.scaletf(kwargs['scale']), self.frame.m)
        if self.frame_gp is None:
            self.frame_gp = new.pencil(name, **{**names, **kwargs})
        for cnt in (0, 1, 2):
            this_stroke_name = self.frame_gp.data.layer.info+'_key{:04d}'.format(self.frame_gp.data.keyframe.frame_number)+'_stroke{:03d}'.format(cnt)
            this_stroke = [stroke for key_name, stroke in self.frame_gp.strokes.items() if key_name == this_stroke_name]
            if this_stroke:
                this_stroke[0].points.foreach_set('co', pcf.co[[0, cnt+1]].flatten())
            else:
                self.frame_gp.stroke(trf.PointCloud(pcf.co[[0, cnt+1]], np.eye(4)), color='crd_'+('i', 'j', 'k')[cnt], line_width=kwargs['line_width']*kwargs['scale'])
        self.frame_gp().update_tag()
        return self.frame_gp

    # transformations
    @property
    def loc(self):
        """Object location (not mesh!)"""
        return np.array(self().matrix_world.translation) # so you can do += 1
    @loc.setter
    def loc(self, new_loc):
        assert np.size(new_loc) == 3
        self().location = mathutils.Vector(new_loc)
        bpy.context.view_layer.update()

    @property
    def rot(self):
        """Object rotation"""
        return self().rotation_euler
    @rot.setter
    def rot(self, theta):
        self().rotation_euler.x = theta[0]
        self().rotation_euler.y = theta[1]
        self().rotation_euler.z = theta[2]
        bpy.context.view_layer.update()

    @property
    def scl(self):
        """Object scale"""
        return self().scale
    @scl.setter
    def scl(self, s):
        if isinstance(s, (int, float)):
            s = np.array([1, 1, 1])*s
        else:
            assert np.size(s) == 3
            self().scale = mathutils.Vector(s)
        bpy.context.view_layer.update()

        self().scale = mathutils.Vector(s)
        bpy.context.view_layer.update()

    # object transforms - update view_layer after any transform operating on the object (bo)
    def translate(self, delta=0, x=0, y=0, z=0):
        """
        Move an object by delta.
        delta is a 3-element tuple, list, numpy array or Vector
        sph.translate((0, 0, 0.6))
        sph.translate(z=0.6)
        """
        if 'numpy' in str(type(delta)):
            delta = tuple(delta)
        if delta == 0:
            delta = (x, y, z)
        assert len(delta) == 3
        self().location = self().location + mathutils.Vector(delta)
        bpy.context.view_layer.update()
        return self
    
    def rotate(self, theta, inp_type='degrees', frame='global'):
        """
        Rotate an object.
        theta is a 3-element tuple, list, numpy array or Vector
        inp_type is 'degrees' (default) or 'radians'
        frame of reference is either 'global' or 'local'
        """
        assert len(theta) == 3
        if inp_type == 'degrees':
            theta = [math.radians(θ) for θ in theta]
        if frame == 'local':
            self().rotation_euler.x = self().rotation_euler.x + theta[0]
            self().rotation_euler.y = self().rotation_euler.y + theta[1]
            self().rotation_euler.z = self().rotation_euler.z + theta[2]
        else: #frame = global
            self().rotation_euler.rotate(mathutils.Euler(tuple(theta)))
        bpy.context.view_layer.update()
        return self

    def scale(self, delta):
        """
        Scale an object.
        delta is a 3-element tuple, list, numpy array or Vector
        """
        if isinstance(delta, (int, float)):
            self().scale = self().scale*float(delta)
        else:
            assert np.size(delta) == 3
            self().scale = mathutils.Vector(np.array(delta)*np.array(self().scale))
        bpy.context.view_layer.update()
        return self

    # animation
    def hide(self, keyframe=None):
        """Hide object at keyframe."""
        if keyframe is None:
            keyframe = bpy.context.scene.frame_current
        self().hide_render = True
        self().keyframe_insert('hide_render', frame=keyframe)
        self().hide_viewport = True
        self().keyframe_insert('hide_viewport', frame=keyframe)
    
    def show(self, keyframe=None):
        """Show object at keyframe."""
        if keyframe is None:
            keyframe = bpy.context.scene.frame_current
        self().hide_render = False
        self().keyframe_insert('hide_render', frame=keyframe)
        self().hide_viewport = False
        self().keyframe_insert('hide_viewport', frame=keyframe)
    
    def key(self, frame=None, target='lrs', values=None):
        """
        Easy keying. Useful for playing around in the command line, or iterating ideas while keeping history.
        :param frame: (int) Uses current frame number if nothing is specified.
        :param target: (str) recommended use - one of 'l', 'r', 's', 'lrs', 'lr', 'ls', 'rs'
        :param values: (list) each element of the list should be a 3-tuple
            If you have only one parameter to change, still supply [(1, 2, 3)] instead of (1, 2, 3)

        Note that if values are not specified, current numbers will be used.
        Example:
            s = bpn.new.sphere(name='sphere')
            s.key(1)
            s.loc = (2, 2, 2) # this location will be keyed into frame 26!
            s.key(26)
            s.scl = (1, 0.2, 1)
            s.key(51)
        """
        assert isinstance(target, str)
        target = target.lower()

        if target in ['l', 'loc', 'location']:
            attrs = ['location']
        if target in ['r', 'rot', 'rotation', 'rotation_euler']:
            attrs = ['rotation_euler']
        if target in ['s', 'scl', 'scale']:
            attrs = ['scale']
        if target in ['lrs', 'locrotscale', 'locrotscl']:
            attrs = ['location', 'rotation_euler', 'scale']
        if target in ['lr', 'locrot']:
            attrs = ['location', 'rotation_euler']
        if target in ['ls', 'locscl', 'locscale']:
            attrs = ['location', 'rotation_euler']
        if target in ['rs', 'rotscl', 'rotscale']:
            attrs = ['rotation_euler', 'scale']

        if not frame:
            frame = bpy.context.scene.frame_current

        if values is None:
            for attr in attrs:
                self().keyframe_insert(data_path=attr, frame=frame)
            return self
        
        for attr, value in zip(attrs, values):
            setattr(self(), attr, value)
            self().keyframe_insert(data_path=attr, frame=frame)

        return self # so you can chain keyings into one command
    
    @property
    def coll(self):
        """
        Collection of the object.
        If the object is in multiple collections, return the last one
        """
        this_coll = self().users_collection
        if not this_coll: # orphan object not linked to the scene
            return this_coll
        return Collection(this_coll[-1].name)

    def to_coll(self, coll_name, typ='move'):
        """
        Move this object to a collection.

        :param coll_name: (str)
            A collection will be created if a collection by coll_name doesn't exist
        :param typ: (str) 'copy' or 'move'
            Note that copy won't copy the object itself. It will simply keep the same object in both collections. 
            Use core.Object.copy or core.Object.deepcopy to achieve this.
        """
        assert isinstance(coll_name, (bpy.types.Collection, str))
        assert typ in ['copy', 'move']
        oldC = self.coll
        if not isinstance(coll_name, str):
            coll_name = coll_name.name
        if coll_name not in [c.name for c in bpy.data.collections]:
            # creates a new collection and links it to the current scene if it doesn't exist
            newC = Collection(coll_name)()
        else:
            # if the collection exists and is not linked to the scene, it will remain unlinked.
            newC = bpy.data.collections[coll_name]        
        if coll_name not in [c.name for c in self().users_collection]: # link only if the object isn't in collection already
            newC.objects.link(self())
            if typ == 'move' and oldC: # if it was part of a collection
                oldC().objects.unlink(self())
    
    def in_coll(self, coll_name):
        """
        Put the same object in another collection.
        Does NOT make a copy of the object. See copy and deepcopy for that.
        Useful for putting the object in RigidBodyWorld collection.
        """
        self.to_coll(coll_name, 'copy')
    
    # modifiers
    def get_modifier(self, modifier_type):
        """Returns bpy.types.Modifier, or makes a new one if a modifier does not exist."""
        if self.modifier_list[modifier_type.lower()] is not None:
            return self().modifiers[self.modifier_list[modifier_type.lower()]]
        modifier_name = modifier_type.lower().replace('_', ' ').title()
        return self().modifiers.new(modifier_name, modifier_type.upper())

    def subsurf(self, levels=2, render_levels=3, **kwargs):
        """Subdivision surface modifier."""
        # get a subsurf modifier if it already exists
        subsurf_modifier = self.get_modifier('subsurf')
        
        # update important attributes
        subsurf_modifier.levels = levels
        subsurf_modifier.render_levels = render_levels

        # update optional attributes
            # kwargs_other: if you didn't specify, don't change
            # kwargs_impose: if you didn't specify, impose a certain value
        kwargs_impose, kwargs_keep = pn.clean_kwargs(kwargs, {
            'subdivision_type' : 'CATMULL_CLARK' #('CATMULL_CLARK', 'SIMPLE')
        })
        for key, val in {**kwargs_impose, **kwargs_keep}.items():
            setattr(subsurf_modifier, key, val)

        # update modifier list
        self.modifier_list['subsurf'] = subsurf_modifier.name

    # constraints
    def get_constraint(self, constraint_type):
        """Returns the bpy.types.Constraint, or makes a new one if a constraint doesn't exist."""
        if self.constraint_list[constraint_type.lower()] is not None:
            return self().constraints[self.constraint_list[constraint_type.lower()]]
        return self().constraints.new(constraint_type.upper())

    def follow_path(self, path_obj=None, **kwargs):
        """
        Add a FOLLOW PATH constraint to parametrically control object flow.
        obj.follow_path(r=3) to add a bezier circle path constraint
        obj.follow_path(functools.partial(new.bezier, r=3)) also does the same.
        Give any function or partial that returs a bpy.types.Object of type CURVE, OR its wrapper, core.Object
        """
        if path_obj is None:
            path_obj = functools.partial(new.bezier_circle, r=kwargs['r'] if 'r' in kwargs else 2)
        if isinstance(path_obj, functools.partial) or type(path_obj).__name__ == 'function': # give a function or a partial function that returns a core.Object or a bpy.types.Object of type CURVE
            path_obj = path_obj(curve_name=self.name+'Path', obj_name=self.name+'_path', coll_name=self().users_collection[0].name)
        if isinstance(path_obj, Thing):
            path_obj = path_obj()
        assert isinstance(path_obj, bpy.types.Object)
        assert path_obj.type == 'CURVE'

        path_constraint = self.get_constraint('follow_path')
        path_constraint.target = path_obj
        kwargs, _ = pn.clean_kwargs(kwargs, {
            'use_curve_follow': True,
            'use_curve_radius': False,
            'use_fixed_location': True,
            'up_axis': 'UP_Z', # ('UP_X', 'UP_Y', 'UP_Z')
            'forward_axis': 'FORWARD_Y', # ('FORWARD_X', 'FORWARD_Y', 'FORWARD_Z', 'TRACK_NEGATIVE_X', 'TRACK_NEGATIVE_Y', 'TRACK_NEGATIVE_Z')
        })
        for key, val in kwargs.items():
            setattr(path_constraint, key, val)
        self.constraint_list['follow_path'] = path_constraint.name
    
    def track_to(self, targ_obj, **kwargs):
        """
        Add a TRACK TO constraint
        """
        if isinstance(targ_obj, Thing):
            targ_obj = targ_obj()
        assert isinstance(targ_obj, bpy.types.Object)

        track_constraint = self.get_constraint('track_to')
        track_constraint.target = targ_obj
        kwargs, _ = pn.clean_kwargs(kwargs, {
            'up_axis': 'UP_Y', # ('UP_X', 'UP_Y', 'UP_Z')
            'track_axis': 'TRACK_NEGATIVE_Z', # ('TRACK_X', 'TRACK_Y', 'TRACK_Z', 'TRACK_NEGATIVE_X', 'TRACK_NEGATIVE_Y', 'TRACK_NEGATIVE_Z')
        })
        for key, val in kwargs.items():
            setattr(track_constraint, key, val)
    
    def copy(self, obj_name=None, coll_name=None):
        """
        Make a copy of the object, keep the same mesh and put it in the same collection.
        Use the same animation data!
        """
        this_o = Object(self().copy().name) # copy object data
        if isinstance(obj_name, str): # rename
            this_o.name = obj_name
        if isinstance(coll_name, str):
            this_o.to_coll(coll_name)
        else: # put it in the same collection
            curr_coll = self.coll
            if self.coll:
                this_o.to_coll(curr_coll.name)
        return this_o

    def deepcopy(self, obj_name=None, coll_name=None, msh_name=None):
        """
        Make a copy of everything - object, mesh and animation
        """
        this_o = self.copy(obj_name=obj_name, coll_name=coll_name)
        this_o().data = this_o().data.copy()
        if isinstance(msh_name, str):
            this_o.data.name = msh_name
        return utils.enhance(this_o())


class Mesh(Thing):
    """Wrapper around a bpy.types.Mesh object."""
    def __new__(cls, name, **kwargs): #pylint: disable=arguments-differ
        return super().__new__(cls, name, **kwargs)

    def __init__(self, name, **kwargs):
        super().__init__(name, 'Mesh', **kwargs)
        # Don't overwrite internal states if object was retrieved from database
        if not hasattr(self, 'v_init'):
            self.v_init = copy.deepcopy(self.v)
        if not hasattr(self, 'v_bkp'):
            self.v_bkp = copy.deepcopy(self.v)
    
    @property
    def v(self):
        """Coordinates of a mesh as an nVx3 numpy array."""
        return np.array([v.co for v in self().vertices])
    
    @v.setter
    def v(self, thisCoords):
        """
        Set vertex positions of a mesh using a numpy array of size nVertices x 3.
        Note that this will only work when blender 3D viewport is in object mode.
        Therefore, this code will temporarily change the 3D viewport mode to Object,
        change the mesh coordinates and switch it back.
        """
        self.v_bkp = copy.deepcopy(self.v) # for undo
        for vertexCount, vertex in enumerate(self().vertices):
            vertex.co = mathutils.Vector(thisCoords[vertexCount, :])
        bpy.context.view_layer.update()
    
    @property
    def vertex_center(self):
        """
        Return the center of all vertices.
        This was originally 'center' which was confusing.
        """
        return np.mean(self.v, axis=0)

    @vertex_center.setter
    def vertex_center(self, new_center):
        self.v = self.v + new_center - self.vertex_center

    @property
    def vn(self):
        """Vertex normals as an nVx3 numpy array."""
        return np.array([vert.normal[:] for vert in self().vertices])
    
    @property
    def f(self):
        """Faces as an nFx3 numpy array."""
        return np.array([polygon.vertices[:] for polygon in self().polygons], dtype=object)

    @property
    def fn(self):
        """Face normals as an nFx3 numpy array."""
        return np.array([polygon.normal[:] for polygon in self().polygons])
        
    @property
    def fa(self):
        """Area of faces as an nFx3 numpy array."""
        return np.array([polygon.area for polygon in self().polygons])
    
    @property
    def fc(self):
        """Coordinates of face centers."""
        return np.array([polygon.center for polygon in self().polygons])

    @property
    def e(self):
        """Vertex indices of edges."""
        return np.array([edge.vertices[:] for edge in self().edges])

    @property
    def eL(self):
        """Edge lengths."""
        e = self.e
        v = self.v
        # This will take forever! Need a better way
        return [np.sqrt(np.sum(np.diff(v[k], axis=0)**2)) for k in e]

    @property
    def nV(self):
        """Number of vertices."""
        return np.shape(self.v)[0]

    @property
    def nF(self):
        """Number of faces."""
        return np.shape(self.f)[0]

    @property
    def nE(self):
        """Number of edges."""
        return np.shape(self.e)[0]

    def undo(self):
        """
        Undo the last change to coords.
        Repeated application of undo will keep switching between the
        last two views.
        """
        self.v, self.v_bkp = self.v_bkp, self.v

    def reset(self):
        """Reset the mesh to its initalized state"""
        self.v = self.v_init

    def inflate(self, pres=0.2, elas=0.1, delta=0.05, nIter=20):
        """
        Inflate a mesh towards a sphere

        Try this sequence on Suzanne:
        m.inflate(0.2, 0.1, 0.05, 300)
        m.inflate(0.02, 0.1, 0.01, 300)
        m.inflate(0.05, 0.1, 0.01, 300)
        m.inflate(0.1, 0.1, 0.01, 300)
        m.inflate(0.15, 0.1, 0.02, 600)

        Don't normalize pressure vector by area:
        F_p = np.sum(fn[tNei[i]], 0)
        Then, try
        m.inflate(1, 0.1, 0.5, 150)
        """
        newV = self.v
        f = self.f
        e = self.e
        nV = self.nV

        fnv = [self.fnv(f, i) for i in range(nV)] # face neighbors of vertices
        vnv = [self.vnv(e, i) for i in range(nV)] # vertex neighbors of vertices
        for _ in range(nIter):
            fn = self.fn
            fa = self.fa
            for i in range(self.nV):
                F_el = np.sum(newV[vnv[i]] - newV[i], 0) # elastic force vector
                F_p = np.sum(fn[fnv[i]].T*fa[fnv[i]], 1) # pressure force vector
                F = elas*F_el + pres*F_p # sum of elastic and pressure forces
                newV[i] = newV[i] + delta*F
            self.v = newV
        
    def fnv(self, f, i):
        """Face neighbors of a vertex i.
        Faces attached to vertex i, given faces f."""
        return np.flatnonzero(np.sum(f == i, 1))
    
    def vnv(self, e, i):
        """Vertex neighbors of vertex i.
        Vertex indices attached to vertex i, given edges e."""
        return [np.setdiff1d(k, i)[0] for k in e if i in k]

    def export(self, fName=None, fPath=None):
        """
        Export a core.Mesh instance into an stl file.
        REMEMBER: This only works if the mesh has ONLY triangular faces.
        """
        if fPath is None:
            fPath = utils.PATH['cache']

        if fName is None:
            fName = self().name + '.stl'

        if fName.lower()[-4:] != '.stl':
            print('File name should end with a .stl')
            return

        # if the full path is supplied as the first argument
        if os.path.dirname(fName):
            if os.path.exists(os.path.dirname(fName)):
                fPath = os.path.dirname(fName)
        fName = os.path.basename(fName)

        # generate faces for blender's write_stl function
        # faces: iterable of tuple of 3 vertex, vertex is tuple of 3 coordinates as float
        # faces = [f1: (v1:(p11, p12, p13), v2:(p21, p22, p23), v3:(p31, p32, p33)), f2:...]
        # poke faces that have more than 3 coordinates (only for saving)
        tmp_self_flag = False
        if any([np.size(x) > 3 for x in self.f]): # if not every face is a 3-gon, then poke faces
            tmp_self_flag = True
            tmp_self = Mesh(self().copy())
            bm = bmesh.new()
            bm.from_mesh(tmp_self())
            # only poke a face if it has more than 3 vertices
            bmesh.ops.poke(bm, faces=[x for x in bm.faces if len(x.verts[:]) > 3])
            bm.to_mesh(tmp_self())
            bm.free()

        v = [tuple(v.co) for v in tmp_self().vertices]
        f = [tuple(polygon.vertices[:]) for polygon in tmp_self().polygons]

        faces = []
        for face in f:
            thisFace = []
            for vPos in face:
                thisFace.append(v[vPos])
            faces.append(tuple(thisFace))
        write_stl(filepath=os.path.join(fPath, fName), faces=faces, ascii=False)
        if tmp_self_flag:
            -tmp_self
    
    def morph(self, n_frames=50, frame_start=1, v_orig=None, v_targ=None):
        """
        Morphs the mesh from initial vertex positions to current vertex positions.
        CAUTION: Using this multiple times on the same object can cause unpredictable behavior.
        """
        if v_orig is None:
            v_orig = self.v_init
        if v_targ is None:
            v_targ = self.v
        frame_end = frame_start + n_frames
        def my_handler(scene):
            p = (scene.frame_current-frame_start)/(frame_end-frame_start)
            self.v = (1-p)*v_orig + p*v_targ
        my_handler.__doc__ = self.name # so we know which object the handler belongs to
        bpy.app.handlers.frame_change_pre.append(my_handler)
        return my_handler

    def morph_clear(self, morph_handler=None):
        """
        Remove all morphs for this object.
        Remove only the morph specified by morph_handler (only if belongs to this MeshObject) 
        """
        if morph_handler is None:
            # clear all handlers related to this object
            mark_for_removal = []
            for hdl in bpy.app.handlers.frame_change_pre:
                if hdl.__doc__ == self.name:
                    mark_for_removal.append(hdl)
            for hdl in mark_for_removal:
                bpy.app.handlers.frame_change_pre.remove(hdl)
        elif morph_handler.__doc__ != self.name:
            # only clear the handler if it was related to this object
            print("The handler belongs to " + morph_handler.__doc__ + ". Not clearing")
            return
        else:
            print("Unaccounted scenario!")
    
    def update_normals(self):
        """Update face normals (for example, when updating the point locations!)"""
        bm = bmesh.new()
        bm.from_mesh(self())
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(self())
        bm.clear()
        self().update()
        bm.free()
    
    def shade(self, typ='smooth'):
        """
        Easy access to set shading.
        Extend this to mark sharpe edges, and define smoothing only for some faces
        """
        assert typ in ('smooth', 'flat')
        poly_smooth = typ == 'smooth'
        for p in self().polygons:
            p.use_smooth = poly_smooth


class CompoundObject(Object):
    """
    Blender has different types of objects.
    This class enables accessing 'wrapped' data.
    For example, a mesh object's data will be wrapped with the Mesh class
    https://docs.blender.org/manual/en/latest/scene_layout/object/types.html
    """
    def __new__(cls, name, obj_type, *args, **kwargs): #pylint: disable=unused-argument
        if name in [o.name for o in bpy.data.objects]:
            # If an object with that name exists in the blender env, assert that it is the correct type
            # the 'new' module should ensure this doesn't happen, so this is here as an additional check
            assert bpy.data.objects[name].type == obj_type
        return super().__new__(cls, name, *args, **kwargs)

    def __init__(self, name, obj_type, data_class, *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        assert self().type == obj_type
        self._data_class = data_class
        if args and isinstance(args[0], data_class):
            self._data = args[0]
        else:
            self._data = data_class(self().data)
    
    def __neg__(self):
        super().__neg__()
        self.data.__neg__()

    @property
    def data(self):
        """Mesh data. Initalized at the time of object creation."""
        return self._data

    @data.setter
    def data(self, new_data):
        if not isinstance(new_data, str):
            assert hasattr(new_data, 'name')
            new_data = new_data.name
        self._data = self._data_class(new_data)
        self().data = self.data() # pylint:disable=not-callable # replace the blender data
        bpy.context.view_layer.update()


@pn.PortProperties(Mesh, 'data') # instance of MeshObject MUST have 'data' attribute/property that is an instance of Mesh class
class MeshObject(CompoundObject):
    """
    This is a core.Object. Automatically calls the appropriate methods
    and properties from Object and Mesh classes.
    For example:
        new.sphere('sph')
        s = MeshObject('sph')
        s.v -> automatically returns vertices from them mesh
    """
    def __new__(cls, name, *args, **kwargs):
        return super().__new__(cls, name, 'MESH', *args, **kwargs)

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, 'MESH', Mesh, *args, **kwargs)

    @property
    def pts(self):
        """Return vertices as a trf.PointCloud object."""
        return trf.PointCloud(self.data.v, self.frame)

    @pts.setter
    def pts(self, new_pts):
        """
        Set the vertices AND the frame. In other words, transform the
        point cloud into the desired frame of reference before putting
        it here.
        """
        assert isinstance(new_pts, trf.PointCloud)
        self.data.v = new_pts.co
        self.frame = new_pts.frame
    
    def apply_matrix(self):
        """
        Apply world transformation coordinates to the mesh vertices.
        CAUTION: Applies matrix to the MESH directly and NOT the object!!
        It also resets matrix_world
        Note that this move will move the mesh center to origin.
        """
        bpy.context.view_layer.update()
        self.data.v_bkp = self.data.v # for undoing
        self.data.v = trf.apply_matrix(self().matrix_world, self.data.v)
        self().matrix_world = mathutils.Matrix(np.eye(4))
        bpy.context.view_layer.update()
        return self

    def apply_modifiers(self):
        """
        Make a copy of the object by applying all the modifiers
        """
        dg = bpy.context.evaluated_depsgraph_get()
        self_eval = self().evaluated_get(dg)
        m = bpy.data.meshes.new_from_object(self_eval)
        self_mod = utils.enhance(bpy.data.objects.new(self.name+'_mod', m))
        self_mod.to_coll(self.coll.name)
        return self_mod

    def slice_ax(self, axis='x', slice_dir='neg'):
        """
        Use a plane as a slicer and set all vertices below it to zero.
        """
        assert slice_dir in ('pos', 'neg')
        if isinstance(axis, str):
            axis = {'x':0, 'y':1, 'z':2}[axis]
        self.data.v_bkp = self.data.v

        # apply matrix, do your thing, apply inverse, then put the original matrix back in
        m = self().matrix_world.copy()
        mi = m.copy()
        mi.invert()
        self.apply_matrix()

        v = self.data.v
        if slice_dir == 'neg':
            v[v[:, axis] < 0, axis] = 0
        else: 
            v[v[:, axis] > 0, axis] = 0
        self.data.v = v

        self().matrix_world = mi
        self.apply_matrix()
        self().matrix_world = m
        bpy.context.view_layer.update()
        return self

    slice_x = functools.partialmethod(slice_ax, axis='x')
    slice_y = functools.partialmethod(slice_ax, axis='y')
    slice_z = functools.partialmethod(slice_ax, axis='z')

    def groups(self, vert_attr='co', sav_name=None, ret_type=None):
        """Return a dictionary of vertex group names : vertex attribute (e.g. coordinates)"""
        ret = {g.name: [] for g in self().vertex_groups}
        group_index_to_name = {g.index:g.name for g in self().vertex_groups}
        if ret_type is None:
            if vert_attr == 'index':
                ret_type = int
            else:
                ret_type = list
        for v in self().data.vertices:
            for g in v.groups:
                ret[group_index_to_name[g.group]].append(ret_type(getattr(v, vert_attr)))
        if sav_name is not None:
            assert isinstance(sav_name, str) and sav_name.endswith('.json')
            with open(sav_name, 'w') as f:
                json.dump(ret, f, indent=4)
        return ret


class GreasePencil(Thing):
    """Wrapper around blender's grease pencil."""
    def __new__(cls, name, **kwargs): #pylint: disable=arguments-differ
        return super().__new__(cls, name, **kwargs)

    def __init__(self, name, **kwargs):
        super().__init__(name, 'GreasePencil', **kwargs)
        if not hasattr(self, '_layer'):
            self._layer = None
            self._keyframe = None

            # initialize hidden variables
            if not self().layers[:]:
                self.layer = 'main' # this will also take care of the keyframe
            else:
                self.layer = self().layers[0].info
                if self.layer.frames[:]:
                    self.keyframe = self.layer.frames[0].frame_number
                else:
                    self.keyframe = 0 # if there was a layer without keyframes in it
    
    @property
    def layer(self):
        """Returns the current layer."""
        return self._layer
    
    @layer.setter
    def layer(self, layer_name):
        """
        Returns a reference to an existing layer.
        Creates a layer if it doesn't exist.
        """
        if layer_name in [l.info for l in self().layers]:
            self._layer = self().layers[layer_name]
        else:
            self._layer = self().layers.new(layer_name)
            self.keyframe = 0 # make a default keyframe at 0 with every new layer

    def layer_clear(self):
        """Remove all strokes from all frames in the current layer"""
        self.layer.clear() # removes all keyframes and strokes

    @property
    def keyframe(self):
        """Returns the current keyframe."""
        return self._keyframe
    
    @keyframe.setter
    def keyframe(self, keynum):
        """
        Returns reference to the keyframe given by keynum for the
        current layer.
        Inserts a keyframe in the current layer if there isn't one.
        """
        assert isinstance(keynum, int)
        if keynum not in [kf.frame_number for kf in self.layer.frames]:
            self._layer.frames.new(keynum)
        self._keyframe = [kf for kf in self.layer.frames if kf.frame_number == keynum][0]
    
    def keyframe_clear(self):
        """Clear the current keyframe in the current layer."""
        self.keyframe.clear()

    @property
    def layers(self):
        """Return names of all layers."""
        return [l.info for l in self().layers]
    
    @property
    def keyframes(self):
        """Return a mapping of layers: keyframes"""
        ret = {}
        for layer in self().layers:
            ret[layer.info] = [kf.frame_number for kf in layer.frames]
        return ret

    @property
    def strokes(self):
        """Return a list of all the strokes."""
        ret = {}
        for layer in self().layers:
            for kf in layer.frames:
                if kf.strokes[:]:
                    for i, stroke in enumerate(kf.strokes[:]):
                        ret[layer.info+'_key{:04d}'.format(kf.frame_number)+'_stroke{:03d}'.format(i)] = stroke
                else:
                    ret[layer.info+'_key{:04d}'.format(kf.frame_number)] = None
        return ret


@pn.PortProperties(GreasePencil, 'data') # instance of CompundObject OR GreasePencilObject MUST have 'data' attribute/property that is an instance of Mesh class
class GreasePencilObject(CompoundObject):
    """
    This is a core.Object. Automatically calls the appropriate methods
    and properties from Object and Greasepencil classes.
    """
    def __new__(cls, name, *args, **kwargs):
        return super().__new__(cls, name, 'GPENCIL', *args, **kwargs)

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, 'GPENCIL', GreasePencil, *args, **kwargs)
        if not hasattr(self, '_color'):
            self._color = None
            if not self().material_slots[:]:
                if 'white' not in [m.name for m in bpy.data.materials]:
                    self.color = {'white': (1.0, 1.0, 1.0, 1.0)}
                self().data.materials.append(bpy.data.materials['white'])
            else:
                self.color = 0

    @property
    def color_index(self):
        """Index of the current color."""
        return {m.name : i for i, m in enumerate(self().material_slots)}[self._color]

    @property
    def color(self):
        """Return the name of the current color."""
        return self._color

    @color.setter
    def color(self, this_color, verbose=False):
        """
        Set the current stroke material (self._color).
        this_color is either a string, a number, a dict, or a tuple.
        string - material name
        integer - cycle through colors in COLOR LIST, which defaults to the matplotlib color cycler 
            Note that older versions of this code interpreted the integer as blender's material index)
        tuple - 4-element tuple : select the closest color
        dict - create new material
            one key, value pair {name: 4-tuple rgba}
            if material with that name exists, print a warning and DO NOTHING
        """
        if isinstance(this_color, int):
            # assert this_color < len(self().material_slots)
            # color_name = {i : m.name for i, m in enumerate(self().material_slots)}[this_color]
            this_color = COLOR_LIST[this_color % len(COLOR_LIST)]

        if isinstance(this_color, dict):
            assert len(this_color) == 1 # supply only one color at a time?'
            key = list(this_color.keys())[0] # key is the name
            val = list(this_color.values())[0]
            if key in [m.name for m in bpy.data.materials]:
                if verbose:
                    print('Color '+key+' already exists in the palette!')
            else: # make a new color
                assert len(val) == 4
                for v in val:
                    assert 0.0 <= v <= 1.0
                utils.new_gp_color(key, val)
            color_name = key
        if isinstance(this_color, str):
            if this_color == 'random':
                import matplotlib.colors as mc
                import random
                this_color = random.choice(list(mc.cnames.keys()))
            color_name = this_color  
            # create material if color does not exist
            if color_name not in [m.name for m in bpy.data.materials]:
                utils.new_gp_color(color_name)

        # add color to the material slot if it does not exist
        if color_name not in [m.name for m in self().data.materials if m is not None]:
            self().data.materials.append(bpy.data.materials[color_name])

        self._color = color_name

    def stroke(self, ptcloud, **kwargs):
        """
        Make a new stroke 
            1) in the current layer, 
            2) at the current keyframe,
            3) in the current color.
        Allow settings for color, layer, keyframe 
        (which change the current settings)
        Add pressure and strength arrays
        """
        kwargs, _ = pn.clean_kwargs(kwargs, {
            'pressure': 1.0, 
            'strength': 1.0, 
            'line_width': 40, 
            'layer': None, # defaults to layer in self._layer
            'color': None, # defaults to current color self._color
            'keyframe': None, # defaults to self._keyframe
            'display_mode': '3DSPACE',
            })

        # set where, when and color
        if kwargs['layer'] is not None:
            self.data.layer = kwargs['layer']
        if kwargs['keyframe'] is not None:
            if isinstance(kwargs['keyframe'], (tuple, list)):
                assert len(kwargs['keyframe']) == 2 # start and stop frame
                self.data.keyframe = kwargs['keyframe'][0]
        if kwargs['color'] is not None:
            self.color = kwargs['color']

        assert isinstance(ptcloud, trf.PointCloud)
        gp_stroke = self.data.keyframe.strokes.new()
        gp_stroke.display_mode = kwargs['display_mode']

        gp_stroke.points.add(count=ptcloud.n)
        gp_stroke.points.foreach_set('co', tuple(ptcloud.in_frame(self.frame).co.flatten())) # more efficient
        gp_stroke.material_index = self.color_index
        gp_stroke.line_width = kwargs['line_width']
        n_pts = len(gp_stroke.points[:])

        for attr in ('pressure', 'strength'):
            if isinstance(kwargs[attr], (int, float)):
                kwargs[attr] = kwargs[attr]*np.ones(n_pts)
            else:
                assert len(kwargs[attr]) == n_pts
            gp_stroke.points.foreach_set(attr, tuple(kwargs[attr]))
        
        if isinstance(kwargs['keyframe'], (tuple, list)):
            self.data.keyframe = kwargs['keyframe'][1]+1 # if a range was specified, turn off the stroke on the keyframe after the end frame specified
        return gp_stroke


class Curve(Thing):
    """
    Wrapper around a bpy.types.Curve object.
    Blender appears to have three types of curves - CURVE, SURFACE, FONT
    """
    def __new__(cls, name, **kwargs): #pylint: disable=arguments-differ
        return super().__new__(cls, name, **kwargs)

    def __init__(self, name, **kwargs):
        """args[0] is in (CURVE, SURFACE, FONT)"""
        super().__init__(name, 'Curve', 'CURVE', **kwargs)


@pn.PortProperties(Curve, 'data') # CurveObject (or CompoundObject) MUST define data as an attribute or property
class CurveObject(CompoundObject):
    """Wrapper for curve object"""
    def __new__(cls, name, *args, **kwargs):
        return super().__new__(cls, name, 'CURVE', *args, **kwargs)

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, 'CURVE', Curve, *args, **kwargs)
 

class ContainerObject(Object):
    """
    Create an empty container object (to be used by Text, Screen, etc)
    It is easier to move a collection of objects around with this, compared to using a collection.
    """
    def __new__(cls, name, **kwargs): # pylint: disable=arguments-differ
        return super().__new__(cls, name, **kwargs)

    def __init__(self, name, **kwargs):
        super().__init__(name, None, **kwargs)
    
    def add(self, obj, keep_in_world=True):
        """
        Add an object to the container.
        Don't change its matrix_world (if keep_in_world is True).
        """
        # This assertion fails if modules are reloaded, and the object passed was in a different module
        # assert isinstance(obj, Object)
        if keep_in_world:
            obj_frame = obj.frame
        obj().parent = self()
        if keep_in_world:
            obj.frame = obj_frame
        
    def children(self):
        """Get the children of the object."""
        return [utils.enhance(c) for c in self().children]


class Stroke:
    """Enhance Grease pencil stroke, for setting and getting points."""
    def __init__(self, GPStroke):
        self.GPStroke = GPStroke

    def __call__(self):
        return self.GPStroke
    
    @property
    def n(self):
        return len(self().points)

    @property
    def v(self):
        co = [0]*3*self.n
        self().points.foreach_get('co', co)
        return np.reshape(co, (self.n, 3))

    @v.setter
    def v(self, co):
        assert np.shape(co) == (self.n, 3)
        self().points.foreach_set('co', np.reshape(co, self.n*3))
        self().id_data.update_tag()
        bpy.context.view_layer.update()

    @property
    def name(self):
        all_strokes = GreasePencil(self().id_data).strokes
        return list(all_strokes.keys())[list(all_strokes.values()).index(self())]

    @property
    def properties(self):
        name = self.name
        keyframe = int(name.split('_')[-2].strip('key'))
        strokenumber = int(name.split('_')[-1].strip('stroke'))
        layer = "_".join(name.split('_')[:-2])
        return {"object": self.parent_object.name, "pencil": self().id_data.name, "layer": layer, "keyframe": keyframe, "stroke": strokenumber}

    @property
    def parent_object(self):
        x = [utils.enhance(o) for o in bpy.data.objects if o.data == self().id_data]
        if len(x) == 1:
            return x[0]
        return x

    @property
    def parent_pencil(self):
        return GreasePencil(self().id_data)

    @property
    def parent_layer(self):
        p = self.properties
        return self().id_data.layers[p["layer"]]

    @property
    def parent_keyframe(self):
        p = self.properties
        return [f for f in self().id_data.layers[p["layer"]].frames if f.frame_number == p["keyframe"]][0]
