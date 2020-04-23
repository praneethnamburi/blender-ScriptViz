"""
Praneeth's tools for making life easy while coding in python.

The tools are organized into the following categories:
Inheritance, File system, Package management, Introspection, Input management and Code development

Inheritance: (Special cases where I needed to tweak inheritance)
    AddMethods      - (Decorator) Add methods to a class
    Mixin           - (Decorator) Grab methods from another class, and deepcopy list/dict class attributes
    port_properties - Implement containers with automatic method routing
    PortProperties  - (Decorator) for using port_properties

File system:
    locate_command - locate an executable in the system path
    OnDisk         - (Decorator) Raise error if function output file is not on disk
    ospath         - Find file or directory

Package management: (mostly useful during deployment)
    pkg_list - return list of installed packages
    pkg_path - return path to installed packages

Introspection:
    inputs         - Get input variable names and default values of a function
    module_members - list members of a module
    properties     - summary of object attributes, properties and methods

Input management:
    clean_kwargs - Clean keyword arguments based on default values and aliasing

Code development: (functions that help during code development)
    reload  - Reload modules in development folder
    Time    - (Decorator) Execution time
    tracker - (decorator) Track objects created by a class (preserves class as class - preferred)
    Tracker - (Decorator) Track objects created by a class (turns classes into Tracker objects)
"""

import datetime
import errno
import functools
import importlib
import inspect
import json
import os
import re
import pickle
import sys
import subprocess
from copy import deepcopy
from timeit import default_timer as timer

import numpy as np
from blinker import signal

## Inheritance
class AddMethods:
    """
    Add methods to a class. Decorator.
    
    Usage:
        @AddMethods([pntools.properties])
        class myClass:
            def foo(self):
                print("bar")
        
        a = myClass()
        a.foo() # prints bar
        a.properties() # lists foo and properties
    """
    def __init__(self, methodList):
        self.methodList = methodList
    def __call__(self, func):
        functools.update_wrapper(self, func)
        @functools.wraps(func)
        def wrapperFunc(*args, **kwargs):
            for method in self.methodList:
                setattr(func, method.__name__, method)
            funcOut = func(*args, **kwargs)
            return funcOut
        return wrapperFunc

class MixIn:
    """
    Decorator to grab properties from src class and put them in target class.
    No overwrites.
    ALMOST the same as inheritance, BUT, if the source class has a
    'list' or 'dict' class attribute, then it makes a deepcopy
    Example:
        @MixIn(src_class)
        class trg_class:
            pass
    """
    def __init__(self, src_class):
        self.src_class = src_class
    def __call__(self, trg_class):
        src_attrs = {attr_name:attr for attr_name, attr in self.src_class.__dict__.items() if attr_name[0] != '_'}
        for src_attr_name, src_attr in src_attrs.items():
            if not hasattr(trg_class, src_attr_name): # no overwrites
                if isinstance(src_attr, (list, dict)):
                    src_attr = deepcopy(src_attr)
                setattr(trg_class, src_attr_name, src_attr)
        return trg_class

