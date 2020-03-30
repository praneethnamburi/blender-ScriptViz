from bpn_init import *
pn.reload()
env.reset()

gp = GP(gp_name='myGP', obj_name='myGPobj', coll_name='myColl', layer_name='sl1')

θ = np.radians(np.arange(0, 360*2+1, 1))
z1 = np.sin(θ)
y1 = np.cos(θ)
x1 = θ/2

pc1 = PC(np.vstack((x1, y1, z1)).T, trf.normal2tfmat((1, 1, 1)))
pc2 = PC(np.vstack((x1, y1, z1)).T, trf.normal2tfmat((0, 0, 1)))
gp.stroke(pc1, color=2, layer='sl1', keyframe=0)
gp.stroke(pc2, color=1, layer='sl3', keyframe=10)
gp.stroke(pc1, color=2, layer='sl1', keyframe=20, line_width=100)
gp.keyframe = 30

# bpy.data.grease_pencils[0].layers['sl1'].frames[1].clear() # removes the stroke, but there is still a keyframe
# bpy.data.grease_pencils[0].layers['sl1'].clear() # removes all keyframes and strokes

# show the frame for point cloud 1
pcf = pc1.frame.as_points()
gp.layer = 'crd'
gp.stroke(PC(pcf.co[[0, 1]]), color='crd_i', line_width=80)
gp.stroke(PC(pcf.co[[0, 2]]), color='crd_j', line_width=80)
gp.stroke(PC(pcf.co[[0, 3]]), color='crd_k', line_width=80)
