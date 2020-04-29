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

leg_bones = env.Props().get_children('Leg_Bones_R')
leg_bones = [utils.enhance(b) for b in leg_bones]

hip_articulation_center_world = (-0.10529670119285583, 0.007387260906398296, 0.9325617551803589)
knee_articulation_center_world = (-0.10663662105798721, 0.03164456784725189, 0.5140388011932373)
ankle_articulation_center_world = (-0.1197955459356308, 0.06532438099384308, 0.06592987477779388)

hip_articulation_angle = -66*np.pi/180
knee_articulation_angle = 77*np.pi/180
ankle_articulation_angle = 33*np.pi/180
n_keyframes = 22

hip_articulation_center_rel_ilium = trf.PointCloud(hip_articulation_center_world, np.eye(4)).in_frame(get('Ilium_R').frame).co[0, :]
knee_articulation_center_rel_femur = trf.PointCloud(knee_articulation_center_world, np.eye(4)).in_frame(get('Femur_R').frame).co[0, :]
ankle_articulation_center_rel_tibia = trf.PointCloud(ankle_articulation_center_world, np.eye(4)).in_frame(get('Tibia_R').frame).co[0, :]

def _transform_bones(bones, articulation_center_rel, articulation_center_frames, articulation_angle):
    for tkf in range(1, n_keyframes):
        articulation_center = trf.PointCloud(articulation_center_rel, articulation_center_frames[tkf]).in_world().co[0, :]
        q = trf.Quat([1, 0, 0], articulation_angle*tkf/n_keyframes, trf.CoordFrame(origin=articulation_center))
        for b in bones:
            all_frames[b.name][tkf] = q*all_frames[b.name][tkf]

all_frames = {}
for bone in leg_bones:
    all_frames[bone.name] = {}
    for kf in range(n_keyframes):
        all_frames[bone.name][kf] = bone.frame # original frame

# apply transformation around the hip joint
exc_list = ['Ilium_R']
bone_list = [b for b in leg_bones if b.name not in exc_list]
# _transform_bones(bone_list, hip_articulation_center_rel_ilium, all_frames['Ilium_R'], hip_articulation_angle)
for kf in range(1, n_keyframes):
    hip_articulation_center = trf.PointCloud(hip_articulation_center_rel_ilium, all_frames['Ilium_R'][kf]).in_world().co[0, :]
    q_hip = trf.Quat([1, 0, 0], hip_articulation_angle*kf/n_keyframes, trf.CoordFrame(origin=hip_articulation_center))
    for bone in bone_list:
        all_frames[bone.name][kf] = q_hip*all_frames[bone.name][kf]

# apply transformation around the femur
exc_list += ['Femur_R']
bone_list = [b for b in bone_list if b.name not in exc_list]
for kf in range(1, n_keyframes):
    knee_articulation_center = trf.PointCloud(knee_articulation_center_rel_femur, all_frames['Femur_R'][kf]).in_world().co[0, :]
    q_knee = trf.Quat([1, 0, 0], knee_articulation_angle*kf/n_keyframes, trf.CoordFrame(origin=knee_articulation_center))
    for bone in bone_list:
        all_frames[bone.name][kf] = q_knee*all_frames[bone.name][kf]

# apply transformation around the tibia
exc_list += ['Tibia_R', 'Fibula_R', 'Patella_R']
bone_list = [b for b in bone_list if b.name not in exc_list]
for kf in range(1, n_keyframes):
    ankle_articulation_center = trf.PointCloud(ankle_articulation_center_rel_tibia, all_frames['Tibia_R'][kf]).in_world().co[0, :]
    q_ankle = trf.Quat([1, 0, 0], ankle_articulation_angle*kf/n_keyframes, trf.CoordFrame(origin=ankle_articulation_center))
    for bone in bone_list:
        all_frames[bone.name][kf] = q_ankle*all_frames[bone.name][kf]

# Display in blender
for kf in range(n_keyframes):
    for bone in leg_bones:
        bone.frame = all_frames[bone.name][kf]
        bone.key(kf+1) # blender keyframes are 1-indexed
