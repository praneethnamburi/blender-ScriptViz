import numpy as np
from bpn import new, trf
from bpn.utils import get
from numpy.linalg.linalg import inv

def demo():
    """camera, object = demo()"""
    d = Dancer()
    d.translate((2, 1, 0))
    d.turn(30)
    d.turn_head(45)
    return d

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
        self.screen = new.empty()
        self.screen.frame = self.head.frame
        self.screen.translate((1, 0, -0.3))

        self.m1viz = new.sphere(name='m1viz', r=0.08)
        self._update_m1()
    
    def translate(self, delta=(0., 0., 0.)):
        self.body.translate(delta)
        self.head.translate(delta)
        self.screen.translate(delta)
        self._update_m1()
        self.body.show_frame()
        self.head.show_frame()
        self.screen.show_frame()

    def turn(self, angle_deg):
        self.body.rotate((0., 0., angle_deg))
        self.screen.frame = self.screen.frame.transform(trf.m4(trf.twisttf(angle_deg*np.pi/180)), tf_frame=self.head.frame)
        self.head.rotate((0., 0., angle_deg))
        self._update_m1()
        self.body.show_frame()
        self.head.show_frame()
        self.screen.show_frame()

    def turn_head(self, angle_deg):
        self.head.rotate((0., 0., angle_deg))
        self.screen.frame = self.screen.frame.transform(trf.m4(trf.twisttf(angle_deg*np.pi/180)), tf_frame=self.head.frame) 
        self.head.show_frame()
        self.screen.show_frame()
        self._update_m1()
    
    def _update_m1(self):
        self.m1.loc = self.m1_pos.transform(self.body.frame.m).co[0]
        self.m1viz.loc = (self.screen.frame.m@inv(self.body.frame.m)@np.hstack((self.m1.loc, 1)))[:-1]
        # self.m1viz.loc = trf.PointCloud(trf.PointCloud(self.m1.loc).in_frame(self.body.frame.m).co[0], self.screen.frame).in_world().co[0]

    def __neg__(self):
        -self.body
        -self.head
        -self.m1
        for g in self.gp:
            -g