def port_properties(src_class, trg_class, trg_attr_name='data'):
    """
    Port properties and methods (not hidden) from source class src_class
    to target class trg_class.

    Differs from Mixin and inheriance. Used to design 'containers' with automatic routing.

    :param src_class: (class)
    :param trg_class: (class)
    :param trg_attr_name: (str)

    Basically, trg_class objects have an attribute with name
    trg_attr_name, which is an instance of trg_class
    Example:
        MeshObject class has an attribute (or property) 'data' that is an instance of trg class
        s = MeshObject() # MeshObject is the trg_class
        s.data = Mesh()  # Mesh is the src_class
    Now,
        s.data.prop : to execute this, I want to say s.prop
        s.data.func() : to execute this, I want to say s.func()
        
    Within MeshObject, defining the __init__ function as follows achieves this!
    class MeshObject(Object):
        def __init__(self, name, *args, **kwargs):
            super().__init__(name, *args, **kwargs) # make an instance of Object
            self.data = Mesh(...) # make an instance of mesh
            pn.port_properties(Mesh, self.__class__, 'data') 
            # grants direct access to Mesh's stuff with appropritate routing

    Now a MeshObject instance inherits all methods and properties from
    Object class, AND from Mesh class. Methods from Mesh class are
    automagically called with the correct Mesh object as the first input.

    Note that trg_class itself is being modified
    (i.e., return statement is just to enable the decorator)

    Note that attributes of the Mesh class will NOT be copied
    """
    # properties
    def swap_input_fget(this_prop):
        return lambda x: this_prop.fget(getattr(x, trg_attr_name))
    
    def swap_input_fset(this_prop):
        return lambda x, s: this_prop.fset(getattr(x, trg_attr_name), s)

    src_properties = {p_name : p for p_name, p in src_class.__dict__.items() if isinstance(p, property)}
    for p_name, p in src_properties.items():
        if not hasattr(trg_class, p_name): # no overwrites - this implmentation is more readable
            if p.fset is None:
                setattr(trg_class, p_name, property(swap_input_fget(p)))
            else:
                setattr(trg_class, p_name, property(swap_input_fget(p), swap_input_fset(p)))

    # methods
    def swap_first_input(func): # when we don't know how many inputs func has
        return lambda x: functools.partial(func, getattr(x, trg_attr_name))

    src_methods = {func_name:func for func_name, func in src_class.__dict__.items() if type(func).__name__ == 'function' and func_name[0] != '_'}
    for src_func_name, src_func in src_methods.items():
        if not hasattr(trg_class, src_func_name): # no overwrites
            setattr(trg_class, src_func_name, property(swap_first_input(src_func)))

    return trg_class

class PortProperties:
    """
    Providing port_properties functionality as a decorator.
    
    This is for implementing the idea of a 'container' in blender, that
    I could not solve using multiple inheritance. A container is an
    instance of a specific class, but also contains instances of other
    classes. You can act on any 'contained' object directly (you just
    have to use the method name)
    cont = primary_class()
    cont.two = secondary_class()
    If dummy is a method of cont.two, then I want to say:
    cont.dummy() instead of cont.two.dummy(), 
    BUT cont.dummy() should execute cont.two.dummy() if cont doesn't have a method called dummy()

    A container class is created by:
    Inheriting from a primary class.
    Modifiying the container class with port_properties (or using the PortProperties decorator)

    Example:
    @PortProperties(Mesh, 'data') # instance of MeshObject MUST have 'data' attribute/property
    class MeshObject(Object):   
        def __init__(self):
            super().__init__()
            self.data = Mesh()

    m = MeshObject()

    In this example, MeshObject is the container class.
    It inherits from Object class.
    Mesh is the secondary class
    """
    def __init__(self, src_class, trg_attr_name):
        self.src_class = src_class
        self.trg_attr_name = trg_attr_name
    def __call__(self, trg_class):
        return port_properties(self.src_class, trg_class, self.trg_attr_name)


## Event handlers and broadcasting using blinker's signal
# def handler_id(thing, mode='post'):
#     """
#     Return an event handler's ID (signal name) for a give function, property or method.
#     """
#     assert mode in ('pre', 'post')
#     def _handler_id_prefix(thing):
#         if type(thing).__name__ == 'function':
#             return thing.__module__ + '.' + thing.__qualname__
#         if type(thing).__name__ == 'method':
#             if hasattr(thing.__self__, 'name'):
#                 instance_string = thing.__self__.name
#             else:
#                 instance_string = hex(id(thing.__self__))
#             return thing.__module__ + '.' + thing.__qualname__ + '.' + instance_string

#         if isinstance(thing, property):
#             if thing.fset is None:
#                 print('Event handlers are currently supported only for properties with setters')
#                 return []
#             return thing.fset.__module__ + '.' + thing.fset.__qualname__ + '.fset'
#         return []

#     hid = _handler_id_prefix(thing)
#     if not hid:
#         return None
#     return hid + '.' + mode

def _handler_helper(thing, attr):
    assert hasattr(thing, attr)
    thing_is_class = inspect.isclass(thing)
    thing_class = thing if thing_is_class else type(thing)
    attr_cat = type(getattr(thing_class, attr)).__name__ # attribute category
    assert attr_cat in ('property', 'function')
    if attr_cat == 'property':
        assert getattr(thing_class, attr).fset is not None
    return thing_is_class, thing_class, attr_cat

