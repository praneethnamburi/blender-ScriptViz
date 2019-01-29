# Notes

## Next steps

1. Import meshes from STL files
2. Add color to vertices of these meshes

## Questions to guide development

1. How to clean up the scene at the beginning of a script?
      - This does the job in the command line: bpy.ops.wm.read_homefile()
2. How to animate?
3. Import meshes programatically from files
4. Overlay maps as textures over the meshes
5. How to assign object to a collection
6. WTF is a depsgraph?

- Try Chris Conlan's commands in the command window (to make sure they work in blender 2.8), and then using VScode
- Also see what works and what doesn't work in VScode's debug mode

### get the names of all objects

      objNames = [k.name for k in bpy.data.objects]

### list of collections

      collList = [k.name for k in bpy.data.collections]

### names of objects in a collection

      [k.name for k in bpy.data.collections['Collection'].objects]

### names of objects in the current scene

      [k.name for k in bpy.context.scene.collection.objects]

### reference an object

      myObj = bpy.data.objects['sin1.002']

### get the vertices of a referenced object

      myVert = myObj.data.vertices

### get vertex coordinates of an object

```python
coords = [(o.matrix_world * v.co) for v in o.data.vertices]
```

### move a referenced object (object-specific)

```python
o.location = (-2.0, -2.0, -2.0)
o.rotation_euler = (pi/3, 0, 0) # radians!!
bpy.data.objects['sin'].location = (0.0, 2.0, 1.0)
bpy.ops.transform.translate(value=(-2,0,0)) #this is discouraged!
```

### set the position of an object using a 'trf' matrix

o.matrix_world = ((1.0, 0.0, 0.0, 0.0), (0.0, 1.0, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0))

### change the coordinate of a vertex

since can be done through a mesh or an object, but better do this using a mesh because changing it through an object changes the mesh anyway

```python
m = bpy.data.meshes['sin.004'] # refernce a mesh
coords = [v.co for v in m.vertices] # get vertices
m.vertices[2].co = Vector((1, 0, 2)) # Vector is in mathutils.Vector, and appears to be a blender built-in thing
```

### select all objects

```python
for obj in bpy.data.objects:
    obj.select_set(True)
```

### add a modifier to a referenced object

```python
mod = myObj.modifiers.new("Skin", "SKIN")
```

### IMPORTANT: calling a function when its name is in a string

This is the python equivalent of how MATLAB evaluates myStruct.(myVar)  
but more general!

```python
import numpy as np
myVar = 'arange'
getattr(np, myVar)(0, 5, 2)
```

This gives [0,2,4]

## Errors

### file not found

```python
if not os.path.exists(fullName):
    raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), fullName)
```

## Examples

### Example - adding stuff at random locations

```python
# context.area: VIEW_3D
import bpy #pylint: disable=import-error
from random import randint

n = 25
m = []
for i in range(0,n):
    x = randint(-5, 5)
    y = randint(-5, 5)
    z = randint(-5, 5)
    bpy.ops.mesh.primitive_monkey_add(location=(x,y,z))

for i in range(0,n):
    bpy.ops.mesh.primitive_uv_sphere_add(location=[randint(-10,10) for axis in 'xyz'])
```

### Example - basic animation in blender

```python
import bpy #pylint: disable=import-error

positions = (0,0,0), (-5,1,1), (1,3,3), (4,3,6), (4,10,6)

start_pos = (1,10,1)

ob = bpy.data.objects["Sphere"]

frame_num = 0

for position in positions:
    bpy.context.scene.frame_set(frame_num)
    ob.location = position
    ob.keyframe_insert(data_path="location", index=-1)
    frame_num += 20
```

### Example - creating an object

