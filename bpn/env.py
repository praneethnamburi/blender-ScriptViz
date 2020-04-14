"""
Environment control in blender.

Classes:
    Props - Snapshot of prop collections in blender's data.
    ReportDelta - Decorator for functions to report changes the function made to blender after execution.

Functions:
    reset() - Reset the current blender scene programatically (useful to preserve console history and variables)
    shade() - Change the shading in 3D viewport
"""
import re
import functools
import numpy as np

import bpy #pylint: disable=import-error

PROP_FIELDS = [k for k in dir(bpy.data) if 'bpy_prop_collection' in str(type(getattr(bpy.data, k)))]

### Manage blender resources
class Props:
    """
    Snapshot of prop collections in blender's data.

    This is an easy way to get references to all Props when you're
    working in blender.

    Construction:
        :param inp_dict: dict. Meant for internal use by operators.

    Usage:
        Props() -> new Props object. Access everything with Props().__dict__
        Props(inpDict) -> turn a dictionary into Props object. Used by
            add and subtract. User shouldn't need to worry about this.
        a = Props()
        # make changes to the scene
        b = Props()
        (b-a)() -> call prop objects to return a dictionary reporting only the changes!
        diff1 = b-a
        # add another mesh to the scene
        c = Props()
        diff2 = c-b
        diff2 | diff1 -> object summarizing all changes
        (b-a).names() -> dictionary of names of changes
        b('Cube') -> Find all Props named 'Cube', returns 
                    dict of {prop type: list of Props with name}
                    {'meshes': [bpy.data.meshes['Cube']], 'objects': [bpy.data.objects['Cube']]}
        b.get('Cube') -> Find all Props named 'Cube', returns 
                    list of Props with 'Cube' in their name, irrespective of prop type
                    [bpy.data.meshes['Cube'], bpy.data.objects['Cube']]
        Props().get('Cube') -> calling this way, as opposed to b.get('Cube') 
                    doesn't seem to have any difference in performance. So, make
                    Props objects only to store states.
    
    Dev note:
        Don't add any properties to this object. Keep it limited to PROP_FIELDS.
        TODO: Change to slots?
    """
    def __init__(self, inp_dict=None):
        if not inp_dict:
            self.__dict__ = {p : set(getattr(bpy.data, p)) for p in PROP_FIELDS}
        else:
            self.__dict__ = inp_dict
    def __or__(self, other): # union
        self.clean()
        return Props({p:self.__dict__[p].union(other.__dict__[p]) for p in PROP_FIELDS})
    def __and__(self, other): # intersection
        self.clean()
        return Props({p:self.__dict__[p].intersection(other.__dict__[p]) for p in PROP_FIELDS})
    def __sub__(self, other): # setdiff
        self.clean()
        return Props({p:self.__dict__[p] - other.__dict__[p] for p in PROP_FIELDS})
    def __xor__(self, other): # exclusive or
        return (self | other) - (self & other)
    def __call__(self, names=None):
        """Dictionary of lists of objects, skip empty collections."""
        self.clean()
        if isinstance(names, str):
            names = [names]
        if not names:
            return {p:list(propset) for p, propset in self.__dict__.items() if propset != set()}
        else: # list of names
            res = {}
            for p, propset in self.__dict__.items():
                if propset != set():
                    res[p] = [prop for prop in propset if prop.name in names]
            return {p:proplist for p, proplist in res.items() if proplist}
    def clean(self):
        """Remove invalid objects (i.e., deleted from blender)."""
        self.__dict__ = {p : {k for k in self.__dict__[p] if 'invalid' not in  str(k)} for p in PROP_FIELDS}
    def get(self, name=''):
        """Get an object by its name."""
        assert isinstance(name, str)
        return [k[0] for k in self(name).values()]
    def search(self, name=''):
        """
        Return names of props in the environment that match a specific regular expression.
        See get_re for examples
        """
        all_prop_names = [this_item for this_set in self.names().values() for this_item in this_set]
        all_matched_names = list(np.unique([i for i in all_prop_names if re.search(name, i)]))
        return all_matched_names
    def get_re(self, name=''):
        """
        Return all props that fit a regular expression given in name.
        Props().get_re('^ax') : return all props starting with 'ax'
        Props().get_re('_R$') : return all props ending with '_R'
        Props().get_re('es') : return everything with 'es' in it
        Props().get_re('es$') : return everython ending with es
        """
        ret_list = []
        for this_name in self.search(name):
            ret_list += self.get(this_name)
        return ret_list
    def names(self, discard_empty=True):
        """Return only the names, and not references to objects."""
        self.clean()
        allNames = {p: {k.name for k in self.__dict__[p]} for p in PROP_FIELDS}
        if discard_empty:
            return {k:v for k, v in allNames.items() if v}
        else:
            return allNames
    def get_children(self, obj_name):
        """
        Return children of a given object.
        Note that this function will only return children at the bottom most level.
        Example:
            c = Props().get_children('Foot_Bones_R')
        """
        if not self.get(obj_name):
            return set() # return empty set if the object isn't found
        children = set((self.get(obj_name)[0],))
        iterFlag = True
        while iterFlag:
            iterFlag = False
            for obj in children:
                if obj.children: # if children exist, remove object, and put children into the set
                    children = children.union(set(obj.children)) - set((obj,))
                    iterFlag = True
        return children

