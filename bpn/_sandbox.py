# context.area: VIEW_3D
"""
This is a sandbox. Develop code here!
"""
#-----------------
from bpn_init import * # pylint: disable=wildcard-import, unused-wildcard-import
pn.reload()
env.reset()
#-----------------

grid_scale = 1 # 0.4 => 0.4 m in the world is 1 unit in coordinate frame
grid_lim = 8 # how many lines on each side of an axis to show a grid?
sine_scale = 0.375 # separate scale for the 2D plot 0.15 m = 1 unit for 2D plot (separate X and Y units??)
txt_size = (80, 80, 80) # size of axis titles
line_width_wave = 8
line_width_ptguides = 6
color_grid = {'gray': (0.12, 0.12, 0.12, 0.12)}
color_wave = {'white': (1.0, 1.0, 1.0, 1.0)}
color_ghost = {'ghost': (0.12, 0.12, 0.12, 0.12)}
color_ptvector = {'ptvector': (0.6, 0.6, 0.6, 0.6)}
color_ball = (0.8, 0.8, 0.8, 0.8)
color_world = (0, 0, 0)
out = 'vid'
text_eqn = r'$A\sin(2 \pi f t + \phi)$'
text_xlabel = r'$\leftarrow$\textit{Phase($\phi$)}'
text_ylabel = r'\textit{Frequency(f)} $\rightarrow$'
text_zlabel = r'\textit{Amplitude(A)} $\rightarrow$'
# text_eqn = r'\textit{Walking}'
# text_xlabel = r'$\leftarrow$\textit{?}'
# text_ylabel = r'\textit{?} $\rightarrow$'
# text_zlabel = r'\textit{?} $\rightarrow$'

def rig():
    """Set up camera and lights."""
    cr = new.CircularRig()
    cr.center = np.array((0, 0, 0.5))*grid_scale
    cr.target = np.array((0, 0, 1))*grid_scale
    cr.camera.theta = np.pi/6
    cr.key_light.theta = np.pi/4
    cr.fill_light.theta = 0
    cr.back_light.theta = np.pi
    cr.fov = 80
    cr.key_light().data.energy = 4
    bpy.context.scene.camera = cr.camera()
    return cr

def draw_axes():
    """Draw the grid and axes."""
    gpax = new.pencil('axes', coll_name='ax', layer_name='main')
    gpax.color = color_ptvector
    smp = np.r_[-grid_lim:grid_lim:0.05]*grid_scale

    gpax.stroke(trf.PointCloud(np.vstack((smp, 0*smp, 0*smp)).T, trf.CoordFrame()), color='crd_i', layer='main', keyframe=0, line_width=5)
    gpax.stroke(trf.PointCloud(np.vstack((0*smp, smp, 0*smp)).T, trf.CoordFrame()), color='crd_j', layer='main', keyframe=0, line_width=5)
    gpax.stroke(trf.PointCloud(np.vstack((0*smp, 0*smp, smp)).T, trf.CoordFrame()), color='crd_k', layer='main', keyframe=0, line_width=5)
    gpax.color = color_grid
    for i in np.r_[-grid_lim:grid_lim+1]*grid_scale:
        gpax.stroke(trf.PointCloud(np.vstack((smp, i*np.ones_like(smp), 0*smp)).T, trf.CoordFrame()), color='gray', layer='grid', keyframe=0, line_width=3)
        gpax.stroke(trf.PointCloud(np.vstack((i*np.ones_like(smp), smp, 0*smp)).T, trf.CoordFrame()), color='gray', layer='grid', keyframe=0, line_width=3)
    return gpax