```python
import bpy #pylint: disable=import-error
import numpy as np
from math import sin

m = bpy.data.meshes.new('sin')

n = 100

//# make a mesh
m.vertices.add(n)
m.edges.add(n-1)
yVals = np.linspace(0, 10, 100)

for i,y in zip(range(n), yVals):
    m.vertices[i].co = (0, y, sin(y))

    if i < n-1:
        m.edges[i].vertices = (i, i+1)

//# make an object from that mesh, an object is an instantiation of a mesh
o = bpy.data.objects.new('sin'+'1', m)

bpy.context.scene.collection.objects.link( o )
```

### Event handlers. Wow!!

This code shows a way to change mesh vertices every time a frame is updated.

```python
import bpy
import bmesh
import numpy as np

## ------- part 1 --- do this once.
sig = 0.3
n_frames = 101
bpy.context.scene.frame_end = n_frames

## PN Note - this part didn't work in blender 2.8
pi = np.pi
make_ico = bpy.ops.mesh.primitive_ico_sphere_add
make_ico(subdivisions=3, size = 2.0, location = (0,0,3))
obj = bpy.context.active_object
me = obj.data
##

ico0 = np.array([v.co for v in me.vertices]) # get ico vertices
zmin, zmax = ico0[:,2].min(), ico0[:,2].max()
zc = np.linspace(zmin, zmax, n_frames)
ico = np.zeros_like(ico0)
data = []

for i in range(n_frames):
    ico[:,:2] = (1.0 + np.exp(-(ico0[:,2] - zc[i])**2/(2.*sig**2)))[:,None] * ico0[:,:2]
    ico[:,2] = ico0[:,2]
    data.append(ico.copy())

## ------- part 2  ---set up frame change event handler,
def my_handler(scene):
    i_frame = scene.frame_current
    if not (0 <= i_frame < len(data)):
        return

    obj = bpy.data.objects['Icosphere'] # be explicit.
    me = obj.data
    for (vert, co) in zip(me.vertices, data[i_frame]):
        vert.co = co
    me.update()

## attach the event handler to bpy
bpy.app.handlers.frame_change_pre.append(my_handler)
```

```python
# to remove all handlers, say
bpy.app.handlers.frame_change_pre.clear()
```

## Decorators in python

A decorator takes a function and returns a function. In the example below, smart_divide is a decorator that takes the function divide and returns a function, let's say smart_divide, and call it divide again. Therefore, the function chkDivideByZero is *decorating* the function *divide* by adding some functionality. More generally, I need to wrap my head around passing functions as arguments

```python
def chkDivideByZero(func):
   def inner(a,b):
      print("I am going to divide",a,"and",b)
      if b == 0:
         print("Whoops! cannot divide")
         return

      return func(a,b)
   return inner

@chkDivideByZero
def divide(a,b):
    return a/b
```

### two ways of defining decorators

```python
# Class syntax for making a decorator
class baseNames:
    def __init__(self, func):
        self.f = func
    def __call__(self, *args, **kwargs):
        # input validation code goes here
        fOut = self.f(*args, **kwargs)
        # output validation code goes here
        # output modification code goes here
        fOut2 = [os.path.basename(k) for k in fOut]
        return fOut2

# function syntax for making a decorator
def baseNames(func):
    """This decorator function returns just the file names in case full file paths are used"""
    def funcWithBaseNameOutput(*args, **kwargs):
        # input validation code goes here
        fOut = func(*args, **kwargs)
        # output validation and modification code goes here
        fOutBase = [os.path.basename(k) for k in fOut]
        return fOutBase
    return funcWithBaseNameOutput

# using the decorator
@baseNames
def getMeshNames(fPath=marmosetAtlasPath(), searchStr='smooth'):
    mshNames = glob.glob(fPath + '*' + searchStr + '*.stl')
    return mshNames
```

Remember that the above syntax of using the decorator (@basenames) just before a function definition translates to redefining the function getMeshNames like so:

```python
getMeshNames = baseNames(getMeshNames)
```

If you call it without using the decorator, it will be the equivalent of saying:  
baseNames(getMeshNames)(searchStr='smooth')

