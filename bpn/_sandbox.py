# context.area: VIEW_3D
"""
This is a sandbox. Develop code here!
"""
#-----------------
from bpn_init import * # pylint: disable=wildcard-import, unused-wildcard-import
pn.reload()
# env.reset()
#-----------------

# def get_traj(xlname='armReach_ineffTrial'):
#     fname = 'D:\\Workspace\\blenderPython\\apps\\animation\\'+xlname+'.xlsx'
#     sheet_name = 'animation'
#     pt_names = ['RH_AcromioClavicular', 'RH_ElbowLat', 'RH_ElbowMed']

#     data = pd.read_excel(fname, sheet_name)

#     pd.unique(data['object'])
#     pd.unique(data['attribute'])

#     np.sum([data['object'] == 'RH_AcromioClavicular'])

#     # create a frame from 3 points
#     loc = lambda ob: np.vstack(data[(data['object'] == ob) & (data['attribute'] == 'location')]['value'].apply(eval).to_numpy())/10
#     norm = lambda n: np.sqrt(np.sum(n**2, axis=1, keepdims=True))
#     hat = lambda n: n/norm(n)
    
#     anatomy_frame = Frm(i=(-1, 0, 0), j=(0, 0, 1), k=(0, 1, 0))
#     pos = {ob: PC(loc(ob), np.eye(4)).in_frame(anatomy_frame).co for ob in pt_names}
#     origin = pos['RH_AcromioClavicular']
#     k_hat = hat((pos['RH_ElbowLat'] + pos['RH_ElbowMed'])/2 - origin)
#     j_hat = hat(pos['RH_ElbowLat'] - pos['RH_ElbowMed'])
#     i_hat = hat(np.cross(j_hat, k_hat)) # should already be normalized

#     return pos, [trf.CoordFrame(origin=o, i=i, j=j, k=k) for o, i, j, k in zip(origin, i_hat, j_hat, k_hat)]


# bone_names = ['Humerus_R', 'Scapula_R', 'Clavicle_R']
# bones = resources.load_bones(bone_names)
# for bone in bones.values():
#     bone.update_normals()
# h = bones['Humerus_R']
# h.pts = reframe_pca(h.pts)
# h.update_normals()
# he = h.copy('H_effcopy')
# hi = h.copy('H_ineffcopy')
# h.bo.hide_set(True)
# c = resources.CircularRig()
# c.center = h.frame.origin
# pos_eff, traj_eff = get_traj('armReach_effTrial')
# pos_ineff, traj_ineff = get_traj('armReach_ineffTrial')

# # rot_origin = h.pts.in_world().co[np.argmin(h.v[:, -1]), :]
# # force origin in all the coordinate frames to be at humerus z minimum

# dist = lambda p1, p2: np.sqrt(np.sum((np.array(p1) - np.array(p2))**2))

# rot_origin = (-0.076826, -0.18167, 1.46056)


# for h, traj in zip((he, hi), (traj_eff, traj_ineff)):
#     for frm in traj:
#         frm.origin = rot_origin

#     for i, tr in enumerate(traj):
#         # represent humerus' frame in the current rotation frame
#         tmp1 = h.frame.as_points().in_frame(tr)
#         # origin is at a fixed distance in the z-direction
#         tmp1.co[0, :] = np.array([0, 0, dist(tmp1.co[0, :], (0, 0, 0))])
#         # specify unit vector locations in the rotation frame
#         tmp1.co[1:, :] = np.eye(3) + tmp1.co[0, :]
#         # convert back to frame in world coordinates
#         h.frame = tmp1.in_world().as_frame()
#         h.key(i+1, 'lr')
#         c.key(i+1, targ='target', value=h.frame.origin)

# # zooming in
# c.key(1, 'fov', 120)
# c.key(100, 'fov', 40)

# pc_eff = Pencil('eff', layer_name='elbow_lat')
# crd = pos_eff['RH_ElbowLat'] - pos_eff['RH_AcromioClavicular'] + np.array(rot_origin)
# pc_eff.stroke(PC(crd, np.eye(4)), color=1, keyframe=0, layer='elbow_lat', line_width=6)
# crd = pos_eff['RH_ElbowMed'] - pos_eff['RH_AcromioClavicular'] + np.array(rot_origin)
# pc_eff.stroke(PC(crd, np.eye(4)), color=1, keyframe=0, layer='elbow_med', line_width=6)

# pc_ineff = Pencil('ineff', layer_name='elbow_lat')
# crd = pos_ineff['RH_ElbowLat'] - pos_ineff['RH_AcromioClavicular'] + np.array(rot_origin)
# pc_ineff.stroke(PC(crd, np.eye(4)), color=2, keyframe=0, layer='elbow_lat', line_width=6)
# crd = pos_ineff['RH_ElbowMed'] - pos_ineff['RH_AcromioClavicular'] + np.array(rot_origin)
# pc_ineff.stroke(PC(crd, np.eye(4)), color=2, keyframe=0, layer='elbow_med', line_width=6)

# traj_eff[0].show(scale=0.1)

# h = resources.load_bones(['Humerus_R'])['Humerus_R']

# h.pts = h.pts.reframe_pca(z_dir=-1)
# h.update_normals()

arm_bone_names = [b.name for b in list(Props().get_children('Arm_Bones_L')) + list(Props().get_children('Arm_Bones_R'))]
for this_obj in bpy.data.objects:
    if this_obj.type == 'MESH':
        o = get(this_obj.name)
        o.pts = o.pts.reframe_pca(i=3, k=1-2*int(this_obj.name in arm_bone_names)) # down for arm bones
        o.update_normals()
