import bpn # pylint: disable=unused-import

bpy = bpn.bpy
bpy.data.scenes['Scene'].cursor.location[0] = -100

# bpn.env.reset()

bpy.ops.mesh.primitive_cube_add(location=(1.0, 0.0, 0.0))

m = bpn.Msh(name='Cube')
m.v = m.v*2
