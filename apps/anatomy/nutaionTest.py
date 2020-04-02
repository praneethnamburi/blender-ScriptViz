"""
Support for nutations.
"""
from bpn_init import *
pn.reload()

FRAME_INIT = 1
FRAME_INRIGHT = 100
FRAME_OUTRIGHT = 200

import mathutils # pylint: disable=import-error

def setOriginToCenter(obj_name):
    """Bring every bone's origin to center."""
    new_origin = mathutils.Vector(get(obj_name).center)
    bpy.data.objects[obj_name].data.transform(mathutils.Matrix.Translation(-new_origin))
    bpy.data.objects[obj_name].matrix_world.translation += new_origin

def locRotKeyFrame(obj_name, frameNum=1):
    """Set location and rotation keyframes for a given object."""
    bpy.data.objects[obj_name].keyframe_insert(data_path="location", frame=frameNum)
    bpy.data.objects[obj_name].keyframe_insert(data_path="rotation_euler", frame=frameNum)

def initBones():
    """
    Run this code once after importing the skeletal system from ultimate human anatomy file.
    I changed the rotation and the scale manually so the units make sense, and then ran this script
    """
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            setOriginToCenter(obj.name)
            locRotKeyFrame(obj.name, FRAME_INIT)
            locRotKeyFrame(obj.name, FRAME_INRIGHT)
            locRotKeyFrame(obj.name, FRAME_OUTRIGHT)

# Rotate the skeleton by 90 degrees around Z
tfmat = np.array(Matrix.Rotation(np.pi/2, 4, 'Z'))
tfmat2 = np.linalg.inv(tfmat)
for this_obj in bpy.data.objects:
    if this_obj.type == 'MESH':
        o = get(this_obj.name)
        o.frame = o.frame.transform(tfmat)
        o.frame = o.frame.transform(tfmat2, o.frame)
        o.pts = o.pts.transform(tfmat)
        # o.pts = o.pts.transform(tfmat, np.eye(4))
        # o.apply_matrix()
        # setOriginToCenter(this_obj.name)
# bpy.ops.wm.open_mainfile(filepath="D:\\Dropbox (MIT)\\Anatomy\\Workspace\\Ultimate_Human_Anatomy_Rigged_Blend_2-81\\skeletalSystem.blend", display_file_selector=False)
# initBones()

### Saving nutations to excel, and applying them in another blend file

# # (load skeletalSystem.blend in blender)
# fname = r'D:\Workspace\blenderPython\apps\anatomy\nutations.xlsx'
# p2 = bpn.io.readattr('Skeletal_Sys', [1, 100], ['location', 'rotation_euler'], fname)

# (load skeletalSystem_originAtCenter_bkp02.blend)
# fname = r'D:\Workspace\blenderPython\apps\anatomy\nutations.xlsx'
# bpn.io.animate_simple(fname)
