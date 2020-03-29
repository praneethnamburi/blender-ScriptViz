# context.area: VIEW_3D
"""
This is a sandbox. Develop code here!
"""
#-----------------
from bpn_init import * # pylint: disable=wildcard-import, unused-wildcard-import
pn.reload()
env.reset()
#-----------------

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

    t = new.Tube('myTube', x=x1, y=y1, z=z1, n=4, th=0, shade='flat', subsurf=True)

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

    t = new.Tube('mobius', x=θ, y=np.zeros_like(θ), z=np.zeros_like(θ), n=8, th=0, shade='flat', subsurf=True)
    t.scale((1, 1, 0.3))
    t.apply_matrix()

    X = t.xsec.all
    nX = len(X)
    for ix, x in enumerate(X):
        x.origin = trf.PointCloud((x1[ix], y1[ix], z1[ix]), np.eye(4))
        x.normal = trf.PointCloud(normals[ix, :]+x.origin, np.eye(4))
        x.twist(360*ix/(nX-1))
    
    for ix in (0, -1):
        X[ix].normal = trf.PointCloud(np.array([0, 1, 0])+X[ix].origin, np.eye(4))
    
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
    s = new.Tube('spring', x=x1, y=y1, z=z1)
    s.xsec.centers = np.vstack((x1/2, y1, z1)).T
    s.morph(frame_start=100)
    return s



spring()
