import urdfpy as u
import numpy as np
# r_def = u.URDF.load(r'C:\Users\Praneeth\.conda\envs\blender2830\Lib\site-packages\pybullet_data\biped\biped2d_pybullet.urdf')

pose = np.eye(4) # matrix_world
inertia_tensor = np.eye(3)
geometry = u.Geometry(sphere=u.Sphere(0.25))
inertia = u.Inertial(1, inertia_tensor, pose) # mass, inertia, frame rel. 'link frame'
visuals = [u.Visual(geometry)]
collisions = [u.Collision("coll", pose, geometry)]
links = [u.Link("body", inertia, visuals, collisions)]
r = u.URDF("myRobot", links)
r.save("myRobot.urdf")