class ReportDelta:
    """
    This class is primarily meant to be used as a decorator.
    This decorator reports changes to blender data (prop collections) after the decorated function is executed.
    Within a script, you can use the decorator syntax, for example
    @ReportDelta
    def demo_animateDNA():
        #animation code goes here
        pass
    deltaReport = demo_animateDNA()
    OR
    when using from a terminal, or from within a script, use
    deltaReport = bpn.ReportDeltaData(bpn.demo_animateDNA)()

    Primarily created for use with loadSTL, but works well with any function that changes the scene.
    To capture the state of blender environment, and compare between states, use the Props class.
    Use ReportDelta mainly as a decorator.
    """
    def __init__(self, func):
        self.func = func # a function that changes something in the blender data
        functools.update_wrapper(self, func) # to preserve original signatures

        # find all the things to monitor
        self.monFieldNames = PROP_FIELDS

        # initialize generated report
        self.deltaReport = {
            'funcOut'         : [],                 # output of the function passed to this decorator
            'monitoredFields' : self.monFieldNames, # list of monitored fields in bpy.data
            'unchangedFields' : [],                 # list of fields unchanged by func
            'changedFields'   : [],                 # list of fields changed by func
        }

    def __call__(self, *args, **kwargs):
        # get the 'before' state
        propsBefore = Props().__dict__

        # evaluate the function that is going to change blender data, and stash its output
        self.deltaReport['funcOut'] = self.func(*args, **kwargs)

        # get the 'after' state
        propsAfter = Props().__dict__

        # find all the new things
        for fieldName in self.monFieldNames:
            thisDelta = propsAfter[fieldName] - propsBefore[fieldName]
            if not thisDelta == set(): # only if something changed
                self.deltaReport[fieldName] = list(thisDelta)
                self.deltaReport['changedFields'].append(fieldName)
            else:
                self.deltaReport['unchangedFields'].append(fieldName)

        # if an object is modified, then arrange meshes and groups according to the object order?
        return self.deltaReport


def reset():
    """
    Reset the current scene programatically.
    Script adapted from:
    https://developer.blender.org/T47418

    This is extremely useful for clearing the scene programatically during iterative development.
    """
    for scene in bpy.data.scenes:
        for obj in scene.objects:
            try:
                scene.objects.unlink(obj)
            except AttributeError:
                # import traceback
                # traceback.print_exc()
                pass

    exclusion_list = ['brushes', 'images', 'screens', 'window_managers', 'workspaces', 'scenes', 'worlds', 'palettes', 'linestyles']
    all_prop_coll = [pc for pc in dir(bpy.data) if type(getattr(bpy.data, pc)).__name__ == 'bpy_prop_collection']
    rem_prop_coll = [pc for pc in all_prop_coll if pc not in exclusion_list]
    clear(rem_prop_coll)

    # clear frame change handlers (perhaps clear all handlers?)
    bpy.app.handlers.frame_change_pre.clear()
    bpy.app.handlers.frame_change_post.clear()

def clear(clist=None):
    """
    Clear specific things from prop collection.
    Example:
        env.clear('actions') will remove all actions
    """
    if clist is None:
        clist = []
    if isinstance(clist, str):
        clist = [clist]
    assert isinstance(clist, list)
    for bpy_data_iter in [getattr(bpy.data, citem) for citem in clist]:
        for id_data in bpy_data_iter:
            try:
                bpy_data_iter.remove(id_data)
            except AttributeError:
                pass

def shade(shading='WIREFRAME', area='Layout'):
    """
    Set 3D viewport shading
    """
    my_areas = bpy.data.screens[area].areas
    assert shading in ['WIREFRAME', 'SOLID', 'MATERIAL', 'RENDERED']

    for this_area in my_areas:
        for space in this_area.spaces:
            if space.type == 'VIEW_3D' and this_area.type == 'VIEW_3D':
                space.shading.type = shading

class Key:
    """
    Easy access to set animation limits.

    After a series of animation commands, use env.Key().auto_lim()
    """
    @property
    def start(self):
        """First frame of animation."""
        return bpy.context.scene.frame_start
    @start.setter
    def start(self, val):
        bpy.context.scene.frame_start = val
    begin = start

    @property
    def end(self):
        """Last frame of animation."""
        return bpy.context.scene.frame_end
    @end.setter
    def end(self, val):
        bpy.context.scene.frame_end = val
    stop = end

    @property
    def lim(self):
        """Current animation limits."""
        return self.begin, self.end
    @lim.setter
    def lim(self, val):
        self.begin = val[0]
        self.end = val[1]

    def auto_lim(self):
        """Use this function after doing an animation."""
        action_list = np.array([action.frame_range for action in bpy.data.actions if action.users > 0])
        if action_list.size:
            self.lim = np.min(action_list), np.max(action_list)

    def goto(self, frame):
        """Go to a frame given by frame."""
        assert isinstance(frame, int)
        bpy.context.scene.frame_current = frame
