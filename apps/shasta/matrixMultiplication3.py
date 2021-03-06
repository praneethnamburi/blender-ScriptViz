"""Demonstrate matrix multiplication on points forming 3d objects using blender."""

from bpn_init import * #pylint: disable=wildcard-import, unused-wildcard-import

bpy.data.scenes['Scene'].cursor.location[0] = -10

msh = get('Suzy')
if not msh:
    msh = bpn.new.monkey('Suzy')

coords = msh.v.T

# Exercises:
# 1. Make the monkey look away
# 2. Make the monkey's face thin
# 3. make the monkey look around (chaining transforms)

m1 = np.array([\
    [1, 0.95, 0],\
    [0.95, 1, 0],\
    [0, 0, 1]\
    ])

newCoords = m1@coords

# make sure you're in object mode
msh.v = newCoords.T

# coords = msh.v
# for i, co in enumerate(coords):
#     coords[i] = coords[i] + 0.01*np.random.randn(3)
# msh.v = coords

# λ = 0
# δλ = np.pi/6
# λ = λ + δλ
# m1 = np.array([\
#     [np.cos(λ), -np.sin(λ), 0],\
#     [np.sin(λ), np.cos(λ), 0],\
#     [0, 0, 1]\
#     ])
