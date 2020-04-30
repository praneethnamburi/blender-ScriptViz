"""
Create poses
"""

import numpy as np

from bpn import trf, env, utils
from apps import anatomy

def leg_lift():
    """Creates an animation for lifting the leg and putting it back down."""
    # load the skeleton
    SKELETON = "D:\\Dropbox (MIT)\\Anatomy\\Workspace\\Ultimate_Human_Anatomy_Rigged_Blend_2-81\\skeletalSystem_originAtCenter_bkp02.blend"
    anatomy.load_coll('Skeletal_Sys', SKELETON)

    n_keyframes = 22

    hip_articulation_center_world = (-0.10529670119285583, 0.007387260906398296, 0.9325617551803589)
    knee_articulation_center_world = (-0.10663662105798721, 0.03164456784725189, 0.5140388011932373)
    ankle_articulation_center_world = (-0.1197955459356308, 0.06532438099384308, 0.06592987477779388)

    hip_articulation_angle = -66*np.pi/180
    knee_articulation_angle = 77*np.pi/180
    ankle_articulation_angle = 1*np.pi/180

    hip_articulation_center_rel_ilium = trf.PointCloud(hip_articulation_center_world, np.eye(4)).in_frame(utils.get('Ilium_R').frame).co[0, :]
    knee_articulation_center_rel_femur = trf.PointCloud(knee_articulation_center_world, np.eye(4)).in_frame(utils.get('Femur_R').frame).co[0, :]
    ankle_articulation_center_rel_tibia = trf.PointCloud(ankle_articulation_center_world, np.eye(4)).in_frame(utils.get('Tibia_R').frame).co[0, :]

    def _transform_bones(bones, articulation_center_rel, articulation_center_frames, articulation_angle):
        """
        :param bones: (list of bpn.core.MeshObject) list of bones to be transformed
        :param articulation_center_rel: (3-element np array) location of the center of transformation. The position of the rotation center does not change in this frame.
        :param articulation_center_frames: (list of CoordFrames, same length as number of keyframes) 
            The coordinate frame in which articulation center is specified (specifies the frame in world coordinates)
        :param articulation angle: (radians) how much to articulate that joint
        """
        for tkf in range(1, n_keyframes):
            articulation_center = trf.PointCloud(articulation_center_rel, articulation_center_frames[tkf]).in_world().co[0, :]
            q = trf.Quat([1, 0, 0], articulation_angle*tkf/n_keyframes, trf.CoordFrame(origin=articulation_center))
            for b in bones:
                all_frames[b.name][tkf] = q*all_frames[b.name][tkf]

    # get all leg bones from the right leg
    leg_bones = env.Props().get_children('Leg_Bones_R')
    leg_bones = [utils.enhance(b) for b in leg_bones]

    # Initialize coordinate frames for every keyframe for every bone
    all_frames = {}
    for bone in leg_bones:
        all_frames[bone.name] = {}
        for kf in range(n_keyframes):
            all_frames[bone.name][kf] = bone.frame # original frame

    # apply transformation around the hip joint
    exc_list = ['Ilium_R']
    bone_list = [b for b in leg_bones if b.name not in exc_list]
    _transform_bones(bone_list, hip_articulation_center_rel_ilium, all_frames['Ilium_R'], hip_articulation_angle)

    # apply transformation around the femur
    exc_list += ['Femur_R']
    bone_list = [b for b in bone_list if b.name not in exc_list]
    _transform_bones(bone_list, knee_articulation_center_rel_femur, all_frames['Femur_R'], knee_articulation_angle)

    # apply transformation around the tibia
    exc_list += ['Tibia_R', 'Fibula_R', 'Patella_R']
    bone_list = [b for b in bone_list if b.name not in exc_list]
    _transform_bones(bone_list, ankle_articulation_center_rel_tibia, all_frames['Tibia_R'], ankle_articulation_angle)

    # Insert keyframes for transformed bones in blender
    for kf in range(n_keyframes):
        for bone in leg_bones:
            bone.frame = all_frames[bone.name][kf]
            bone.key(kf+1) # blender keyframes are 1-indexed
            bone.key(3*n_keyframes+1-kf) # leg goes back down
    
    env.Key().auto_lim()

if __name__ in ('__main__', '<run_path>'):
    leg_lift()
    