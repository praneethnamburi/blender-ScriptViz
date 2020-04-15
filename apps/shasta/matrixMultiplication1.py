"""Demonstrate matrix multiplication on points using blender."""

from bpn_init import * #pylint: disable=wildcard-import, unused-wildcard-import

bpy.data.scenes['Scene'].cursor.location[0] = -10

origin = [0, 0, 0]
v1 = [1, 2, 0]

# Exercises
# 1. Make the vector in orange twice its size
# 2. Scale only the X axis by a factor of 2
# 3. Rotate the vector by 90 degrees
# 4. Rotate the vector by a given angle theta
# 5. Reflect the vector along the line x=y
m1 = np.array([\
    [1, 0, 0],\
    [0, 1, 0],\
    [0, 0, 0]\
    ])

v2 = m1@v1

verts = {'v1': v1, 'v2':v2}

for vertName, vertPos in verts.items():
    if vertName not in [o.name for o in bpy.data.objects]:
        new.mesh(name=vertName, x=[origin[0], vertPos[0]], y=[origin[1], vertPos[1]], z=[origin[2], vertPos[2]])
    else:
        get(vertName).v = np.array([origin, vertPos])
