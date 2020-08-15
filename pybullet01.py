import pybullet as p
import time
import pybullet_data

class globals:
    pass

# load URDF file in python and pybullet, store initial conditions
def init_sim():
    if not p.isConnected():
        globals.physicsClient = p.connect(p.GUI) #or p.DIRECT for non-graphical version
        p.setAdditionalSearchPath(pybullet_data.getDataPath()) #optionally
    else:
        p.resetSimulation(globals.physicsClient)

    p.setGravity(0, 0, -10)
    planeId = p.loadURDF("plane.urdf")
    cubeStartOrientation = p.getQuaternionFromEuler([0, 0, 0])
    globals.sph1 = p.loadURDF("robots/capsule01.urdf", [0, 0, 3], cubeStartOrientation)
    globals.sph2 = p.loadURDF("robots/sphere01_man.urdf", [0, 0, 5], cubeStartOrientation)
    globals.t_step = p.getPhysicsEngineParameters()['fixedTimeStep']
    globals.curr_step = 0
    p.setJointMotorControl2(globals.sph1, 0, controlMode=p.VELOCITY_CONTROL, force=0)

def distance(obj1, obj2):
    """Calculate the scalar Euclidean distance between two objects."""
    pos1 = p.getBasePositionAndOrientation(obj1)[0]
    pos2 = p.getBasePositionAndOrientation(obj2)[0]
    return np.sqrt(np.sum(np.subtract(pos1, pos2)**2))

def up_force(obj, mag):
    """Upward force on obj of a given magnitude mag."""
    p.applyExternalForce(objectUniqueId=obj, linkIndex=-1, forceObj=[0, 0, mag], posObj=[0, 0, 0], flags=p.LINK_FRAME)

def sim(n_steps, animate=True):
    for i in range(n_steps):
        up_force(globals.sph2, 9)
        p.stepSimulation()
        if animate:
            time.sleep(globals.t_step)

    globals.curr_step += n_steps

if __name__ == "__main__":
    init_sim()
    sim(500)
    time.sleep(15)
    p.disconnect(globals.physicsCilent)

