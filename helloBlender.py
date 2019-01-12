import bpy #pylint: disable=import-error
from random import randint

n = 5
for i in range(0,n):
    x = randint(-5, 5)
    y = randint(-5, 5)
    z = randint(-5, 5)
    bpy.ops.mesh.primitive_monkey_add(location=(x,y,z))    