def label_axes():
    """label the axes."""
    h_txt = {}
    h_txt['ax_k'] = new.Text(text_zlabel, 'z_label',
                             halign='left', 
                             valign='bottom', 
                             scale=txt_size,
                             color=pal['crd_k'], 
                             coll_name='ax')
    h_txt['ax_k'].frame = h_txt['ax_k'].frame.transform(trf.m4(i=(0, 0, 1), j=(0, -1, 0), k=(1, 0, 0)))
    h_txt['ax_j'] = new.Text(text_ylabel, 'y_label',
                             halign='left', 
                             valign='top', 
                             scale=txt_size,
                             color=pal['crd_j'], 
                             coll_name='ax')
    h_txt['ax_j'].frame = h_txt['ax_j'].frame.transform(trf.m4(i=(0, 1, 0), j=(0, 0, 1), k=(1, 0, 0)))
    h_txt['ax_i'] = new.Text(text_xlabel, 'x_label',
                             halign='right', 
                             valign='top', 
                             scale=txt_size,
                             color=pal['crd_i'], 
                             coll_name='ax')
    h_txt['ax_i'].frame = h_txt['ax_i'].frame.transform(trf.m4(i=(-1, 0, 0), j=(0, 0, 1), k=(0, 1, 0)))

    h_txt['ax_i']().location = Vector((1*grid_scale, 0, -0.02*grid_scale))
    h_txt['ax_j']().location = Vector((0, 1*grid_scale, -0.02*grid_scale))
    h_txt['ax_k']().location = Vector((0, -0.02*grid_scale, 0.5*grid_scale))
    bpy.context.view_layer.update()

    # h_txt['ax_k']().matrix_world = Matrix.Rotation(np.pi/3, 4, 'Z')@h_txt['ax_k']().matrix_world
    return h_txt


def make_sphere():
    """Sphere to represent points in 3D space."""
    sph = new.sphere('sphere', r=0.07*grid_scale, coll_name='spheres')
    sph.shade('smooth')  #pylint:disable=no-member
    sph.subsurf(2, 3)
    b = bpy.data.materials.new('ball_mat')
    b.diffuse_color = color_ball
    b.metallic = 0.7
    sph().data.materials.append(b)
    sph.show(1)
    return sph

# sine wave
def wave_pts(amp, f, phi, t_end=4):
    """Sine wave as a point cloud."""
    if isinstance(amp, (int, float)):
        amp = [amp]
    if isinstance(f, (int, float)):
        f = [f]
    if isinstance(phi, (int, float)):
        phi = [phi]
    x = np.linspace(0, t_end, 200) # time
    y = np.zeros_like(x)
    z = np.zeros_like(x)
    for ta, tf, tp in zip(amp, f, phi):
        y += ta*np.sin(2*np.pi*tf*x + tp)
    y = y/len(np.array(amp))
    return trf.PointCloud(np.vstack((x, y, z)).T*sine_scale, trf.CoordFrame())

def draw_wave():
    """Set up greasepencil for drawing sine wave strokes."""
    wav = new.pencil('wave', coll_name='plot', layer_name='main')
    wav.color = color_ghost
    wav.color = color_wave

    # point the sine wave to the camera
    wo_frame = trf.CoordFrame(wav().matrix_world, unit_vectors=False)
    cam_frame = trf.CoordFrame(c.camera().matrix_world)
    wav().matrix_world = wo_frame.transform(np.linalg.inv(trf.m4(i=cam_frame.i, j=cam_frame.j, k=cam_frame.k))).m
    wav().location = np.array((2, -2, 1))*grid_scale
    bpy.context.view_layer.update()
    return wav

def sin_eqn():
    """Equation for sine wave."""
    print(color_wave)
    txt_eqn = new.Text(
        text_eqn, 'plot_title',
        halign='left', 
        valign='bottom', 
        scale=np.array(txt_size)*1.2,
        color=color_wave['white'], 
        coll_name='eqn',
        combine_curves=False)
    # for mtrl in bpy.data.objects[txt_eqn.obj_names[5]].data.materials:
    #     mtrl.diffuse_color = pal['crd_k']
    # for mtrl in bpy.data.objects[txt_eqn.obj_names[13]].data.materials:
    #     mtrl.diffuse_color = pal['crd_j']
    # for mtrl in bpy.data.objects[txt_eqn.obj_names[17]].data.materials:
    #     mtrl.diffuse_color = pal['crd_i']
    # for mtrl in bpy.data.objects[txt_eqn.obj_names[10]].data.materials:
    #     mtrl.diffuse_color = pal['crd_k']
    # for mtrl in bpy.data.objects[txt_eqn.obj_names[12]].data.materials:
    #     mtrl.diffuse_color = pal['crd_j']
    # for mtrl in bpy.data.objects[txt_eqn.obj_names[14]].data.materials:
    #     mtrl.diffuse_color = pal['crd_i']

    cam_frame = trf.CoordFrame(c.camera().matrix_world)
    txt_eqn.frame = txt_eqn.frame.transform(trf.m4(i=cam_frame.i, j=cam_frame.j, k=cam_frame.k))
    txt_eqn().location = w().location + Vector((0.4*grid_scale, -0.4*grid_scale, 0.8*grid_scale))
    return txt_eqn

