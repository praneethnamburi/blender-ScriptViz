from bpn import new, trf
from bpn.utils import get

def demo():
    """camera, object = demo()"""
    # create object of interest
    s = new.cone('object')
    s.scale(0.12)
    s.rotate((40, 0, 0))
    s.apply_matrix()

    # move object to a new position
    s.frame = trf.CoordFrame(origin=(0., 3., 0.))

    # create a proxy object for the camera
    c = new.cube('camera')

    # record original object frame position with respect to the camera
    s_orig_frame = s.frame

    # fix the object with respect to the camera by transforming it with the camera's transformation matrix in the world
    s.frame = trf.CoordFrame(c.frame.m@s_orig_frame.m)
    # every time you move the camera object, just run the above line of code to get the object in the camera's reference frame
    return c, s

class Dancer:
    def __init__(self):
        # create dancer
        body = new.cone(name='body',r1=0.2, r2=0.2, h=1.5)
        body.translate(z=0.75)
        body.scale((0.5, 1, 1))
        body.apply_matrix()

        head = new.cone(name='head', r1=0.2, r2=0, h=0.3)
        head.rotate((0.,90.,0.))
        head.translate(x=0.1)
        head.apply_matrix()
        head.translate(z=1.6)
        
        self.gp = []
        self.gp.append(body.show_frame())
        self.gp.append(head.show_frame())
        
        # create markers
        m1 = new.sphere(name='m1', r=0.05)
        self.m1_pos = trf.PointCloud((-0.1, 0, 1)) # both body frame and world frame
        
        self.body = body
        self.head = head
        self.m1 = m1

        self.screen = new.plane('screen')
        self.m1viz = new.sphere(name='m1viz', r=0.08)
        self._update_m1()
    
    def translate(self, delta=(0., 0., 0.)):
        self.body.translate(delta)
        self.head.translate(delta)
        self._update_m1()
        self.body.show_frame()
        self.head.show_frame()

    def turn(self, angle_deg):
        self.body.rotate((0., 0., angle_deg))
        self.head.rotate((0., 0., angle_deg))
        self._update_m1()
        self.body.show_frame()
        self.head.show_frame()

    def turn_head(self, angle_deg):
        self.head.rotate((0., 0., angle_deg))
        self.head.show_frame()
    
    def _update_m1(self):
        self.m1.loc = self.m1_pos.transform(self.body.frame.m).co[0]

    def __neg__(self):
        -self.body
        -self.head
        -self.m1
        for g in self.gp:
            -g