Also note that there are two parentheses after baseNames. You can access two functions of a python class using two sets of parentheses, the first set executes the __init__() method wrapper and the second set executes the __call__() method wrapper. Each of those can have arguments of their own.

Another decorator example

```python
# decorator - takes a function: function to be decorated
def checkIfOutputExistsFDEF(func):
    """This decorator function raises an error if the output does not exist on disk"""
    # makes a new function: the decorated function
    def funcWithChecking(*args, **kwargs):
        output = func(*args, **kwargs)
        raiseNotFoundError(output)
        return output
    # returns the new function
    return funcWithChecking
```

And this would be the same as calling

```python
baseNames(getMeshNames)(searchStr='smooth')
```

Parameters in parentheses 2 get passed to the object in parentheses 1

Decorators can improve code readability. If a reader is just trying to understand the core concepts of the code, then they can skip over the decorator definitions and simply focus on the 'core' functions

### Decorators with arguments

```python
class ReportDelta:
    """This decorator reports what changed in the scene after the decorated function is executed"""
    def __init__(self, deltaType='objects'): # what changed? report 'objects' or 'meshes'
        self.deltaType = deltaType
    def __call__(self, func):
        def deltaAfterFunc(*args, **kwargs):
            namesBefore = [k.name for k in getattr(bpy.data, self.deltaType)]
            funcOut = func(*args, **kwargs)
            if not isinstance(funcOut, dict):
                funcOut = {'funcOut': funcOut}
            namesAfter = [k.name for k in getattr(bpy.data, self.deltaType)] # read: bpy.data.objects
            funcOut['new'+self.deltaType.capitalize()] = list(set(namesAfter)-set(namesBefore))
            return funcOut
        return deltaAfterFunc

# It can also be redefined using def like so:
def ReportDelta(deltaType='meshes'):
    def deltaAfterFunc(func):
        # tell what kind of modification
        def nameGenerationFunction(*args, **args):
                # find names before
                funcOutput = func(*args, **args)
                # find names after, modify funcOutput
            return modifiedFuncOutput
        return nameGenerationFunction
    return deltaAfterFunc

@ReportDelta(deltaType='objects')
@ReportDelta(deltaType='meshes')
def loadSTL(fPath=marmosetAtlasPath(), searchStr='*smooth*.stl', collName = 'Collection'):
    fNames=getMeshNames(fPath, searchStr)
    for fName in fNames:
        bpy.ops.import_mesh.stl(filepath=getFileName_full(fPath, fName))

ReportDelta(deltaType='objects')(ReportDelta(deltaType='meshes')(loadSTL))

# alternate syntax
loadSTL = ReportDelta(deltaType='meshes')(loadSTL)(searchStr='*123*.stl')
# this is equivalent to:
tmp1 = bpy.b.ReportDelta(deltaType='meshes')
# tmp1 is <bpn.ReportDelta object at 0x7fc0ea199470>
tmp2 = tmp1(bpy.b.loadSTL)
# tmp2 is <function ReportDelta.__call__.<locals>.deltaAfterFunc at 0x7fc13f7e06a8>
tmp2(searchStr='*123*.stl')
# this is the final evaluation that produces the output
# h(g(f(x)))  h(g)(f)(x)
# ReportDelta(deltaType='meshes')(loadSTL)(searchStr='*123*.stl')
```

Another way of doing the same thing: can't use the decorator syntax in this case, but you can modify a function using another function nonetheless

```python
def reportDeltaAlt(func, deltaType='meshes'):
    def deltaAfterFunc(*args, **kwargs):
        namesBefore = [k.name for k in getattr(bpy.data, deltaType)]
        funcOut = func(*args, **kwargs)
        if not isinstance(funcOut, dict):
            funcOut = {'funcOut': funcOut}
        namesAfter = [k.name for k in getattr(bpy.data, deltaType)] # read: bpy.data.objects
        funcOut['new'+deltaType.capitalize()] = list(set(namesAfter)-set(namesBefore))
        return funcOut
    return deltaAfterFunc

loadSTL2 = reportDeltaAlt(reportDeltaAlt(loadSTL, deltaType='meshes'), deltaType='objects')
# call as loadSTL2(searchStr='*142*.stl')
```