def handler_id(thing, attr, mode='post'):
    """
    String that represents the identity of the handler
    """
    assert mode in ('pre', 'post')
    thing_is_class, thing_class, attr_cat = _handler_helper(thing, attr)
    mod_name = thing.__module__ if thing_is_class else type(thing).__module__
    attr_name = getattr(thing_class, attr).__qualname__ if attr_cat == 'function' else getattr(thing_class, attr).fset.__qualname__
    if attr_cat == 'property':
        attr_name += '.fset' # emphasizing that we are only adding handlers to setters
    instance_name = ''
    if not thing_is_class:
        instance_name = thing.name if hasattr(thing, 'name') else hex(id(thing))
        instance_name = '(' + instance_name + ')'
    return mod_name + '.' + attr_name + instance_name + '_' + mode


def add_handler2(thing, attr, handler_funcs, mode='post'):
    """
    s1 = new.sphere('sph1')
    # s1.frame is a property, and fire fun whenever s1.frame is set
    add_handler(s1, 'frame', fun, mode='pre') 
    # Fire fun when the frame attribute of any instance of core.Object is set
    add_handler(core.Object, 'frame', fun, mode='post')
    # s1.translate is a method, and fire fun whenever s1.translate is invoked!
    add_handler(s1, 'translate', fun, mode='post')
    """
    # input handling
    assert mode in ('pre', 'post')
    if type(handler_funcs).__name__ in ('function', 'method'):
        handler_funcs = [handler_funcs]

    thing_is_class, thing_class, attr_cat = _handler_helper(thing, attr)
    signal_name = handler_id(thing, attr)

    # set up broadcaster
    if attr_cat == 'function':
        setattr(thing, attr, broadcast_function(getattr(thing, attr), mode))

    # add listeners
    for hfun in handler_funcs:
        signal(signal_name).connect(hfun)



# def add_handler(thing, handler_funcs, mode='post'):
#     """
#     Add an event handler to a function, method or property

#     Function/method (Handler function signature):
#         pre_handlers will receive the same inputs as func
#             f(*args, **kwargs)
#         post_handlers will receive function output, AND inputs (perhaps modified)
#             f((f_out, *args,), **kwargs)
    
#     Property:
#         Add event handler functions to property p either before (mode='pre')
#         or after (mode='post') the property is set.
#         Example:
#             # update coordinate frame every time location is updated
#             s = new.sphere('sph') # create a sphere
#             s.loc = (1, 0, 0) # no coordinate frame shows up
#             # Note that the next statement attaches a handler to ALL instances of core.Object
#             core.Object.loc = pn.add_handler(core.Object.loc, core.Object.show_frame, mode='post')
#             s.loc = (-1, 0, 0) # coordinate frame pops up when location is changed

#     Note that property handlers can only be applied to ALL instances of a class.
#     """
#     assert type(thing).__name__ in ('function', 'method') or (isinstance(thing, property) and thing.fset is not None)
#     assert mode in ('pre', 'post')
#     if type(handler_funcs).__name__ in ('function', 'method'):
#         handler_funcs = [handler_funcs]
#     signal_name = handler_id(thing, mode)

#     if isinstance(thing, property):
#         broadcaster = broadcast_property
#     elif type(thing).__name__ == 'function':
#         broadcaster = broadcast_function
#     elif type(thing).__name__ == 'method':
#         broadcaster = broadcast_method
#     new_thing = broadcaster(thing, mode, signal_name)
#     for hfun in handler_funcs:
#         signal(signal_name).connect(hfun)

#     return new_thing

# def broadcast_method(meth, signal_name, mode='post'):
#     """
#     Creates a new function/method which is the same as func but
#     broadcasts a signal every time it is executed.

#     Broadcaster sends the object (containing meth) to the receiver
#     """
#     assert type(meth).__name__ == 'method'
#     assert mode in ('pre', 'post')

#     unbound_func = getattr(meth.__self__.__class__, meth.__name__)
#     _new_unbound_func = broadcast_function(unbound_func, signal_name, mode)
#     _new_meth = _new_unbound_func.__get__(meth.__self__)
#     return _new_meth

