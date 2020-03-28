# context.area: VIEW_3D
"""
This is a sandbox. Develop code here!
"""
#-----------------
from bpn_init import * # pylint: disable=wildcard-import, unused-wildcard-import
pn.reload()
env.reset()
#-----------------

class Tube(core.Msh):
    """
    Creates a 'Tube' object with a specified number of cross sections
    and vertical sections.
    """
    def __init__(self, name=None, x=0, y=0, z=0, **kwargs):
        names, kwargs = bpn.utils.clean_names(name, kwargs, {'msh_name':'tube_msh', 'obj_name':'tube_obj', 'priority_obj':'new', 'priority_msh':'new'})
        kwargs_ngon, kwargs = pn.clean_kwargs(kwargs, {'n':6, 'r':0.3, 'theta_offset_deg':-1}, {'n':['segments', 'seg', 'u', 'n'], 'r':['radius', 'r'], 'theta_offset_deg':['theta_offset_deg', 'th', 'offset', 'th_off_deg']})
        kwargs_this, kwargs_bpnmsh = pn.clean_kwargs(kwargs, {'shade':'smooth', 'subsurf':True, 'subsurf_levels':2, 'subsurf_render_levels':2})
        
        spine = np.array([np.array((tx, ty, tz)) for tx, ty, tz in zip(x, y, z)])
        normals = np.vstack((spine[1, :] - spine[0, :], spine[2:, :] - spine[:-2, :], spine[-1, :] - spine[-2, :]))

        a = Draw(**names)
        a.skin(spine, **kwargs_ngon)
        a_exp = a.export()
        -a
        super().__init__(**{**names, **kwargs_bpnmsh})
        self.shade(kwargs_this['shade'])
        if kwargs_this['subsurf']:
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
        
        @centers.setter
        def centers(self, new_centers):
            new_centers = np.array(new_centers)
            assert np.shape(new_centers) == (self.n, 3)
            for i in range(self.n):
                self.all[i].origin = trf.PointCloud(new_centers[i, :], np.eye(4))

        # def update_normals(self):
        #     """Update normals based on the location of the centers."""
        #     spine = self.centers
        #     self.normals = np.vstack((spine[1, :] - spine[0, :], spine[2:, :] - spine[:-2, :], spine[-1, :] - spine[-2, :]))

        @property
        def normals(self):
            """
            Normals of each x-section.
            Returns direction in world
            """
            return np.array([self.all[i].normal for i in range(self.n)])

        @normals.setter
        def normals(self, new_normal_dir):
            """
            Directions are origin-agnostic.
            """
            new_normal_dir = np.array(new_normal_dir)
            assert np.shape(new_normal_dir) == (self.n, 3)
            for i in range(np.shape(new_normal_dir)[0]):
                self.all[i].normal = trf.PointCloud(new_normal_dir[i, :]+self.all[i].origin.co[0, :], np.eye(4))

def test_skin():
    θ = np.radians(np.arange(0, 360*6+40, 40))
    z1 = np.sin(θ)
    y1 = np.cos(θ)
    x1 = θ/2

    spine = np.array([np.array((tx, ty, tz)) for tx, ty, tz in zip(x1, y1, z1)])
    a = Draw('testskin')
    a.skin(spine, n=4, r=0.3)
    +a
    return get('testskin')
    
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

    t = Tube('mobius', x=θ, y=np.zeros_like(θ), z=np.zeros_like(θ), n=8, th=0, shade='flat', subsurf=True)
    t.scale((1, 1, 0.3))
    t.apply_matrix()

    X = t.xsec.all
    nX = len(X)
    for ix, x in enumerate(X):
        x.origin = trf.PointCloud((x1[ix], y1[ix], z1[ix]), np.eye(4))
        x.normal = trf.PointCloud(normals[ix, :]+x.origin.co[0, :], np.eye(4))
        x.twist(360*ix/(nX-1))
    
    for ix in (0, -1):
        X[ix].normal = trf.PointCloud(np.array([0, 1, 0])+X[ix].origin.co[0, :], np.eye(4))
    
    ## make a merge_XS feature
    # bm = bmesh.new()
    # bm.from_mesh(t.bm)
    # bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    # bm.to_mesh(t.bm)
    # t.bm.update()
    # bm.clear()
    # bm.free()

    X[0].origin = PC((2, 0, 0), np.eye(4))
    X[-1].origin = trf.PointCloud((2, 0, 0), np.eye(4))

def spring():
    θ = np.radians(np.arange(0, 360*6+40, 40))
    z1 = np.sin(θ)
    y1 = np.cos(θ)
    x1 = θ/2
    s = Tube('spring', x=x1, y=y1, z=z1)
    s.xsec.centers = np.vstack((x1/2, y1, z1)).T
    s.morph(frame_start=100)

test_tube_03_mobius()
