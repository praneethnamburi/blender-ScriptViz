# context.area: VIEW_3D
"""
This is a sandbox. Develop code here!
"""
#-----------------
from bpn_init import * # pylint: disable=wildcard-import, unused-wildcard-import
pn.reload()
env.reset()
#-----------------

"""
s.rigid_body.collision_shape in ('BOX', 'SPHERE', 'CAPSULE', 'CYLINDER', 'CONE', 'CONVEX_HULL', 'MESH')
s.rigid_body.mass, 
type in ('ACTIVE', 'PASSIVE')
friction, restitution
linear_damping, angular_damping
enabled -> Dynamic (controlled by the physics engine)
kinematic -> Animated (controlled by the animation system)
collision_shape -> ('BOX', 'SPHERE', 'CAPSULE', 'CYLINDER', 'CONE', 'CONVEX_HULL', 'MESH')
mesh_source -> ('BASE', 'DEFORM', 'FINAL')
"""

if bpy.context.scene.rigidbody_world is None:
    bpy.ops.rigidbody.world_add()
rb = bpy.data.collections.new('RigidBodies')
bpy.context.scene.rigidbody_world.collection = rb

env_kf = env.Key()
env_kf.goto(1)

def make_ground(name='pl'):
    ground = new.plane(name, r=4*np.sqrt(2))
    ground.in_coll(rb.name)
    ground().rigid_body.friction = 0
    ground().rigid_body.type = 'PASSIVE'
    ground().rigid_body.restitution = 1
    return ground

g1 = make_ground('pl1')
# g1.translate((-4, 0, 0))
# g1.frame = trf.Quat([0, 1, 0], 10*np.pi/180, trf.CoordFrame(origin=(0, 0, 0)))*g1.frame

# g2 = make_ground('pl2')
# g2.translate((4, 0, 0))
# g2.frame = trf.Quat([0, -1, 0], 10*np.pi/180, trf.CoordFrame(origin=(0, 0, 0)))*g2.frame
# g2.hide()

# s_bound = new.sphere('bound', r=12, u=64, v=32)
# s_bound.in_coll(rb.name)
# s_bound().rigid_body.friction = 0
# s_bound().rigid_body.type = 'PASSIVE'
# s_bound().rigid_body.collision_shape = 'MESH'
# s_bound().rigid_body.restitution = 1
# s_bound().rigid_body.friction = 0.5
# s_bound().rigid_body.mass = 1000
# s_bound.hide()

def make_sphere(name='sph_rb'):
    s = new.sphere(name, r=1)
    s.in_coll(rb.name)
    s().rigid_body.friction = 0
    s().rigid_body.restitution = 1
    return s

s = make_sphere('sph1')
s.loc = (0, 0, 10)

# m = new.monkey('suzy')
# m.in_coll(rb.name)
# m.loc = (2, 0, 8)
# m().rigid_body.mass = 100
# m().rigid_body.restitution = 1
# for _ in range(25):
#     ts = make_sphere()
#     ts.loc = np.random.random(3)*5

# loc_frm = {env_kf(): s.loc}
# for _ in range(100):
#     +env_kf
#     loc_frm[env_kf()] = s.loc

# print(np.vstack(loc_frm.values()))
