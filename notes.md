# Questions to guide development

1. How to clean up the scene at the beginning of a script?
2. How to animate?
3. Import meshes programatically from files
4. Overlay maps as textures over the meshes

- Try Chris Conlan's commands in the command window (to make sure they work in blender 2.8), and then using VScode
- Also see what works and what doesn't work in VScode's debug mode

## get the names of all objects

objNames = [k.name for k in bpy.data.objects]

## list of collections

collList = [k.name for k in bpy.data.collections]

## names of objects in a collection

[k.name for k in bpy.data.collections['Collection'].objects]

## names of objects in the current scene

[k.name for k in bpy.context.scene.collection.objects]

## reference an object

myObj = bpy.data.objects['sin1.002']

## get the vertices of a referenced object

myVert = myObj.data.vertices

## get vertex coordinates of an object

coords = [(o.matrix_world * v.co) for v in o.data.vertices]

## move a referenced object (object-specific)

o.location = (-2.0, -2.0, -2.0)
bpy.data.objects['sin'].location = (0.0, 2.0, 1.0)
bpy.ops.transform.translate(value=(-2,0,0)) #this is discouraged!

## set the position of an object using a 'trf' matrix

o.matrix_world = ((1.0, 0.0, 0.0, 0.0), (0.0, 1.0, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0))

## change the coordinate of a vertex

since can be done through a mesh or an object, but better do this using a mesh because changing it through an object changes the mesh anyway

m = bpy.data.meshes['sin.004'] # refernce a mesh
coords = [v.co for v in m.vertices] # get vertices
m.vertices[2].co = Vector((1, 0, 2)) # Vector is in mathutils.Vector, and appears to be a blender built-in thing

## select all objects

for obj in bpy.data.objects:
    obj.select_set(True)