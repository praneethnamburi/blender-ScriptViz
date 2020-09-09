from bpn_init import *
# from importlib import reload
# reload(env)
# reload(io)
env.reset()

env.Key().fps = 30
env.Key().start = 1 #frame
env.Key().time = 22 # s

# sphere size pulsation parameters
sine_period = 11 # s
r_min = 0.2
r_max = 1

time_vec = np.r_[env.Key().start:env.Key().end+1]/env.Key().fps
sine_vec = np.sin(2*np.pi*time_vec/sine_period)
pulse_vec = ( (sine_vec+1)/2 )*(r_max - r_min) + r_min

s = new.sphere("Pulsar", r=1)
s_vert = s.v
s_vert[:, 1] = s_vert[:, 1]/6 # squish along the Y axis
s.v = s_vert
s.subsurf(2, 3)
s.shade('smooth')

for this_frame, pulse_val in enumerate(pulse_vec):
    s.scl = [pulse_val, 1, pulse_val]
    s.key(this_frame+1)

cr = new.CircularRig()
cr.scale(1.2)
cr.key_light.center = [0, 0, 2]
cr.key_light.theta = cr.camera.theta - np.pi/6
cr.fill_light.center = [0, 0, 1]
cr.back_light.center = [0, 0, 4]
cr.fov = 100

# add text - inhale and exhale
pal = utils.color_palette('MATLAB', alpha=1)
h_inhale = new.Text('Inhale', 'txt_inhale',
                             halign='center', 
                             valign='middle', 
                             scale=(300, 300, 300),
                             color=pal['MATLAB_04'], 
                             coll_name='ax')
h_inhale.frame = trf.Quat([1, 0, 0], np.pi/2)*h_inhale.frame
h_inhale.translate([0, -0.4, 0])

color_world = (0, 0, 0)
bpy.data.worlds['World'].use_nodes = False
bpy.data.worlds['World'].color = color_world
bpy.context.scene.camera = cr.camera()
bpy.context.scene.render.engine = 'CYCLES'
# io.render('breathing_test_02')

# add material for the sphere
# animate inhale
# add exhale