# animation
def stroke_loc(sph, phi=0, f=0.5, amp=1, key_num=0, guide_type='axes', ghost=False):
    """Helper function for the animation"""
    
    sph = sph if isinstance(sph, list) else [sph]
    phi = phi if isinstance(phi, list) else [phi]
    f = f if isinstance(f, list) else [f]
    amp = amp if isinstance(amp, list) else [amp]
    assert guide_type in ('axes', 'vector', None)

    # compound wave
    w.stroke(wave_pts(phi=phi, f=f, amp=amp), color='white', keyframe=key_num, line_width=line_width_wave)
    
    for ts, tp, tf, ta in zip(sph, phi, f, amp):
        # ghost individual waves
        if ghost: 
            w.stroke(wave_pts(phi=tp, f=tf, amp=ta), color='ghost', keyframe=key_num, line_width=line_width_wave*0.7)

        # sphere location
        ts.key(key_num, 'l', [np.array((tp, tf, ta))*grid_scale])

        # sphere guides
        if guide_type is not None:
            if guide_type == 'axes':
                axg.stroke(trf.PointCloud(np.array([[0, tf, 0], [0, tf, ta]])*grid_scale, trf.CoordFrame()), color='crd_k', keyframe=key_num, layer=guide_type, line_width=line_width_ptguides)
                axg.stroke(trf.PointCloud(np.array([[0, tf, ta], [tp, tf, ta]])*grid_scale, trf.CoordFrame()), color='crd_i', keyframe=key_num, layer=guide_type, line_width=line_width_ptguides)
                axg.stroke(trf.PointCloud(np.array([[0, 0, ta], [0, tf, ta]])*grid_scale, trf.CoordFrame()), color='crd_j', keyframe=key_num, layer=guide_type, line_width=line_width_ptguides)
            if guide_type == 'vector':
                axg.stroke(trf.PointCloud(np.array([[0, 0, 0], [tp, tf, ta]])*grid_scale, trf.CoordFrame()), color='ptvector', keyframe=key_num, layer=guide_type, line_width=line_width_ptguides/2)


def sweep_freq(tkey):
    """Animation. Frequency sweep."""
    for tf in np.linspace(1, 2, 40):
        stroke_loc(s_all[0], phi=0, f=tf, amp=1, key_num=tkey)
        tkey += 1
    tkey += 10
    for tf in np.linspace(2, 0, 60):
        stroke_loc(s_all[0], phi=0, f=tf, amp=1, key_num=tkey)
        tkey += 1
    tkey += 10
    for tf in np.linspace(0, 1, 30):
        stroke_loc(s_all[0], phi=0, f=tf, amp=1, key_num=tkey)
        tkey += 1
    return tkey

def blanks(tkey, n_blanks=20):
    """Insert blanks for sphere and freeze wave."""
    w.keyframe = tkey+1
    axg.keyframe = tkey+1
    for ts in s_all:
        ts.hide(tkey)
    tkey += n_blanks
    for ts in s_all:
        ts.show(tkey)
        ts.key(tkey-1, 'l')
    w.keyframe = tkey-1
    axg.keyframe = tkey-1
    return tkey

def sweep_amp(tkey):
    """Animation. Amplitude sweep."""
    for ta in np.linspace(1, 2, 40):
        stroke_loc(s_all[0], phi=0, f=0.5, amp=ta, key_num=tkey)
        tkey += 1
    tkey += 10
    for ta in np.linspace(2, 0, 60):
        stroke_loc(s_all[0], phi=0, f=0.5, amp=ta, key_num=tkey)
        tkey += 1
    tkey += 10
    for ta in np.linspace(0, 1, 30):
        stroke_loc(s_all[0], phi=0, f=0.5, amp=ta, key_num=tkey)
        tkey += 1
    return tkey

