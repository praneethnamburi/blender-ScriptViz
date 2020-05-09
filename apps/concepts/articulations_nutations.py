"""
Creates a leg pose with articulations, and then adds nutations

To run the setup part of this code from a blender console, use:
exec(''.join(open('apps/concepts/articulations_nutations.py').readlines()[0:117]))

Used these videos in the slides:
Luca lab documentation -> 20200430 NCSOFT awardees meeting.pptm
"""
import numpy as np

import bpy #pylint: disable=import-error

from bpn import io, env, utils, trf, new
from apps import anatomy
from apps.anatomy import nutations

# dark background
env.background((0, 0, 0))

# Establishing shot
est_frames = 35
c = new.CircularRig()
bpy.context.scene.camera = c.camera()
c.key(1, 'theta', 3*np.pi/2)
c.key(est_frames, 'theta', np.pi-15*np.pi/180)
c.key(1, 'fov', 90)
c.key(est_frames, 'fov', 37)
c.key(1, 'center', (0, 0, 1))
c.key(est_frames, 'center', (0, 0, 0.4))
c.key(1, 'target', (0, 0, 1))
c.key(est_frames, 'target', (0, 0, 0.25))

keyframe_offset = est_frames

nutations_in, nutations_out = nutations.load_nutation_coordframes()

nutation_trf_out2in = {}
nutation_trf_in2out = {}
for bone_name in nutations_in:
    nutation_trf_out2in[bone_name] = trf.CoordFrame(nutations_in[bone_name].m@np.linalg.inv(nutations_out[bone_name].m))
    nutation_trf_in2out[bone_name] = trf.CoordFrame(nutations_out[bone_name].m@np.linalg.inv(nutations_in[bone_name].m))

if 'Skeletal_Sys' not in [c.name for c in bpy.data.collections]:
    SKELETON = "D:\\Dropbox (MIT)\\Anatomy\\Workspace\\Ultimate_Human_Anatomy_Rigged_Blend_2-81\\skeletalSystem_originAtCenter_bkp02.blend"
    anatomy.load_coll('Skeletal_Sys', SKELETON)

n_keyframes = 22
n_keyframes_nutation = 20
n_keyframes_hold = 10

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
        progress = (tkf/n_keyframes)**1
        q = trf.Quat([1, 0, 0], articulation_angle*progress, trf.CoordFrame(origin=articulation_center))
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

# add nutations
for bone in leg_bones:
    all_frames[bone.name]['nutation_in'] = trf.CoordFrame(nutation_trf_out2in[bone.name].m@all_frames[bone.name][0].m)

# Insert keyframes for transformed bones in blender
for kf in range(n_keyframes):
    for bone in leg_bones:
        bone.frame = all_frames[bone.name][kf]
        bone.key(keyframe_offset + n_keyframes-kf) # blender keyframes are 1-indexed
        bone.key(keyframe_offset + n_keyframes + 2*n_keyframes_nutation + n_keyframes_hold + kf + 1)

env.Key().lim = (1, est_frames)
env.Key().goto(1)
io.render('est_01_start', 'img')
env.Key().goto(est_frames)
io.render('est_02_end', 'img')
io.render('est_shot')

# hide bones in the left leg
hidden_bones = env.Props().get_children('Leg_Bones_L')
for bone in hidden_bones:
    utils.enhance(bone).hide()

io.render('est_03_end_hide', 'img')

env.Key().auto_lim()
env.Key().start = est_frames + 1

io.render('leg articulation without nutation')

# Insert keyframes for nutation
for bone in leg_bones:
    bone.frame = all_frames[bone.name]['nutation_in']
    bone.key(keyframe_offset + n_keyframes + n_keyframes_nutation)
    bone.key(keyframe_offset + n_keyframes + n_keyframes_nutation + n_keyframes_hold)

io.render('leg articulation with nutation')

print('Done')
