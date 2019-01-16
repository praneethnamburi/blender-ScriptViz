import bpy #pylint: disable=import-error
import numpy as np
from math import sin

m = bpy.data.meshes.new('sin')

n = 100

# make a mesh
m.vertices.add(n)
m.edges.add(n-1)
yVals = np.linspace(0, 10, 100)

for i,y in zip(range(n), yVals):
    m.vertices[i].co = (0, y, sin(y))

    if i < n-1:
        m.edges[i].vertices = (i, i+1)

# make an object from that mesh, an object is an instantiation of a mesh
o = bpy.data.objects.new('sin'+'1', m)

bpy.context.scene.collection.objects.link( o )