# context.area: VIEW_3D
"""
This is a sandbox. Develop code here!
"""
#-----------------
from bpn_init import * # pylint: disable=wildcard-import, unused-wildcard-import
pn.reload()
env.reset()
#-----------------

grid_scale = 0.4 # 0.4 => 0.4 m in the world is 1 unit in coordinate frame
grid_lim = 8 # how many lines on each side of an axis to show a grid?
sine_scale = 0.15 # separate scale for the 2D plot 0.15 m = 1 unit for 2D plot (separate X and Y units??)
txt_size = (80, 80, 80) # size of axis titles
line_width_wave = 8
line_width_ptguides = 6
color_grid = {'gray': (0.12, 0.12, 0.12, 0.12)}
color_wave = {'white': (1.0, 1.0, 1.0, 1.0)}
color_ball = (0.8, 0.8, 0.8, 0.8)
color_world = (0, 0, 0)

# Background
bpy.data.worlds[0].use_nodes = False
bpy.data.worlds[0].color = color_world

# Rig
c = resources.CircularRig()
c.scale(4)
c.center = np.array((0, 0, 0.5))*grid_scale
c.target = np.array((0, 0, 1))*grid_scale
c.set_theta('camera', np.pi/6)
c.set_theta('key', np.pi/4)
c.set_theta('fill', 0)
c.set_theta('back', np.pi)
c.fov = 80
bpy.data.lights['Key'].energy = 4

# draw axes
axp = Pencil('axes', coll_name='ax', layer_name='main')
smp = np.r_[-grid_lim:grid_lim:0.05]*grid_scale

axp.stroke(trf.PointCloud(np.vstack((smp, 0*smp, 0*smp)).T, trf.CoordFrame()), color='crd_i', layer='main', keyframe=0, line_width=5)
axp.stroke(trf.PointCloud(np.vstack((0*smp, smp, 0*smp)).T, trf.CoordFrame()), color='crd_j', layer='main', keyframe=0, line_width=5)
axp.stroke(trf.PointCloud(np.vstack((0*smp, 0*smp, smp)).T, trf.CoordFrame()), color='crd_k', layer='main', keyframe=0, line_width=5)
axp.color = color_grid
for i in np.r_[-grid_lim:grid_lim+1]*grid_scale:
    axp.stroke(trf.PointCloud(np.vstack((smp, i*np.ones_like(smp), 0*smp)).T, trf.CoordFrame()), color='gray', layer='grid', keyframe=0, line_width=3)
    axp.stroke(trf.PointCloud(np.vstack((i*np.ones_like(smp), smp, 0*smp)).T, trf.CoordFrame()), color='gray', layer='grid', keyframe=0, line_width=3)

# name axes
pal = utils.color_palette('blender_ax')
txt = {}
txt['ax_k'] = new.Text(r'\textit{Amplitude(A)} $\rightarrow$', 'z_label',
                       halign='left', 
                       valign='bottom', 
                       scale=txt_size,
                       color=pal['crd_k'], 
                       coll_name='ax')
txt['ax_k'].frame = txt['ax_k'].frame.transform(np.linalg.inv(trf.m4(i=(0, 0, 1), j=(0, -1, 0), k=(1, 0, 0))))
txt['ax_j'] = new.Text(r'\textit{Frequency(f)} $\rightarrow$', 'y_label',
                       halign='left', 
                       valign='top', 
                       scale=txt_size,
                       color=pal['crd_j'], 
                       coll_name='ax')
txt['ax_j'].frame = txt['ax_j'].frame.transform(np.linalg.inv(trf.m4(i=(0, 1, 0), j=(0, 0, 1), k=(1, 0, 0))))
txt['ax_i'] = new.Text(r'$\leftarrow$\textit{Phase($\phi$)}', 'x_label',
                       halign='right', 
                       valign='top', 
                       scale=txt_size,
                       color=pal['crd_i'], 
                       coll_name='ax')
txt['ax_i'].frame = txt['ax_i'].frame.transform(np.linalg.inv(trf.m4(i=(-1, 0, 0), j=(0, 0, 1), k=(0, 1, 0))))

txt['ax_i']().location = Vector((1*grid_scale, 0, -0.02*grid_scale))
txt['ax_j']().location = Vector((0, 1*grid_scale, -0.02*grid_scale))
txt['ax_k']().location = Vector((0, -0.02*grid_scale, 0.5*grid_scale))
bpy.context.view_layer.update()

txt['ax_k']().matrix_world = Matrix.Rotation(np.pi/3, 4, 'Z')@txt['ax_k']().matrix_world

