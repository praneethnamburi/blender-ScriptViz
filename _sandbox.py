"""
This is a sandbox. Develop code here!
"""
# Don't touch this
import os
import sys
import bpn # pylint: unused-import

if os.path.dirname(os.path.realpath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))

# add modules here
bpy = bpn.bpy

def main():
    """Actual development happens here"""
    bpy.ops.mesh.primitive_monkey_add()
    bpy.ops.object.modifier_add(type='TRIANGULATE')
    m = bpn.msh(bpy.data.meshes[0])
    m.inflate()

if __name__ == '__main__' or __name__ == '<run_path>':
    main()