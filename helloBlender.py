import bpy
from random import randint

n = 500
for i in range(0,n):
    x = randint(-30, 30)
    y = randint(-30, 30)
    z = randint(-30, 30)
    bpy.ops.mesh.primitive_monkey_add(location=(x,y,z))