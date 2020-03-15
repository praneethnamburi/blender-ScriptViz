"""
Praneeth's tools for making life easy while coding in python.

Modules:
    classmethods: Methods that can be added to classes using pntools.AddMethods.
        properties: Print all the properties in this class.

Decorators: 
    **Tracker: Provide database-like access accross all objects created by a class. 
    AddMethods: Add methods to a class.
    Time: Prints execution time when a function is decorated.
    -OnDisk: Ensure function output is on disk. 
    -BaseNames: Return only file names (if function outputs full paths) 

Classes:

Functions: 
    ospath: Find a file on your computer. Return full path.
    locateCommand: Locate an executable on your computer. Useful to
        ensure correct executable is being used.
    --getFileName_full: Return full file name and ensure file on disk

    pkgList: List packages. Uses pip freeze.
    pkgPath: List path to a [package list]. Fails for several packages.

    functionInputs: Input variable names and default values of a function.
    getmembers: Members of a module.
    printDict: Print a dictionary to the command line.

I/O:
    dbxmeta: Download metadata recursively from a dropbox folder into a pickled file
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
from timeit import default_timer as timer

if __package__ is not None:
    from . import classmethods as cm

## General utilities - Decorators

class AddMethods:
    """
    Add methods to a class. Decorator.
    
    Usage:
        @AddMethods([pntools.cm.properties])
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

class Tracker:
    """
    Keep track of all instances of objects created by a class.
    This converts a class into a Tracker object. 
    To keep a class as a class, use inheritance with the Track class.
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

class Track:
    """
    The Tracker class converts a class into an object, and therefore, is very inconvenient when it comes to module imports.
    In that case, use this class like so:
        class TestClass(Track):
        def __init__(self, num):
            self.num = num
            # self.track(self)
            super().__init__() # include this line at the end of __init__ after inheritance
    """
    all = []
    cache = []
    def __init__(self):
        self.track(self)

    @classmethod
    def track(cls, obj):
        """Just used by the initalization function to track object."""
        cls.all.append(obj)
    
    @classmethod
    def clear(cls):
        """Forget the objects tracked so far."""
        cls.all = []
    
    @classmethod
    def clear_cache(cls):
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
    def dictAccess(cls, key='id', val=None):
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

class OnDisk:
    """
    Raise error if function output not on disk. Decorator.

    :param func: function that outputs a path/directory
    :returns: decorated function with output handling
    :raises keyError: FileNotFoundError if func's output is not on disk
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

class BaseNames:
    """
    Return file names given full paths.
    
    :param func: function that outputs a list of names of files
    :returns: decorated function that outputs only basenames
    """
    def __init__(self, func):
        self.func = func
        functools.update_wrapper(self, func)
    def __call__(self, *args, **kwargs):
        funcOut = self.func(*args, **kwargs)
        funcOutBase = [os.path.basename(k) for k in funcOut]
        return funcOutBase

class Time:
    """
    Prints execution time. Decorator.
    Note that this only works on functions.
    Consider a function call:
    out1 = m.inflate(0.15, 0.1, 0.02, 100)
    Using the following will give the output in addition to printing the
    execution time.
    out1 = my.Time(m.inflate)(0.15, 0.1, 0.02, 100)
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

## General utilities - Functions
@OnDisk
def getFileName_full(fPath, fName):
    """Full file name given the path and the name. Ensure file on disk."""
    fullName = os.path.join(os.path.normpath(fPath), fName)
    return fullName

## File system
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
    else:
        print('Did not find ', errContent)
        return ''

def locateCommand(thingToFind, requireStr=None, verbose=True):
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
    else:
        if verbose:
            print('Terminal found: ', thingPath)
        if requireStr is not None:
            if requireStr not in thingPath:
                print('Path to ' + thingToFind + ' does not have ' + requireStr + ' in it!')
                return ''
        return thingPath

## Package management
def pkgList():
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

def pkgPath(pkgNames=None):
    """Return path to installed packages."""
    if not pkgNames:
        _, pkgNames, _ = pkgList()
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
def functionInputs(func):
    """Get the input variable names and default values to a function."""
    inputVarNames = []
    defaultValues = []
    if callable(func):
        inputVarNames = [str(k) for k in inspect.signature(func).parameters.keys()]
        defaultValues = [inspect.signature(func).parameters[k].default for k in [str(k) for k in inspect.signature(func).parameters.keys()]]
    return inputVarNames, defaultValues

def getmembers(mod, includeSubModules=True):
    """Return members of a module."""
    members = {}
    for name, data in inspect.getmembers(mod):
        if name.startswith('__') or (inspect.ismodule(data) and not includeSubModules):
            continue
        members[name] = str(type(inspect.unwrap(data))).split("'")[1]
    return members

def printDict(myDict):
    """Print a dictionary in the command line."""
    [print(k, ':', myDict[k]) for k in myDict] #pylint: disable=expression-not-assigned

## Dropbox
def dbxmeta(dbxAuth='./_auth/mkturk_dropbox.json', dbxPath='/mkturkfiles/imagebags/objectome', savName=None, cachePath='./_temp'):
    """
    Download metadata recursively from all entries in a dropbox folder.
    Save the metadata in the temporary cache of the project. 
    Return the metadata entries. For mkturk images, use these entries
    with the class mkturkImg.
    """
    
    if not savName:
        savName = f"{cachePath}/{dbxPath[1:].replace('/', '_')}.dbxmeta"

    if not os.path.exists(savName):
        print("Downloading metadata from dropbox path: ", dbxPath)
        import dropbox
        dbx = dropbox.Dropbox(json.loads(open(dbxAuth).read())['DBX_MKTURK_TOKEN'])
        allFiles = dbx.files_list_folder(dbxPath, recursive=True)
        entries = allFiles.entries
        while allFiles.has_more:
            allFiles = dbx.files_list_folder_continue(allFiles.cursor)
            entries = entries + allFiles.entries

        dlTime = datetime.datetime.now().isoformat()
        with open(savName, 'wb') as f:
            pickle.dump([entries, dlTime], f)
        print("Picked metadata at: ", savName)
    else:
        print("Reading from temporary cache: ", savName)
        with open(savName, 'rb') as f:
            entries, dlTime = pickle.load(f)

    return entries, dlTime

# input handling
def clean_kwargs(kwargs, kwargs_def, kwargs_alias):
    """
    Clean keyword arguments based on default values and aliasing.

    :param kwargs: (dict) input kwargs that require cleaning.
    :param kwargs_def: (dict) should have all the possible keyword arguments.
    :param kwargs_alias: (dict) lists all possible aliases for each keyword.
        {kw1: [kw1, kw1_alias1, ..., kw1_aliasn], ...}
        kw1 is used inside the function, but kw1=val, kw1_alias1=val, ..., kw1_aliasn are all valid

    Returns: 
        (dict) keyword arguments after cleaning. Ensures all keywords are present, and have the names used in the function.
        (dict) remaining keyword arguments
    """
    for k in kwargs_def:
        for ka in kwargs_alias[k]:
            if ka in kwargs:
                kwargs_def[k] = kwargs.pop(ka)

    return kwargs_def, kwargs
    