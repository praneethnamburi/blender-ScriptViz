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