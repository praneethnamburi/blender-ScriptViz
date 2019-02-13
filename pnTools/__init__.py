"""
Praneeth's tools for making life easy while coding in python.
"""

import datetime
import errno
import functools
import importlib
import inspect
import json
import os
import pickle
import sys
import subprocess
from timeit import default_timer as timer

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
        def wrapperFunc(*args, **kwargs):
            for method in self.methodList:
                setattr(func, method.__name__, method)
            funcOut = func(*args, **kwargs)
            return funcOut
        return wrapperFunc

class Tracker:
    """
    Keep track of all instances of objects created by a class
    clsToTrack. Decorator.

    :param clsToTrack: keep track of objects created by this class
    :returns: a tracker object

    For operations that span across all objects created by a clsToTrack,
    you can simply create a groupOperations class without __new__,
    __init__ or __call__ functions, and decorate clsToDecorate with that
    class. See tests for an example.
    """
    tracked = []
    def __new__(cls, clsToTrack):
        cls.tracked.append(clsToTrack)
        return object.__new__(cls)
    def __init__(self, clsToTrack):
        self.clsToTrack = clsToTrack
        functools.update_wrapper(self, clsToTrack)
        self._nInst = 0
        self._all = []
    def __call__(self, *args, **kwargs):
        funcOut = self.clsToTrack(*args, **kwargs)
        self._nInst += 1
        self._all.append(funcOut)
        return funcOut
    def __delitem__(self, item):
        """
        Stop tracking item.
        item is an instance of clsToTrack
        """
        self._all.remove(item)
        self._nInst = len(self._all)
    def dictAccess(self, key='id'):
        """
        Give access to the object based on key. If keys (id) of
        different objects are the same, then only the last reference
        will be preserved.
        """
        return {getattr(k, key):k for k in self._all}

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
    def checkFiles(self, thisFileList):
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

def locateCommand(thingToFind, requireStr=None):
    """
    Locate an executable in on your computer.

    :param thingToFind: string name of the executable (e.g. python)
    :param requireStr: require path to thingToFind to have a certain string
    :returns: Full path (like realpath) to thingToFind if it exists
              Empty string if thing does not exist
    """
    if sys.platform == 'linux':
        queryCmd = 'which'
    elif sys.platform == 'win32':
        queryCmd = 'where'
    proc = subprocess.Popen(queryCmd+' '+thingToFind, stdout=subprocess.PIPE, shell=True)
    thingPath = proc.communicate()[0].decode('utf-8').rstrip('\n').rstrip('\r')
    if not thingPath:
        print('Terminal cannot find ', thingToFind)
        return ''
    else:
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
    [print(k, ':', myDict[k]) for k in myDict]

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