You can do the same thing using classes, which might be easier to read

```python
class reportDeltaAlt:
    def __init__(self, func, deltaType='meshes'):
        # func is any function that ideally changes the scene in blender
        self.func = func
        self.deltaType = deltaType
    def __call__(self, *args, **kwargs):
        namesBefore = [k.name for k in getattr(bpy.data, deltaType)]
        funcOut = self.func(*args, **kwargs)
        if not isinstance(funcOut, dict):
            funcOut = {'funcOut': funcOut}
        namesAfter = [k.name for k in getattr(bpy.data, deltaType)] # read: bpy.data.objects
        funcOut['new'+deltaType.capitalize()] = list(set(namesAfter)-set(namesBefore))
        return funcOut
```

The syntax is not as nice (the part where I load STL2). This way is easier to understand though! So, stick to the class method of using decorators? Remember, whatever is in the first set of parentheses calls the __init__ function, and whatever is in the second set of parenteses calls the __call__ function of a class

### Executing a script from the python console

Use this code to execute a script within the python console. Then everything within that script is accessible in the python console's workspace

```python
filename = '/home/praneeth/Workspace/blenderPython/pn_test1.py'
exec(compile(open(filename).read(), filename, 'exec'))
```

Here is a test script. Run the two commands in the python console, and here is an example of pn_test1.py

```python
import pymesh
print('testPrint')
```

## Old way of launching blender from the terminal

```python
### Use the command blender --python launch.py in the terminal to launch blender

# add custom module locations to system path
# note that the appended paths persist
import sys
sys.path.append('/home/praneeth/Workspace/blenderPython')


## import custom modules
import bpn as b

## store them in bpy
'''this is the only way by which I managed to send data from the command line to the python console inside blender'''
import bpy #pylint: disable=import-error
bpy.b = b

## do stuff on startup
# b.demo_animateDNA()
```

## New way of launching blender from the terminal

Step 1: Put everything you want to type into the blender python terminal into a file (call it startupContents.py)

Step 2: Put the following code in a separate script, either on its own, or if there are other commands in that script, then simply use the if __name__ == '__main__' trick, which is shown below. So, for the latter strategy, place this code at the end of a script, say bpn.py

```python
#strategy #1 - make a file with these three lines as the contents, say launch.py
import bpy
import os
launchFileName = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'startupContents.py')
bpy.loadStr = open(launchFileName).read()
```

```python
# strategy #2 - put this at the end of a file, say bpn.py
if __name__ == '__main__':
    launchFileName = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'startupContents.py')
    bpy.loadStr = open(launchFileName).read()
```

Step 3: For strategy #1, launch blender from the terminal using blender --python launch.py
        For strategy #2, launch blender from the terminal using blender --python bpn.py

Step 4: execute the command (exec bpy.loadStr)

### Dealing with bpy py lint errors

Import bpy and other built-in modules into bpn ONLY, and import bpn in all the other scripts, and get bpy and other modules from the bpn import

### Readme

Files that start with _ add functionality, and you shouldn't need to use
them if you're an end user

### Understand and setup debugging

Currently, this is what F5 is doing:

cd /home/praneeth/Workspace/blenderPython ; (cd to current working directory)

env "PYTHONIOENCODING=UTF-8" "PYTHONUNBUFFERED=1" (set some environment variables)

/home/praneeth/blender/2.80.0/2.80/python/bin/python3.7m (choose the executable)

/home/praneeth/.vscode/extensions/ms-python.python-2018.12.1/pythonFiles/ptvsd_launcher.py--default
--client --host localhost --port 43051 (supply debugger to the exe)

/home/praneeth/Workspace/blenderPython/_requirementsCheck.py 
(supply your script to the executable)