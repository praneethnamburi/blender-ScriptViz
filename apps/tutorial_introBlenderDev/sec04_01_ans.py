from bpn_init import * # pylint: disable=wildcard-import, unused-wildcard-import

bpy.data.scenes['Scene'].cursor.location[0] = -10

# env.reset()

m = new.cube(name='Cube')
m.v = m.v*2
