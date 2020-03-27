# context.area: VIEW_3D
"""
This is a sandbox. Develop code here!
"""
#-----------------
import bpn
from bpn import * # pylint: disable=wildcard-import, unused-wildcard-import
bpn._reload() # pylint: disable=protected-access

bpn.env.reset()
#-----------------

class Tube(bpn.Msh):
    """
    Creates a 'Tube' object from a 3d plot.
    """
    def __init__(self, name=None, x=0, y=0, z=0, **kwargs):
        names, kwargs = bpn.utils.clean_names(name, kwargs, {'msh_name':'tube_msh', 'obj_name':'tube_obj', 'priority_obj':'new', 'priority_msh':'new'})
        kwargs_ngon, kwargs = pn.clean_kwargs(kwargs, {'n':6, 'r':0.3, 'theta_offset_deg':-1}, {'n':['segments', 'seg', 'u', 'n'], 'r':['radius', 'r'], 'theta_offset_deg':['theta_offset_deg', 'th', 'offset', 'th_off_deg']})
        kwargs_this, kwargs_bpnmsh = pn.clean_kwargs(kwargs, {'shade':'smooth', 'subsurf':True, 'subsurf_levels':2, 'subsurf_render_levels':2})
        
        spine = np.array([np.array((tx, ty, tz)) for tx, ty, tz in zip(x, y, z)])
        normals = np.vstack((spine[1, :] - spine[0, :], spine[2:, :] - spine[:-2, :], spine[-1, :] - spine[-2, :]))

        a = bpn.Draw(**names)
        a.skin(spine, **kwargs_ngon)
        a_exp = a.export()
        -a
        super().__init__(**{**names, **kwargs_bpnmsh})
        self.shade(kwargs_this['shade'])
        if kwargs['subsurf']:
            self.subsurf(kwargs_this['subsurf_levels'], kwargs_this['subsurf_render_levels'])

        self.xsec = self.XSec(self, normals, a_exp)

    class XSec:
        """Cross sections of a tube: a collection of DirectedSubMsh's"""
        def __init__(self, parent, normals, draw_export):
            self.all = [bpn.turtle.DirectedSubMsh(parent, normals[i, :], **s) for i, s in enumerate(draw_export)]
            self._normals = normals

        @property
        def n(self):
            """Number of cross sections."""
            return len(self.all)

        @property
        def centers(self):
            """The 'spine' of the tube. nCrossSections X 3 numpy array."""
            return np.array([x.origin.co[0, :] for x in self.all])
        
        # @centers.setter
        # def centers(self, new_centers):
        #     new_centers = np.array(new_centers)
        #     assert np.shape(new_centers) == (self.n, 3)
        #     for i in range(self.n):
        #         self.all[i].center = new_centers[i, :]

        # def update_normals(self):
        #     """Update normals based on the location of the centers."""
        #     spine = self.centers
        #     self.normals = np.vstack((spine[1, :] - spine[0, :], spine[2:, :] - spine[:-2, :], spine[-1, :] - spine[-2, :]))

        # @property
        # def normals(self):
        #     """Normals of each x-section"""
        #     return np.array(self._normals)

        # @normals.setter
        # def normals(self, new_normals):
        #     new_normals = np.array(new_normals)
        #     assert np.shape(new_normals) == (self.n, 3)
        #     for i in range(np.shape(new_normals)[0]):
        #         self.all[i].normal = new_normals[i, :]

def test_skin():
    θ = np.radians(np.arange(0, 360+40, 40))
    z1 = np.sin(θ)
    y1 = np.cos(θ)
    x1 = θ/2

    spine = np.array([np.array((tx, ty, tz)) for tx, ty, tz in zip(x1, y1, z1)])
    a = bpn.Draw('testskin')
    a.skin(spine, n=4, r=0.3)
    +a
    
def test_tube_01():
    θ = np.radians(np.arange(0, 360+40, 40))
    z1 = np.sin(θ)
    y1 = np.cos(θ)
    x1 = θ/2

    t = Tube('myTube', x=x1, y=y1, z=z1, n=4, th=0, shade='flat', subsurf=True)

    x = t.xsec.all[5]
    x.scale((3, 8, 1))
    x.twist(-45)

def test_tube_03_mobius():
    θ = np.radians(np.arange(0, 360+40, 40))
    r = 1.5
    x1 = r*np.cos(θ)
    y1 = r*np.sin(θ)
    z1 = np.zeros_like(θ)

    spine = np.array([np.array((tx, ty, tz)) for tx, ty, tz in zip(x1, y1, z1)])
    normals = np.vstack((spine[1, :] - spine[0, :], spine[2:, :] - spine[:-2, :], spine[-1, :] - spine[-2, :]))

    t = Tube('mobius', x=x1, y=y1, z=z1, n=8, th=0, shade='flat', subsurf=True)
    t.subsurf(3, 3)
    # t.scale(0.6)
    # t.apply_matrix()

    X = t.xsec.all
    nX = len(X)
    for ix, x in enumerate(X):
        x.origin = bpn.trf.PointCloud((x1[ix], y1[ix], z1[ix]), np.eye(4))
        x.normal = bpn.trf.PointCloud(normals[ix, :]+x.origin.co[0, :], np.eye(4))
        x.scale((0.3, 1, 1))
        x.twist(360*ix/(nX-1))
    
    for ix in (0, -1):
        X[ix].normal = bpn.trf.PointCloud(np.array([0, 1, 0])+X[ix].origin.co[0, :], np.eye(4))

test_tube_03_mobius()