def broadcast_function(func, signal_name, mode='post'):
    """
    ONLY FOR A CLASS FUNCTION
    Creates a new function/method which is the same as func but
    broadcasts a signal every time it is executed.
    """
    func_type = type(func).__name__
    assert func_type in ('function', 'method')
    assert mode in ('pre', 'post')

    if func_type == 'method': # 'unbounded'
        meth = func
        func = getattr(meth.__self__.__class__, meth.__name__)

    def _new_func_pre(self, *args, **kwargs):
        if bool(signal(signal_name).receivers):
            signal(signal_name).send(self) # signal is sent BEFORE the object is modified
        f_out = func(self, *args, **kwargs)
        return f_out
    def _new_func_post(self, *args, **kwargs):
        f_out = func(self, *args, **kwargs)
        if bool(signal(signal_name).receivers):
            signal(signal_name).send(self) # signal is sent AFTER the object is modified
        return f_out

    _new_func = _new_func_pre if mode == 'pre' else _new_func_post
    _new_func.__name__ = func.__name__
    _new_func.__qualname__ = func.__qualname__
    _new_func.__module__ = func.__module__

    if func_type == 'method': # bind the function to the object
        return _new_func.__get__(meth.__self__)
    return _new_func

def broadcast_property(p, signal_name, mode='post'):
    """
    Creates a new property with a modified setter.
    Adds a broadcasting signal to the setter of property p
    :param p: (property)
    :param signal_name: (str) defaults to handler_id(p, mode)
    """
    assert isinstance(p, property)
    assert mode in ('pre', 'post')

    def _new_fset_pre(x, s): # x is the object whose property is being modified (self)
        if bool(signal(signal_name).receivers):
            signal(signal_name).send(x) # signal is sent AFTER the object is modified
        f_out = p.fset(x, s)
        return f_out
    def _new_fset_post(x, s): # x is the object whose property is being modified (self)
        f_out = p.fset(x, s)
        if bool(signal(signal_name).receivers):
            signal(signal_name).send(x) # signal is sent AFTER the object is modified
        return f_out

    _new_fset = _new_fset_pre if mode == 'pre' else _new_fset_post
    _new_fset.__name__ = p.fset.__name__
    _new_fset.__qualname__ = p.fset.__qualname__
    _new_fset.__module__ = p.fset.__module__
    return property(p.fget, _new_fset)

# BroadcastProperties is useful for modifying classes when defining them
class BroadcastProperties:
    """
    Enables properties in a class to have event handlers. This
    manipulation 'replaces' a property in a class with a new property
    object.

    Takes a class, and makes chosen properties setter emit a signal on
    every change. Use it as a decorator on classes to broadcast some/all
    property changes. Receiver receives the object after it is changed.

    Example: see tests.test_broadcasting2()

    Usage: (Don't chain with the same property. Chaining below is OK)
        @pn.BroadcastProperties('loc', mode='pre')
        @pn.BroadcastProperties('frame', mode='post')
        class Object(Thing):
            frame = property(...)
            loc = property(...)
    """
    def __init__(self, p_names='ALL', mode='post'):
        assert isinstance(p_names, (str, list, tuple))
        assert mode in ('pre', 'post')
        self.p_names = p_names
        self.mode = mode
    def __call__(self, src_class):
        if isinstance(self.p_names, str) and self.p_names == 'ALL':
            src_properties = {p_name : p for p_name, p in src_class.__dict__.items() if isinstance(p, property)}
        else:
            src_properties = {p_name : p for p_name, p in src_class.__dict__.items() if isinstance(p, property) and p_name in self.p_names}
        for p_name, p in src_properties.items():
            if p.fset is not None:
                setattr(src_class, p_name, broadcast_property(p, handler_id(src_class, p_name), self.mode))
        return src_class


## File system
def locate_command(thingToFind, requireStr=None, verbose=True):
    """
    Locate an executable on your computer.

    :param thingToFind: string name of the executable (e.g. python)
    :param requireStr: require path to thingToFind to have a certain string
    :returns: Full path (like realpath) to thingToFind if it exists
              Empty string if thing does not exist
    """
    if sys.platform == 'linux' or sys.platform == 'darwin':
        queryCmd = 'which'
    elif sys.platform == 'win32':
        queryCmd = 'where'
    proc = subprocess.Popen(queryCmd+' '+thingToFind, stdout=subprocess.PIPE, shell=True)
    thingPath = proc.communicate()[0].decode('utf-8').rstrip('\n').rstrip('\r')
    if not thingPath:
        print('Terminal cannot find ', thingToFind)
        return ''

    if verbose:
        print('Terminal found: ', thingPath)
    if requireStr is not None:
        if requireStr not in thingPath:
            print('Path to ' + thingToFind + ' does not have ' + requireStr + ' in it!')
            return ''
    return thingPath

