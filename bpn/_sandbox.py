# context.area: VIEW_3D
"""
This is a sandbox. Develop code here!
"""
#-----------------
from bpn_init import * # pylint: disable=wildcard-import, unused-wildcard-import
pn.reload()
env.reset()
#-----------------

from sklearn.decomposition import PCA

def reframe_pca(coremsh):
    """Reframe core.msh object h """
    pca = PCA(n_components=3)
    pca.fit(coremsh.v)
    # convention:
    # Z is the direction 'away from the floor' in the up cycle
    # So, for long bones, Z is the first principal component
    pc1_dir = pca.components_.T[:, 0]
    pc3_dir = pca.components_.T[:, 2]
    z_dir = pc1_dir if pc1_dir[-1] < 0 else -pc1_dir
    x_dir = pc3_dir if pc3_dir[0] > 0 else -pc3_dir
    y_dir = np.cross(z_dir, x_dir)
    coremsh.pts = coremsh.pts.reframe(Frm(i=x_dir, j=y_dir, k=z_dir, origin=coremsh.bo.location))
    # coremsh.frame.show(scale=0.1)
    coremsh.update_normals()

def center_rig(loc):
    """Load circular rig and focus on 'loc' with camera and lighting."""
    resources.load_rig('circularRig')
    bpy.data.objects['Target'].location = Vector(loc)
    rig_objs = [o for o in bpy.data.objects if o.name.startswith('BezierCircle_')]
    rig_center = np.mean([np.array(o.location) for o in rig_objs], axis=0)
    # bring the center of the rig (z) to the bone's center
    new_center = np.array((0, 0, loc[-1]))
    for o in rig_objs:
        o.location += Vector(new_center - rig_center)

def get_traj(xlname='armReach_ineffTrial'):
    fname = 'D:\\Workspace\\blenderPython\\apps\\animation\\'+xlname+'.xlsx'
    sheet_name = 'animation'
    pt_names = ['RH_AcromioClavicular', 'RH_ElbowLat', 'RH_ElbowMed']

    data = pd.read_excel(fname, sheet_name)

    pd.unique(data['object'])
    pd.unique(data['attribute'])

    np.sum([data['object'] == 'RH_AcromioClavicular'])

    # create a frame from 3 points
    loc = lambda ob: np.vstack(data[(data['object'] == ob) & (data['attribute'] == 'location')]['value'].apply(eval).to_numpy())
    norm = lambda n: np.sqrt(np.sum(n**2, axis=1, keepdims=True))
    hat = lambda n: n/norm(n)
    
    anatomy_frame = Frm(i=(-1, 0, 0), j=(0, 0, 1), k=(0, 1, 0))
    pos = {ob: PC(loc(ob), np.eye(4)).in_frame(anatomy_frame).co for ob in pt_names}
    origin = pos['RH_AcromioClavicular']
    k_hat = hat((pos['RH_ElbowLat'] + pos['RH_ElbowMed'])/2 - origin)
    j_hat = hat(pos['RH_ElbowLat'] - pos['RH_ElbowMed'])
    i_hat = hat(np.cross(j_hat, k_hat)) # should already be normalized

    return [trf.CoordFrame(origin=o, i=i, j=j, k=k) for o, i, j, k in zip(origin, i_hat, j_hat, k_hat)]


bone_names = ['Humerus_R', 'Scapula_R', 'Clavicle_R']
bones = resources.load_bones(bone_names)
h = bones['Humerus_R']
reframe_pca(h)
# center_rig(h.frame.origin)
traj = get_traj('armReach_ineffTrial')

# rot_origin = h.pts.in_world().co[np.argmin(h.v[:, -1]), :]
# force origin in all the coordinate frames to be at humerus z minimum

dist = lambda p1, p2: np.sqrt(np.sum((np.array(p1) - np.array(p2))**2))

rot_origin = (-0.076826, -0.18167, 1.46056)

for frm in traj:
    frm.origin = rot_origin
# traj[0].show('traj0', scale=0.1)

for i, tr in enumerate(traj):
    # represent humerus' frame in the current rotation frame
    tmp1 = h.frame.as_points().in_frame(tr)
    # origin is at a fixed distance in the z-direction
    tmp1.co[0, :] = np.array([0, 0, dist(tmp1.co[0, :], (0, 0, 0))])
    # specify unit vector locations in the rotation frame
    tmp1.co[1:, :] = np.eye(3) + tmp1.co[0, :]
    # convert back to frame in world coordinates
    h.frame = tmp1.in_world().as_frame()
    # h.frame.show(scale=0.1)
    h.key(i+1, 'lr')
