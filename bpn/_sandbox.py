# context.area: VIEW_3D
"""
This is a sandbox. Develop code here!
"""
#-----------------
from bpn_init import * # pylint: disable=wildcard-import, unused-wildcard-import
pn.reload()
env.reset()
#-----------------

# get humerus into blender

filepath = "D:\\Dropbox (MIT)\\Anatomy\\Workspace\\Ultimate_Human_Anatomy_Rigged_Blend_2-81\\skeletalSystem_originAtCenter.blend"
assert os.path.exists(filepath)

bones = ['Humerus_R', 'Scapula_R', 'Clavicle_R', 'Radius_R', 'Ulna_R']
with bpy.data.libraries.load(filepath) as (data_from, data_to):
    data_to.objects = [name for name in data_from.objects if name in bones]

print(data_to.objects)
col = new.collection('Bones')
for obj in data_to.objects:
    if obj is not None:
        col.objects.link(obj)

h = get('Humerus_R')
print(h.pts)

from sklearn.decomposition import PCA
pca = PCA(n_components=3)
pca.fit(h.v)
print(pca.explained_variance_ratio_)
# Frm(pca.components_, origin=h.pts.in_world().center.co[0, :]).show('normal', scale=0.1)
# Frm(pca.components_.T, origin=h.pts.in_world().center.co[0, :]).show('transpose', scale=0.1)

# h.frame = Frm(pca.components_.T, origin=h.bo.location)
pc1_dir = -pca.components_.T[:, 0]
pc2_dir = pca.components_.T[:, 1]
pc3_dir = pca.components_.T[:, 2] #np.cross(pc1_dir, pc2_dir)
h.pts = h.pts.reframe(Frm(i=pc1_dir, j=pc2_dir, k=pc3_dir, origin=h.bo.location))