class OnDisk:
    """
    Raise error if function output not on disk. Decorator.

    :param func: function that outputs a path/directory
    :returns: decorated function with output handling
    :raises keyError: FileNotFoundError if func's output is not on disk

    Example:
        @OnDisk
        def getFileName_full(fPath, fName):
            fullName = os.path.join(os.path.normpath(fPath), fName)
            return fullName
    """
    def __init__(self, func):
        self.func = func
        functools.update_wrapper(self, func)
    def __call__(self, *args, **kwargs):
        thisDirFiles = self.func(*args, **kwargs)
        self.checkFiles(thisDirFiles)
        return thisDirFiles
    @staticmethod
    def checkFiles(thisFileList):
        """Raise error if any file in thisFileList not on disk."""
        if isinstance(thisFileList, str):
            thisFileList = [thisFileList]
        for dirFile in thisFileList:
            if not os.path.exists(dirFile):
                raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), dirFile)

def ospath(thingToFind, errContent=None):
    """
    Find file or directory.
    
    :param thingToFind: string input to os path
    :param errContent=None: what to show when not found
    :returns: Full path to thingToFind if it exists.
              Empty string if thingToFind does not exist.
    """
    if errContent is None:
        errContent = thingToFind
    if os.path.exists(thingToFind):
        print('Found: ', os.path.realpath(thingToFind))
        return os.path.realpath(thingToFind)
    print('Did not find ', errContent)
    return ''


## Package management
def pkg_list():
    """
    Return a list of installed packages.

    :returns: output of pip freeze
    :raises keyError: raises an exception
    """
    proc = subprocess.Popen('pip freeze', stdout=subprocess.PIPE, shell=True)
    out = proc.communicate()
    pkgs = out[0].decode('utf-8').rstrip('\n').split('\n')
    pkgs = [k.rstrip('\r') for k in pkgs]  # windows compatibility
    pkgNames = [m[0] for m in [k.split('==') for k in pkgs]]
    pkgVers = [m[0] for m in [k.split('==') for k in pkgs]]
    return pkgs, pkgNames, pkgVers

def pkg_path(pkgNames=None):
    """Return path to installed packages."""
    if not pkgNames:
        _, pkgNames, _ = pkg_list()
    elif isinstance(pkgNames, str):
        pkgNames = [pkgNames]
    
    currPkgDir = []
    failedPackages = []
    for pkgName in pkgNames:
        print(pkgName)
        if pkgName == 'ipython':
            pkgName = 'IPython'
        elif pkgName == 'ipython-genutils':
            pkgName = str(pkgName).lower().replace('-', '_')
        elif pkgName in ['pywinpty', 'pyzmq', 'terminado']:
            continue
        else:
            pkgName = str(pkgName).lower().replace('-', '_').replace('python_', '').replace('_websupport', '')
        try:
            currPkgDir.append(importlib.import_module(pkgName).__file__)
        except UserWarning:
            failedPackages.append(pkgName)

    print('Failed for: ', failedPackages)    
    return currPkgDir


## introspection
def inputs(func):
    """Get the input variable names and default values to a function."""
    inpdict = {}
    if callable(func):
        inpdict = {str(k):inspect.signature(func).parameters[str(k)].default for k in inspect.signature(func).parameters.keys()}
    return inpdict

def module_members(mod, includeSubModules=True):
    """Return members of a module."""
    members = {}
    for name, data in inspect.getmembers(mod):
        if name.startswith('__') or (inspect.ismodule(data) and not includeSubModules):
            continue
        members[name] = str(type(inspect.unwrap(data))).split("'")[1]
    return members

def properties(obj):
    """
    For an instance obj of any class, use pn.properties(obj) for a summary of properties.
    Especially useful in the blender console.
    """
    #pylint:disable=expression-not-assigned
    [print((k, type(getattr(obj, k)), np.shape(getattr(obj, k)))) for k in dir(obj) if '_' not in k and 'method' not in k]