def sweep_phi(tkey):
    """Animation. Phase sweep."""
    for tp in np.linspace(0, np.pi, 50):
        stroke_loc(s_all[0], phi=tp, f=0.5, amp=1, key_num=tkey)
        tkey += 1
    tkey += 10
    for tp in np.linspace(np.pi, 0, 50):
        stroke_loc(s_all[0], phi=tp, f=0.5, amp=1, key_num=tkey)
        tkey += 1
    return tkey

def copy_spheres(tot_spheres):
    """Make copies of the sphere, but remove animation data."""
    n_present = len(s_all)
    n_copies = tot_spheres - n_present # number of copies to make
    for _ in range(n_copies):
        s_all.append(s_all[0].copy())
    for ts in s_all[n_present:]:
        ts.bo.animation_data_clear() # retains a reference to the old animation data
        ts.hide(1) # hide all the copies until it is time to show
    assert len(s_all) == tot_spheres
    bpy.context.view_layer.update()

def rand_sweep(tkey):
    """Animation. Points in random places constructing a signal."""
    n_pts_max = 7
    copy_spheres(n_pts_max)
    rnd = lambda n: list(np.random.random(n)*2) # pylint: disable=no-member
    for n_pts in range(2, n_pts_max+1):
        for _ in range(4):
            stroke_loc(s_all[0:n_pts], phi=rnd(n_pts), f=rnd(n_pts), amp=rnd(n_pts), key_num=tkey, guide_type='axes', ghost=True)
            for ts in s_all[0:n_pts]:
                ts.show(tkey)
            for ts in s_all[n_pts:]:
                ts.hide(tkey)
            tkey += 1
    return tkey

def add_waves(tkey):
    """Animation. Add points from random locations progressively."""
    n_pts_max = 10
    copy_spheres(n_pts_max)
    rnd = lambda n: list(np.random.random(n)*2) # pylint: disable=no-member
    for n_pts in range(1, n_pts_max+1):
        for _ in range(10):
            stroke_loc(s_all[0:n_pts], phi=rnd(n_pts), f=rnd(n_pts), amp=rnd(n_pts), key_num=tkey, guide_type='axes', ghost=True)
            for ts in s_all[0:n_pts]:
                ts.show(tkey)
            for ts in s_all[n_pts:]:
                ts.hide(tkey)
            tkey += 1
    return tkey

def make_animation(func_list, save=None, name=None):
    """Save video after making the animation."""
    if type(func_list).__name__ == 'function':
        func_list = [func_list]
    if name is None:
        name = ''
        for f in func_list:
            name += f.__name__+'_'
        name = name[:-1]
    if save is None:
        save = []
    key = 1
    env.Key().start = key
    bpy.context.view_layer.update()
    for f in func_list:
        key = f(key)
    env.Key().end = key
    if 'vid' in save:
        io.render(name+' ', 'vid')
        env.Key().goto(1)
        io.render(name+'_title', 'img')
    if 'img' in save:
        for frm in range(env.Key().end):
            env.Key().goto(frm)
            io.render(name+'_{:04d}'.format(frm), 'img')

def clear_animation():
    """Clear animation data."""
    env.clear('actions')
    for g in (axg().data, w().data):
        for l in g.layers:
            l.clear()


env.background(color_world)
c = rig()
draw_axes()
axg = new.pencil('guides', coll_name='ax', layer_name='main')
pal = utils.color_palette('blender_ax')
txt = label_axes()
s_all = [make_sphere()]
w = draw_wave()
txt['eqn'] = sin_eqn()

make_animation(sweep_freq)
# make_animation(sweep_freq, save='vid')
# clear_animation()
# make_animation(sweep_amp, save='vid')
# clear_animation()
# make_animation(sweep_phi, save='vid')
# clear_animation()
# make_animation(rand_sweep)

# make_animation([sweep_freq, blanks, sweep_amp, blanks, sweep_phi, blanks, rand_sweep])

# n_frames = 60
# fov = np.linspace(110, 30, n_frames)
# targ_start = np.array([-0.22117764,  0.06976014,  1.2347604])
# targ_end = np.array([-0.22117764,  0.64740258,  1.29340947])
# targ = np.linspace(targ_start, targ_end, n_frames)

# fcount = 1
# for ttarg, tfov in zip(targ, fov):
#     c.target = ttarg
#     c.fov = tfov
#     s.render('Skeleton.{:04d}'.format(fcount), 'img')
#     fcount += 1
