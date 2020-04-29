# context.area: VIEW_3D
"""
This is a sandbox. Develop code here!
"""
#-----------------
from bpn_init import * # pylint: disable=wildcard-import, unused-wildcard-import
pn.reload()
env.reset()
#-----------------

from apps import anatomy

SKELETON = "D:\\Dropbox (MIT)\\Anatomy\\Workspace\\Ultimate_Human_Anatomy_Rigged_Blend_2-81\\skeletalSystem_originAtCenter_bkp02.blend"

anatomy.load_coll('Skeletal_Sys', SKELETON)

hip_articulation_center = (-0.10529670119285583, 0.007387260906398296, 0.9325617551803589)
# original knee articulation center
rot_frame_hip = trf.CoordFrame(origin=hip_articulation_center)
knee_articulation_center_orig = trf.PointCloud((-0.10663662105798721, 0.03164456784725189, 0.5140388011932373), np.eye(4)).in_frame(rot_frame_hip)

leg_bones = env.Props().get_children('Leg_Bones_R') - set(env.Props().get('Ilium_R'))
leg_bones_enh = [utils.enhance(b) for b in leg_bones]

q_hip = trf.Quat([1, 0, 0], -3*np.pi/180, rot_frame_hip)

n_keyframes = 22
all_frames = {}
for bone in leg_bones_enh:
    all_frames[bone.name] = {}
    for kf in range(n_keyframes):
        all_frames[bone.name][kf] = bone.frame # original frame

# apply transformation around the hip joint
for kf in range(1, n_keyframes):
    q_hip = trf.Quat([1, 0, 0], -3*kf*np.pi/180, rot_frame_hip)
    for bone in leg_bones_enh:
        all_frames[bone.name][kf] = q_hip*all_frames[bone.name][kf]

# apply transformation around the femur
for kf in range(1, n_keyframes):
    q_hip = trf.Quat([1, 0, 0], -3*kf*np.pi/180, rot_frame_hip)
    knee_articulation_center = q_hip*knee_articulation_center_orig
    q_knee = trf.Quat([1, 0, 0], 3.5*kf*np.pi/180, trf.CoordFrame(origin=knee_articulation_center.in_world().co[0, :]))
    for bone in leg_bones_enh:
        if bone.name != 'Femur_R':
            all_frames[bone.name][kf] = q_knee*all_frames[bone.name][kf]

# Display in blender
for kf in range(n_keyframes):
    for bone in leg_bones_enh:
        bone.frame = all_frames[bone.name][kf]
        bone.key(kf+1) # blender keyframes are 1-indexed