# make ball
s = new.sphere(r=0.1*grid_scale)
s.shade('smooth')
s.subsurf(2, 3)
b = bpy.data.materials.new('ball_mat')
b.diffuse_color = color_ball
b.metallic = 0.7
s.bm.materials.append(b)

# sine wave
def wave_pts(amp, f, phi, t_end=4):
    """Sine wave as a point cloud."""
    x = np.linspace(0, t_end, 200) # time
    y = amp*np.sin(2*np.pi*f*x + phi)
    z = np.zeros_like(x)
    return trf.PointCloud(np.vstack((x, y, z)).T*sine_scale, trf.CoordFrame())

w = Pencil('wave', coll_name='plot', layer_name='main')
w.color = color_wave

# point the sine wave to the camera
wo_frame = trf.CoordFrame(w.o.matrix_world, unit_vectors=False)
cam_frame = trf.CoordFrame(bpy.data.objects['MainCamera'].matrix_world)
w.o.matrix_world = wo_frame.transform(np.linalg.inv(trf.m4(i=cam_frame.i, j=cam_frame.j, k=cam_frame.k))).m
w.o.location = np.array((2, -2, 1))*grid_scale
bpy.context.view_layer.update()

# title the equation
txt['eqn'] = new.Text(r'$A\sin(2 \pi f t + \phi)$', 'plot_title',
                      halign='left', 
                      valign='bottom', 
                      scale=np.array(txt_size)*1.2,
                      color=color_wave['white'], 
                      coll_name='eqn',
                      combine_curves=False)
for mtrl in bpy.data.objects[txt['eqn'].obj_names[0]].data.materials:
    mtrl.diffuse_color = pal['crd_k']
for mtrl in bpy.data.objects[txt['eqn'].obj_names[7]].data.materials:
    mtrl.diffuse_color = pal['crd_j']
for mtrl in bpy.data.objects[txt['eqn'].obj_names[10]].data.materials:
    mtrl.diffuse_color = pal['crd_i']

txt['eqn'].frame = txt['eqn'].frame.transform(np.linalg.inv(trf.m4(i=cam_frame.i, j=cam_frame.j, k=cam_frame.k)))
txt['eqn']().location = w.o.location + Vector((0.15*grid_scale, -0.15*grid_scale, 0.8*grid_scale))

# animation
def stroke_loc(phi=0, f=0.5, amp=1, key_num=0):
    """Helper function for the animation"""
    w.stroke(wave_pts(phi=phi, f=f, amp=amp), color='white', keyframe=key_num, line_width=line_width_wave)
    s.key(key_num, 'l', [np.array((phi, f, amp))*grid_scale])
    axp.stroke(trf.PointCloud(np.array([[0, f, 0], [0, f, amp]])*grid_scale, trf.CoordFrame()), color='crd_k', keyframe=key_num, layer='mark', line_width=line_width_ptguides)
    axp.stroke(trf.PointCloud(np.array([[0, f, amp], [phi, f, amp]])*grid_scale, trf.CoordFrame()), color='crd_i', keyframe=key_num, layer='mark', line_width=line_width_ptguides)
    axp.stroke(trf.PointCloud(np.array([[0, 0, amp], [0, f, amp]])*grid_scale, trf.CoordFrame()), color='crd_j', keyframe=key_num, layer='mark', line_width=line_width_ptguides)
    if key_num == 0:
        print((phi, f, amp, key_num))

key = 1
env.Key().start = key
bpy.context.view_layer.update()
for tf in np.linspace(0, 2, 50):
    stroke_loc(phi=0, f=tf, amp=1, key_num=key)
    key += 1
key += 10
for tf in np.linspace(2, 0, 50):
    stroke_loc(phi=0, f=tf, amp=1, key_num=key)
    key += 1

w.keyframe = key
key += 20
s.key(key-1, 'l')

for ta in np.linspace(0, 2, 50):
    stroke_loc(phi=0, f=0.5, amp=ta, key_num=key)
    key += 1
key += 10
for ta in np.linspace(2, 0, 50):
    stroke_loc(phi=0, f=0.5, amp=ta, key_num=key)
    key += 1

w.keyframe = key
key += 20
s.key(key-1, 'l')

for tp in np.linspace(0, np.pi, 50):
    stroke_loc(phi=tp, f=0.5, amp=1, key_num=key)
    key += 1
key += 10
for tp in np.linspace(np.pi, 0, 50):
    stroke_loc(phi=tp, f=0.5, amp=1, key_num=key)
    key += 1

env.Key().end = key
