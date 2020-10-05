from bpn_init import *
# from importlib import reload
# reload(env)
# reload(io)
env.reset()

# sphere size pulsation parameters
sine_period = 11 # s
r_min = 0.2
r_max = 1

# animation parameters
env.Key().fps = 30
env.Key().start = 1 #frame
env.Key().time = sine_period # s

time_vec = np.r_[env.Key().start-1:env.Key().end]/env.Key().fps
sine_vec = np.sin(2*np.pi*time_vec/sine_period - np.pi/2)
print(sine_vec[[0, -1]])
pulse_vec = ( (sine_vec+1)/2 )*(r_max - r_min) + r_min

s = new.sphere("Pulsar", r=1)
s_vert = s.v
s_vert[:, 1] = s_vert[:, 1]/6 # squish along the Y axis
s.v = s_vert
s.subsurf(2, 3)
s.shade('smooth')

m = bpy.data.materials.new("ball_emitter")
m.use_nodes = True
# remove all nodes and links
for node in m.node_tree.nodes:
    if node is not None:
        m.node_tree.nodes.remove(node)
for link in m.node_tree.links:
    if link is not None:
        m.node_tree.links.remove(link)
# Create new nodes and links, and append the material
# https://stackoverflow.com/questions/36185377/how-i-can-create-a-material-select-it-create-new-nodes-with-this-material-and
# https://docs.blender.org/api/blender_python_api_current/bpy.types.ShaderNode.html
m_em = m.node_tree.nodes.new('ShaderNodeEmission')
m_em.inputs['Color'].default_value[:] = (0.58, 0.76, 0.74, 1.0)
m_em.inputs['Strength'].default_value = 0.1
m_out = m.node_tree.nodes.new('ShaderNodeOutputMaterial')
m.node_tree.links.new(m_em.outputs['Emission'], m_out.inputs['Surface'])

s().data.materials.append(m)

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
                             color=pal['MATLAB_00'], 
                             coll_name='ax')
h_inhale.frame = trf.Quat([1, 0, 0], np.pi/2)*h_inhale.frame
h_inhale.translate([0, -0.4, 0])
h_inhale.show(1)
h_inhale.hide(np.floor(0.5*sine_period*env.Key().fps))

h_exhale = new.Text('Exhale', 'txt_exhale',
                             halign='center', 
                             valign='middle', 
                             scale=(300, 300, 300),
                             color=pal['MATLAB_01'], 
                             coll_name='ax')
h_exhale.frame = trf.Quat([1, 0, 0], np.pi/2)*h_exhale.frame
h_exhale.translate([0, -0.4, 0])
h_exhale.hide(1)
h_exhale.show(np.floor(0.5*sine_period*env.Key().fps)+1)


color_world = (0, 0, 0)
bpy.data.worlds['World'].use_nodes = False
bpy.data.worlds['World'].color = color_world
bpy.context.scene.camera = cr.camera()
bpy.context.scene.render.engine = 'CYCLES'
# io.render('breathing_test_02')

# Double spheres? Have an emission sphere in front of a reflective sphere
# manipulate positions of the material nodes so that they don't overlap when the shader editor is opened
