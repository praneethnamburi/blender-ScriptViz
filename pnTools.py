import errno
import functools
import importlib
import inspect
import os
import sys
import subprocess

## General utilities - Decorators
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
        if isinstance(thisDirFiles, str):
            thisDirFiles = [thisDirFiles]
        for dirFile in thisDirFiles:
            if not os.path.exists(dirFile):
                raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), dirFile)
        return thisDirFiles

# General utilities - Decorators - output modifiers
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
def pkglist():
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

def pkgpath():
    _, pkgNames, _ = pkglist()
    for pkgName in pkgNames:
        currPkgDir = importlib.import_module(str(pkgName).lower().replace('-', '_')).__file__
    return currPkgDir

## introspection
def functionInputs(func):
    inputVarNames = [str(k) for k in inspect.signature(func).parameters.keys()]
    defaultValues = [inspect.signature(func).parameters[k].default for k in [str(k) for k in inspect.signature(func).parameters.keys()]]
    return inputVarNames, defaultValues

def getmembers(mod, includeSubModules=True):
    members = {}
    for name, data in inspect.getmembers(mod):
        if name.startswith('__') or (inspect.ismodule(data) and not includeSubModules):
            continue
        members[name] = str(type(inspect.unwrap(data))).split("'")[1]
    return members

def printDict(myDict):
    [print(k, ':', myDict[k]) for k in myDict]
