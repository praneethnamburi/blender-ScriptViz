"""Demonstrate matrix multiplication on points forming 2d objects using blender."""

from bpn_init import * #pylint: disable=wildcard-import, unused-wildcard-import

bpy.data.scenes['Scene'].cursor.location[0] = -10

if 'Plane' not in [o.name for o in bpy.data.objects]:
    msh = new.plane(name='Plane')
else:
    msh = get('Plane')

coords = msh.v.T

# Exercises:
# 1. Stretch the square by 2 along the X axis
# 2. Rotate the square by 45 degrees
# 3. Is this the only way to rotate the square?
# 4. Shear the square
# 5. Make the square disappear.
m1 = np.array([\
    [1, 0, 0],\
    [0, 1, 0],\
    [0, 0, 1]\
    ])

newCoords = m1@coords

msh.v = newCoords.T
