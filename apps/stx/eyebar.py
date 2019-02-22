"""Eye bar modifications for the marmoset stereotax."""

import os
import sys

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../..'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

import bpn # pylint: disable=unused-import

bpy = bpn.bpy
bpy.data.scenes['Scene'].cursor_location[0] = -100

bpn.reset_blender()

import numpy as np

# load the original eyebar mesh from Gilbert Menon 2019
eyebar_path = os.path.realpath(r"D:\GDrive Columbia\issalab_data\Marmoset stereotax\Gilbert Menon 2019\EyeBar.STL")
m = bpn.msh(bpn.loadSTL(eyebar_path)['meshes'][0])

height_frac = 0.70 # modulate the height of the eyebar by this fraction
inc_length = 10 # mm increase the length (keep the hole out of this)
inc_hole = 5 # mm increase the hole by this amount

coords = m.v
# squish along y
sel = coords[:, 1] > 3
coords[sel, 1] = coords[sel, 1]*height_frac
# stretch along x (without the hole)
selX = coords[:, 0] > 20
coords[selX, 0] = coords[selX, 0] + inc_length
# increase the hole
selX = np.logical_and(coords[:, 0] > 10, coords[:, 0] < 20)
coords[selX, 0] = coords[selX, 0] + inc_hole
m.v = coords


# addonPath = os.path.realpath(r'C:\blender\2.80.0\2.80\scripts\addons')
# if addonPath not in sys.path:
#     sys.path.append(addonPath)
# from io_mesh_stl.stl_utils import read_stl

# objName = bpy.path.display_name(os.path.basename(path))
# tris, tri_nors, pts = stl_utils.read_stl(path)
# tri_nors = tri_nors if self.use_facet_normal else None
# blender_utils.create_and_link_mesh(objName, tris, tri_nors, pts, global_matrix)

# TODO: Put this in bpn (make meshes from stl, find meshes from blender workspace, create meshes from faces and vertices)
# # How to make a mesh using vertices and triangles
# tris, tri_nors, pts = read_stl(eyebar_path)
# def makeMesh(name, v, f):
#     mesh = bpy.data.meshes.new(name)
#     mesh.from_pydata(v, [], f)
#     mesh.update()

#     obj = bpy.data.objects.new(name, mesh)
#     bpy.context.collection.objects.link(obj)
#     bpy.context.view_layer.objects.active = obj
#     obj.select_set(True)
#     return mesh

# mBpy = makeMesh('eyeBar', pts, tris)
