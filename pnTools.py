import os
import errno
import functools
import inspect

### Exceptions
def raiseNotFoundError(thisDirFiles):
    if isinstance(thisDirFiles, str):
        thisDirFiles = [thisDirFiles]
    for dirFile in thisDirFiles:
        if not os.path.exists(dirFile):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), dirFile)

### General utilities (don't require blender)
## General utilities - Decorators 
# exception handling
class checkIfOutputExists:
    """This decorator function raises an error if the output does not exist on disk"""
    def __init__(self, func):
        self.func = func
        functools.update_wrapper(self, func)
    def __call__(self, *args, **kwargs):
        funcOut = self.func(*args, **kwargs)
        raiseNotFoundError(funcOut)
        return funcOut

# General utilities - Decorators - output modifiers
class baseNames:
    """This decorator function returns just the file names if func's output consists of full file paths"""
    def __init__(self, func):
        self.func = func
        functools.update_wrapper(self, func)
    def __call__(self, *args, **kwargs):
        funcOut = self.func(*args, **kwargs)
        funcOutBase = [os.path.basename(k) for k in funcOut]
        return funcOutBase

## General utilities - Functions
@checkIfOutputExists
def getFileName_full(fPath, fName):
    fullName = os.path.join(os.path.normpath(fPath), fName)
    return fullName

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