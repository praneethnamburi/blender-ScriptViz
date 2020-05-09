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

def init_bones():
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

def rotate_skeleton():
    """Rotate the skeleton by 90 degrees around Z"""
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

def reframe_bones_pca():
    """Reframe bones in PCA space of each bone"""
    arm_bone_names = [b.name for b in list(env.Props().get_children('Arm_Bones_L')) + list(env.Props().get_children('Arm_Bones_R'))]
    for this_obj in bpy.data.objects:
        if this_obj.type == 'MESH':
            o = get(this_obj.name)
            o.pts = o.pts.reframe_pca(i=3, k=1-2*int(this_obj.name in arm_bone_names)) # down for arm bones
            o.update_normals()

# bpy.ops.wm.open_mainfile(filepath="D:\\Dropbox (MIT)\\Anatomy\\Workspace\\Ultimate_Human_Anatomy_Rigged_Blend_2-81\\skeletalSystem.blend", display_file_selector=False)
# init_bones()

### Saving nutations to excel, and applying them in another blend file

# # (load skeletalSystem.blend in blender)
# fname = r'D:\Workspace\blenderPython\apps\anatomy\nutations.xlsx'
# p2 = bpn.io.readattr('Skeletal_Sys', [1, 100], ['location', 'rotation_euler'], fname)

# (load skeletalSystem_originAtCenter_bkp02.blend)
# fname = r'D:\Workspace\blenderPython\apps\anatomy\nutations.xlsx'
# bpn.io.animate_simple(fname)

def save_nutation_coordframes():
    """Pickle Nutation trf.CoordFrame objects"""
    from apps import anatomy
    import pickle

    SKELETON = "D:\\Dropbox (MIT)\\Anatomy\\Workspace\\Ultimate_Human_Anatomy_Rigged_Blend_2-81\\skeletalSystem_originAtCenter_bkp02.blend"
    anatomy.load_coll('Skeletal_Sys', SKELETON)

    fname = r'D:\Workspace\blenderPython\apps\anatomy\nutations.xlsx'
    bpn.io.animate_simple(fname)

    leg_bones = env.Props().get_children('Leg_Bones_R')
    leg_bones = [utils.enhance(b) for b in leg_bones]

    env.Key().goto(100)
    nutation_in = {}
    for bone in leg_bones:
        nutation_in[bone.name] = bone.frame

    env.Key().goto(1)
    nutation_out = {}
    for bone in leg_bones:
        nutation_out[bone.name] = bone.frame

    sav_file = os.path.join(os.path.dirname(anatomy.__file__), 'nutations.pkl')
    with open(sav_file, 'wb') as f:
        pickle.dump([nutation_in, nutation_out], f)

    print('Saved nutations to : ' + sav_file)

def load_nutation_coordframes():
    """Load picked nutations"""
    from apps import anatomy
    import pickle

    sav_file = os.path.join(os.path.dirname(anatomy.__file__), 'nutations.pkl')
    with open(sav_file, 'rb') as f:
        nutation_in, nutation_out = pickle.load(f)
    return nutation_in, nutation_out

def apply(frac=0.5):
    """Apply nutations to bones.
    frac is in the interval (0, 1). Practically, it is a function of external force distribution.
    """
    nutations_in, nutations_out = load_nutation_coordframes()
    nutation_trf_local = {} # out to in specified in the local frame of the bone (so you can apply it anywhere
    if frac > 0:
        for bone_name in nutations_in:
            nutation_trf_local[bone_name] = nutations_in[bone_name].as_points().in_frame(nutations_out[bone_name]).as_frame().m
    else:
        for bone_name in nutations_in: # in to out
            nutation_trf_local[bone_name] = nutations_out[bone_name].as_points().in_frame(nutations_in[bone_name]).as_frame().m
    frac = np.abs(frac)
    for bone_name in nutations_in:
        tfmat = nutation_trf_local[bone_name]
        tfmat = np.eye(4) + (tfmat - np.eye(4))*frac
        utils.get(bone_name).frame = utils.get(bone_name).frame.transform(tfmat, utils.get(bone_name).frame)
