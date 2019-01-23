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