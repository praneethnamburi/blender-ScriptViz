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
# knee_articulation_center = (-0.11157135665416718, -0.3444276750087738, 0.7093947529792786)


leg_bones = env.Props().get_children('Leg_Bones_R') - set(env.Props().get('Ilium_R'))
leg_bones_enh = [utils.enhance(b) for b in leg_bones]

rot_frame_hip = trf.CoordFrame(origin=hip_articulation_center)
q_hip = trf.Quat([1, 0, 0], -3*np.pi/180, rot_frame_hip)

# original knee articulation center
knee_articulation_center_orig = trf.PointCloud((-0.10663662105798721, 0.03164456784725189, 0.5140388011932373), np.eye(4)).in_frame(rot_frame_hip)

knee_articulation_center = knee_articulation_center_orig
for bone in leg_bones_enh:
    bone.key(1)

for kf in range(2, 22):
    # get new knee articulation center
    knee_articulation_center = q_hip*knee_articulation_center
    # create secondary transform
    q_knee = trf.Quat([1, 0, 0], 3.5*np.pi/180, trf.CoordFrame(origin=knee_articulation_center.in_world().co[0, :]))
    for b in leg_bones_enh:
        # apply primary transform for all bones
        b.frame = q_hip*b.frame
        if b.name != 'Femur_R':
            # apply seconday transform for all bones except femur
            b.frame = q_knee*b.frame
        b.key(kf)


