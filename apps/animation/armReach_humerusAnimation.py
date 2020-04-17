"""
Animate motion capture trajectory with bones.
"""

#-----------------
from bpn_init import * # pylint: disable=wildcard-import, unused-wildcard-import
pn.reload()
env.reset()
#-----------------

PC = trf.PointCloud

def get_traj(xlname='armReach_ineffTrial'):
    fname = 'D:\\Workspace\\blenderPython\\apps\\animation\\'+xlname+'.xlsx'
    sheet_name = 'animation'
    pt_names = ['RH_AcromioClavicular', 'RH_ElbowLat', 'RH_ElbowMed']

    data = pd.read_excel(fname, sheet_name)

    # create a frame from 3 points
    loc = lambda ob: np.vstack(data[(data['object'] == ob) & (data['attribute'] == 'location')]['value'].apply(eval).to_numpy())/10
    norm = lambda n: np.sqrt(np.sum(n**2, axis=1, keepdims=True))
    hat = lambda n: n/norm(n)
    
    anatomy_frame = trf.CoordFrame(i=(-1, 0, 0), j=(0, 0, 1), k=(0, 1, 0))
    pos = {ob: PC(loc(ob), np.eye(4)).in_frame(anatomy_frame).co for ob in pt_names}
    origin = pos['RH_AcromioClavicular']
    k_hat = hat((pos['RH_ElbowLat'] + pos['RH_ElbowMed'])/2 - origin)
    j_hat = hat(pos['RH_ElbowLat'] - pos['RH_ElbowMed'])
    i_hat = hat(np.cross(j_hat, k_hat)) # should already be normalized

    return pos, [trf.CoordFrame(origin=o, i=i, j=j, k=k) for o, i, j, k in zip(origin, i_hat, j_hat, k_hat)]

bone_names = ['Humerus_R', 'Scapula_R', 'Clavicle_R']
bones = resources.load_bones(bone_names)
for bone in bones.values():
    bone.update_normals()
h = bones['Humerus_R']
h.pts = h.pts.reframe_pca(k=-1, i=3)
h.update_normals()
he = h.copy('H_effcopy')
hi = h.copy('H_ineffcopy')
h().hide_set(True)
c = new.CircularRig()
c.center = h.frame.origin
pos_eff, traj_eff = get_traj('armReach_effTrial')
pos_ineff, traj_ineff = get_traj('armReach_ineffTrial')

dist = lambda p1, p2: np.sqrt(np.sum((np.array(p1) - np.array(p2))**2))

rot_origin = (-0.076826, -0.18167, 1.46056) # set manually!!

for h, traj in zip((he, hi), (traj_eff, traj_ineff)):
    for frm in traj:
        frm.origin = rot_origin

    for i, tr in enumerate(traj):
        # represent humerus' frame in the current rotation frame
        tmp1 = h.frame.as_points().in_frame(tr)
        # origin is at a fixed distance in the z-direction
        tmp1.co[0, :] = np.array([0, 0, dist(tmp1.co[0, :], (0, 0, 0))])
        # specify unit vector locations in the rotation frame
        tmp1.co[1:, :] = np.eye(3) + tmp1.co[0, :]
        # convert back to frame in world coordinates
        h.frame = tmp1.in_world().as_frame()
        h.key(i+1, 'lr')
        c.key(i+1, targ='target', value=h.frame.origin)

c.key(1, 'camera_angle', 0)
c.key(40, 'camera_angle', -np.pi/4)

# zooming in
c.key(1, 'fov', 120)
c.key(100, 'fov', 40)

# Draw trajectories!
pc_eff = new.pencil('eff', layer_name='elbow_lat')
crd = pos_eff['RH_ElbowLat'] - pos_eff['RH_AcromioClavicular'] + np.array(rot_origin)
pc_eff.stroke(PC(crd, np.eye(4)), color=1, keyframe=0, layer='elbow_lat', line_width=6)
crd = pos_eff['RH_ElbowMed'] - pos_eff['RH_AcromioClavicular'] + np.array(rot_origin)
pc_eff.stroke(PC(crd, np.eye(4)), color=1, keyframe=0, layer='elbow_med', line_width=6)

pc_ineff = new.pencil('ineff', layer_name='elbow_lat')
crd = pos_ineff['RH_ElbowLat'] - pos_ineff['RH_AcromioClavicular'] + np.array(rot_origin)
pc_ineff.stroke(PC(crd, np.eye(4)), color=2, keyframe=0, layer='elbow_lat', line_width=6)
crd = pos_ineff['RH_ElbowMed'] - pos_ineff['RH_AcromioClavicular'] + np.array(rot_origin)
pc_ineff.stroke(PC(crd, np.eye(4)), color=2, keyframe=0, layer='elbow_med', line_width=6)

traj_eff[0].show(scale=0.1)