## input management
def clean_kwargs(kwargs, kwargs_def, kwargs_alias=None):
    """
    Clean keyword arguments based on default values and aliasing.

    :param kwargs: (dict) input kwargs that require cleaning.
    :param kwargs_def: (dict) should have all the possible keyword arguments.
    :param kwargs_alias: (dict) lists all possible aliases for each keyword.
        {kw1: [kw1, kw1_alias1, ..., kw1_aliasn], ...}
        kw1 is used inside the function, but kw1=val, kw1_alias1=val, ..., kw1_aliasn are all valid

    Returns: 
        (dict) keyword arguments after cleaning. Ensures all keywords in kwargs_def are present, and have the names used in the function.
        (dict) remaining keyword arguments
    """
    if not kwargs_alias:
        kwargs_alias = {key : [key] for key in kwargs_def.keys()}
    kwargs_fun = deepcopy(kwargs_def)
    kwargs_out = deepcopy(kwargs)
    for k in kwargs_fun:
        for ka in kwargs_alias[k]:
            if ka in kwargs:
                kwargs_fun[k] = kwargs_out.pop(ka)

    return kwargs_fun, kwargs_out


## Code development
def reload(constraint='Workspace'):
    """
    Reloads all modules in sys with a specified constraint.
    :param constraint: (str) name to be present within the module's path for reload
    Returns:
        names of all the modules that were identified for reload.
    """
    all_mod = [mod for key, mod in sys.modules.items() if constraint in str(mod)]
    reloaded_mod = []
    for mod in all_mod:
        try:
            importlib.reload(mod)
            reloaded_mod.append(mod.__name__)
        except: # pylint: disable=bare-except 
            #Using a specific exception creates a problem when developing with runpy (Blender development plugin workflow)
            if '<run_path>' not in  mod.__name__:
                print('Could not reload ' + mod.__name__)
    return reloaded_mod

class Time:
    """
    Prints execution time. Decorator.
    Note that this only works on functions.
    Consider a function call:
    out1 = m.inflate(0.15, 0.1, 0.02, 100)
    Using the following will give the output in addition to printing the
    execution time.
    out1 = pn.Time(m.inflate)(0.15, 0.1, 0.02, 100)
    """
    def __init__(self, func):
        self.func = func
        functools.update_wrapper(self, func)
    def __call__(self, *args, **kwargs):
        start = timer()
        funcOut = self.func(*args, **kwargs)
        end = timer()
        print(end-start)
        return funcOut

def tracker(trg_class):
    """
    Use this as a decorator to track class instances (and keep tracked classes as classes).
    include self.track(self) in the decorated class' __init__
    If there is a tracker in the parent class, don't add self.track(self) to the child class.
    BUT, decorate the child class!!
    
    Example:
        @tracker
        class Thing:
            def __init__(self):
                self.track(self)

        @tracker
        class Mesh:
            def __init__(self):
                pass # Don't track again!
    """
    class TrackMethods:
        """
        This is just a method container.
        see tracker function
        """
        all = []
        cache = []

        @classmethod
        def track(cls, obj):
            """Just used by the initalization function to track object."""
            cls.all.append(obj)
        
        @classmethod
        def track_clear(cls):
            """Forget the objects tracked so far."""
            cls.all = []
        
        @classmethod
        def track_clear_cache(cls):
            """Clear cache used by temporary tracking sessions."""
            cls.cache = []

        @classmethod
        def track_start(cls):
            """
            Start a tracking session. Move current objects to cache, and clean.
            Note that objects are tracked even without this method if a class is being tracked.
            Use this to create temporary tracking sessions.
            """
            cls.cache = cls.all
            cls.all = []

        @classmethod
        def track_end(cls):
            """End tracking session."""
            cls.all = cls.cache
            cls.cache = []

        @classmethod
        def dict_access(cls, key='id', val=None):
            """
            Give access to the object based on key. 
            
            Note:
            If keys (id) of different objects are the same, then only the
            last reference will be preserved.

            :param key: Property of the object being tracked (to be used as the key).
            :param val: Property of the object being tracked (to be used as the value).
                        When set to None, val is set to the object itself.
            :returns: A dictionary of property pairs for all objects in key(property1):val(property2)
            """
            if not val:
                return {getattr(k, key):k for k in cls.all}
            
            return {getattr(k, key):getattr(k, val) for k in cls.all}

    src_class = TrackMethods
    src_attrs = {attr_name:attr for attr_name, attr in src_class.__dict__.items() if attr_name[0] != '_'}
    # deliberately overwrite all and cache
    trg_class.all = deepcopy(src_class.all)
    trg_class.cache = deepcopy(src_class.cache)
    for src_attr_name, src_attr in src_attrs.items():
        if not hasattr(trg_class, src_attr_name): # no overwrites
            setattr(trg_class, src_attr_name, src_attr)
    return trg_class

