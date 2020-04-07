# context.area: VIEW_3D
"""
This is a sandbox. Develop code here!
"""
#-----------------
from bpn_init import * # pylint: disable=wildcard-import, unused-wildcard-import
pn.reload()
env.reset()
#-----------------

bpy.data.worlds[0].use_nodes = False
bpy.data.worlds[0].color = (0, 0, 0)
grid_scale = 0.1 # 0.1 => 0.1 m in the world is 1 unit in coordinate frame
c = CircularRig()
c.center = np.array((15, 3, 3))*grid_scale
c.target = np.array((0, 2, 4))*grid_scale
c.theta = np.pi/4
c.fov = 80

def wave_pts(amp, f, phi, t_end=4):
    """Sine wave as a point cloud."""
    y = np.linspace(0, t_end, 200) # time
    z = amp*np.sin(2*np.pi*f*y + phi)
    x = np.zeros_like(z)
    return trf.PointCloud(np.vstack((x, y, z)).T*grid_scale, trf.CoordFrame())

axp = Pencil('axes', coll_name='plot', layer_name='main')
smp = np.r_[-10:10:0.05]

axp.stroke(trf.PointCloud(np.vstack((smp, 0*smp, 0*smp)).T, trf.CoordFrame()), color='crd_i', layer='main', keyframe=0, line_width=5)
axp.stroke(trf.PointCloud(np.vstack((0*smp, smp, 0*smp)).T, trf.CoordFrame()), color='crd_j', layer='main', keyframe=0, line_width=5)
axp.stroke(trf.PointCloud(np.vstack((0*smp, 0*smp, smp)).T, trf.CoordFrame()), color='crd_k', layer='main', keyframe=0, line_width=5)


pal = utils.color_palette('blender_ax')
txt = {}
txt['ax_k'] = new.Text(r'\textit{Amplitude}', halign='left', valign='bottom', color=pal['crd_k'])
txt['ax_k'].frame = txt['ax_k'].frame.transform(np.linalg.inv(trf.m4(i=(0, 0, 1), j=(0, -1, 0), k=(1, 0, 0))))
txt['ax_i'] = new.Text(r'\textit{Phase}', halign='right', valign='top', color=pal['crd_i'])
txt['ax_i'].frame = txt['ax_i'].frame.transform(np.linalg.inv(trf.m4(i=(-1, 0, 0), j=(0, 0, 1), k=(0, 1, 0))))
txt['ax_j'] = new.Text(r'\textit{Frequency}', halign='left', valign='top', color=pal['crd_j'])
txt['ax_j'].frame = txt['ax_j'].frame.transform(np.linalg.inv(trf.m4(i=(0, 1, 0), j=(0, 0, 1), k=(1, 0, 0))))

s = new.sphere(r=0.35*grid_scale)
s.shade('smooth')
s.subsurf(2, 3)
b = bpy.data.materials.new('ball_mat')
b.diffuse_color = (0.8, 0.8, 0.8, 0.8)
b.metallic = 0.7
s.bm.materials.append(b)

ball_scale = grid_scale*4

w = Pencil('wave', coll_name='plot', layer_name='main')
w.color = {'white': (1.0, 1.0, 1.0, 1.0)}
w_width = 4
w.o.location = np.array((6, -6, 4))*grid_scale
w.o.rotation_euler = np.array((0, 0, c.theta))

def stroke_loc(phi=0, f=0.5, amp=1, key_num=0):
    w.stroke(wave_pts(phi=phi, f=f, amp=amp), color='white', keyframe=key_num, line_width=w_width)
    s.key(key_num, 'l', [np.array((phi, f, amp))*ball_scale])
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

for tp in np.linspace(0, 2*np.pi, 50):
    stroke_loc(phi=tp, f=0.5, amp=1, key_num=key)
    key += 1
key += 10
for tp in np.linspace(2*np.pi, 0, 50):
    stroke_loc(phi=tp, f=0.5, amp=1, key_num=key)
    key += 1

env.Key().end = key