class Tracker:
    """
    Keep track of all instances of objects created by a class.
    This converts a class into a Tracker object. 
    To keep a class as a class, decorate with the tracker function.
    clsToTrack. Decorator. 

    Meant to convert clsToTrack into a Tracker object with properties
    all, n, and methods dictAccess

    TODO:list 
    1. keeping track of all tracked classes is controversial because all
       the tracked objects (formerly classes) know what other classes
       are being tracked. (see cls._tracked)

    :param clsToTrack: keep track of objects created by this class
    :returns: a tracker object

    For operations that span across all objects created by a clsToTrack,
    you can simply create a groupOperations class without __new__,
    __init__ or __call__ functions, and decorate clsToDecorate with that
    class. See tests for an example.

    Example of extending the Tracker class:
    class ImgGroupOps(my.Tracker):
        def __init__(self, clsToTrack):
            super().__init__(clsToTrack)
            self.load()
        
        def load(self):
    """
    _tracked = [] # all the classes being tracked
    def __new__(cls, clsToTrack):
        cls._tracked.append(clsToTrack)
        return object.__new__(cls)
    def __init__(self, clsToTrack):
        self.clsToTrack = clsToTrack
        functools.update_wrapper(self, clsToTrack)
        self.all = []
        self.cache = []
    def __call__(self, *args, **kwargs):
        funcOut = self.clsToTrack(*args, **kwargs)
        self.all.append(funcOut)
        return funcOut
    def __delitem__(self, item):
        """
        Stop tracking item.
        item is an instance of clsToTrack
        """
        self.all.remove(item)

    def dictAccess(self, key='id', val=None):
        """
        Give access to the object based on key. 
        
        Note:
        If keys (id) of different objects are the same, then only the
        last reference will be preserved.

        :param key: Property of the object being tracked (to be used as the key).
        :param val: Property of the object being tracked (to be used as the value).
                    When set to None, val is set to the object itself.
        :returns: A dictionary of property pairs for all objects in key(property1):val(property2)
        """
        if not val:
            return {getattr(k, key):k for k in self.all}
        
        return {getattr(k, key):getattr(k, val) for k in self.all}

    @property
    def n(self):
        """Return the number of instances being tracked."""
        return len(self.all)

    def query(self, queryStr="agent == 'sausage' and accuracy > 0.7", keys=None):
        """
        Filter all tracked objects based on object fields (keys).
        
        :param queryStr: list-comprehension style filter string
        :param keys: list of object keys used in the query
        :returns: a subset of tracked objects that satisfy query criteria
        :raises Warning: prints processed query string if the query fails

        Refer to tests for examples and notes on how to use.
        """
        if not queryStr:
            return self.all

        def parseQuery(queryStr):
            queryUnits = re.split(r'and|or', queryStr)
            queryUnits = [queryUnit.lstrip(' ').lstrip('(').lstrip(' ') for queryUnit in queryUnits]
            for queryUnit in queryUnits:
                if ' in ' not in queryUnit:
                    queryStr = queryStr.replace(queryUnit, 'k.'+queryUnit)

            queryStr = queryStr.replace(' in ', ' in k.')
            return queryStr

        if keys is None:
            queryStr = parseQuery(queryStr)
        else:
            for key in keys:
                queryStr = queryStr.replace(key, 'k.'+key)

        try:
            objList = eval("[k for k in self.all if " + queryStr + "]") #pylint:disable=eval-used
        except Warning:
            print('Query failed.')
            print(queryStr)
        return objList

    def clean(self):
        """Forget the objects tracked so far."""
        self.all = []
    
    def clear_cache(self):
        """Clear cache used by temporary tracking sessions."""
        self.cache = []

    def track_start(self):
        """
        Start a tracking session. Move current objects to cache, and clean.
        Note that objects are tracked even without this method if a class is being tracked.
        Use this to create temporary tracking sessions.
        """
        self.cache = self.all
        self.clean()

    def track_end(self):
        """End tracking session."""
        self.all = self.cache
        self.clear_cache()
