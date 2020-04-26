"""
Demonstrations using the bpn package

Functions:
    spheres - keyframe animation
    dna     - animated plots
    heart   - plot a heart
    arch    - surface plots with 2d functions
    zoo     - creates a zoo of primitive objects
    spiral  - animates an object along a spiral path

    plane_slice - sculpting and morphing
    tongue - a morph that looks like a tongue

Turtle module:
    draw_basic - Spring-like structure
    draw_atom  - Electron cloud-like structure
    draw_link  - One link of a chain
    draw_spring - Illustrates skinning in the turtle module

Grease pencil drawing and animation:
    grease_pencil - spirals, strokes with varying transparency and thickness.

Tube class:
    bulge_tube - tube with a bulge in the middle
    spring - animating a spring using the Tube class
    mobius - make a mobius strip
"""
import sys
import types
import numpy as np

import pntools as pn

import bpy #pylint: disable=import-error
import bmesh  #pylint: disable=import-error
import mathutils #pylint: disable=import-error

from . import new, env, turtle, trf, utils

def spheres():
    """
    Demonstration for animating a sphere using blender's functions.
    """
    # Animation with blender's keyframe_insert
    s1 = new.sphere(obj_name='sphere1', msh_name='sph', coll_name='Spheres')
    frameID = [1, 50, 100]
    loc = [(1, 1, 1), (1, 2, 1), (2, 2, 1)]
    attrs = ['location', 'rotation_euler', 'scale']
    for thisFrame, thisLoc in zip(frameID, loc):
        bpy.context.scene.frame_set(thisFrame)
        for attr in attrs:
            setattr(s1(), attr, thisLoc)
            s1().keyframe_insert(data_path=attr, frame=thisFrame)

    # Animation with core.Object's 'key' function.
    s2 = new.sphere(name='sphere2', msh_name='sph', coll_name='Spheres')
    s2.key(1)
    s2.loc = (2, 2, 2)
    s2.key(26)
    s2.scl = (1, 0.2, 1)
    s2.key(51)
    s2.scl = (1, 2, 0.2)
    s2.key(76)

    # chaining absolute values (same as above)
    s3 = new.sphere(name='sphere3', msh_name='sph', coll_name='Spheres')
    s3.key(1, 's').key(26, 's', [(0.5, 0.5, 1)]).key(51, 's', [(1, 3, 0.3)])

    # chaining transforms (relative)
    s4 = new.sphere(name='sphere4', msh_name='sph', coll_name='Spheres')
    s4.key(1).translate((0, 0, 2)).key(26).scale((1, 1, 0.3)).key(51).scale((1, 1, 4)).key(101)
    
    env.Key().auto_lim()

    # coordinate frame display
    s5 = new.sphere('sphere5', msh_name='sph', coll_name='Spheres')
    s5.show_frame('sphere5_CoordFrame', coll_name='Spheres')
    s5.loc = (-2, -2, -1)
    s5.rotate((30, 90, 0))
    s5.show_frame()

def dna():
    """
    Animate two strands of DNA
    """
    a = np.linspace(-2.0*np.pi, 2.0*np.pi, 100)
    f1 = lambda a, offset: np.sin(a+offset)
    x = f1(a, np.pi/2)
    y = f1(a, 0)
    z = a

    n = np.size(x)
    v2 = [(xv, yv, zv) for xv, yv, zv in zip(x, y, z)]
    e2 = [(i, i+1) for i in np.arange(0, n-1)]

    s1 = new.mesh(v=v2, e=e2, name='strand1', coll_name='Plots')
    s2 = new.mesh(x=-x, y=-y, z=z, name='strand2', coll_name='Plots')
    
    frames = (1, 50, 100, 150, 200)

    for s in (s1, s2):
        s.key(frames[0], 'r')
        for i in np.arange(1, np.size(frames)):
            s.rotate((0, 0, 90))
            s.key(frames[i], 'r')

    env.Key().auto_lim()

def heart():
    """Plot a heart"""
    a = np.linspace(-1.0*np.pi, 1.0*np.pi, 100)
    new.mesh(x=np.sqrt(np.abs(a))*np.sin(a), y=np.abs(a)*np.cos(a), z=np.zeros_like(a), name='heart', coll_name='Plots')

def arch():
    """2D surface plots"""
    def xyifun(alpha):
        return lambda x, y: np.sqrt(alpha-np.abs(x))

    for i in np.arange(1, 7):
        rf = new.mesh(xyfun=xyifun(i), x=np.linspace(0, i, 60), y=[1, 2], msh_name='sqrt_1'+str(i), obj_name='sqrt_1'+str(i), coll_name='Arch')
        rf.loc = rf.loc + mathutils.Vector((0.0, 3.0, 0.0))
        rf = new.mesh(xyfun=xyifun(i), x=np.linspace(-i, 0, 60), y=[1, 2], msh_name='sqrt_2'+str(i), obj_name='sqrt_2'+str(i), coll_name='Arch')
        rf.loc = rf.loc + mathutils.Vector((0.0, 3.0, 0.0))

def parabola():
    """
    Draws two parabolas.
    You can use 
    (vertices, faces) v=v1, f=f1, OR 
    (x, y, z) like MATLAB surf, OR 
    (function) xyfun=fun
    """
    # method 1: using the algebraic function
    fun = lambda x, y: x*x+y*y
    x1 = np.arange(-2, 2.5, 0.02)
    y1 = np.arange(-2, 2.5, 0.2)
    p_fun = new.mesh(xyfun=fun, x=x1, y=y1, name='parabola_fun', coll_name='surface')
    p_fun.loc += mathutils.Vector((4.0, -4.0, 0.0))

    def fun2mat(xyfun, tx=np.array([]), ty=np.array([])):
        """
        This functionality is already in the bpn module.
        It is here only to illustrate the versatility of new.mesh creation
        """
        assert isinstance(xyfun, types.FunctionType)
        assert xyfun.__code__.co_argcount == 2 # function has two input arguments
        if tx is fun2mat.__defaults__[0]: # default ranges
            tx = np.arange(-2, 2, 0.1)
        if ty is fun2mat.__defaults__[1]:
            ty = np.arange(-2, 2, 0.1)
        return np.array([[xyfun(xv, yv) for yv in ty] for xv in tx])

    # method 2: MATLAB-style surf, using a 2d matrix Z
    z1 = fun2mat(fun, x1, y1)
    p_xyz = new.mesh(x=x1, y=y1, z=z1, name='parabola_xyz', coll_name='surface')
    p_xyz.loc += mathutils.Vector((-4.0, -4.0, 0.0))

    def mat2mesh(tz, tx=np.array([]), ty=np.array([])):
        """
        z is a 2-D numpy array or a 2D list
        returns:
            v list of vertices
            f list of faces
        This is here only for demonstration. It is already in bpn module.
        """
        if tx is mat2mesh.__defaults__[0]:
            tx = np.arange(0, np.shape(tz)[0])
        if ty is mat2mesh.__defaults__[1]:
            ty = np.arange(0, np.shape(tz)[1])

        nX = len(tx)
        nY = len(ty)

        assert len(tx) == np.shape(tz)[0]
        assert len(ty) == np.shape(tz)[1]
        
        v = [(xv, yv, tz[ix][iy]) for iy, yv in enumerate(ty) for ix, xv in enumerate(tx)]
        f = [(iy*nX+ix, iy*nX+ix+1, (iy+1)*nX+(ix+1), (iy+1)*nX+ix) for iy in np.arange(0, nY-1) for ix in np.arange(0, nX-1)]
        return v, f

    # method 3: by specifying the vertices and faces - this is here mainly for testing
    v1, f1 = mat2mesh(z1, tx=x1, ty=y1)
    p_vf = new.mesh(v=v1, f=f1, name='parabola_vf', coll_name='surface')
    p_vf.loc += mathutils.Vector((0, 4.0, 0.0))

def zoo():
    """
    Create a zoo of primitives. 
    """
    new.sphere(obj_name='sph30', msh_name='sp30', r=0.7, u=3, v=2, coll_name='zoo')
    new.monkey(name='L', msh_name='M', coll_name='zoo')
    new.sphere(name='Sph', r=2, u=6, v=8, coll_name='zoo')
    new.cube(name='de', msh_name='e', size=0.4, coll_name='zoo')
    new.cone(name='mycone', segments=4, diameter1=2, diameter2=2, depth=2*np.sqrt(2), cap_ends=True, cap_tris=False, coll_name='zoo')
    new.cone(name='mycone1', coll_name='zoo')
    new.cone(name='mycone2', seg=3, d=1, coll_name='zoo')
    new.cone(name='mycone3', seg=3, r1=3, r2=2, d=0, cap_ends=False, coll_name='zoo')

    new.polygon(name='hex', seg=6, coll_name='zoo')
    new.ngon('circle', n=32, r=1, coll_name='zoo')

    new.polygon(name='hex', seg=6, coll_name='zoo')

    for obj in bpy.data.collections['zoo'].objects:
        utils.enhance(obj).translate(np.random.randint(-6, 6, 3))


def spiral():
    """
    Animating along a path with a few lines of code.
    """
    sp = new.spiral(name='spiral')
    sp.rotate((0, 30, 0))

    s = new.sphere(name='sphere', r=0.3, u=4, v=2)
    s.key(1, 'l')
    for idx, loc in enumerate(list(sp.pts.in_world().co)):
        s.key(idx+2, 'l', [tuple(loc)])

def spiral2():
    """
    Animating along a path, with internal rotation.
    Demonstrates the use of Quaternions for rotation.
    """
    sp = new.spiral('spiral', n_rot=6)
    sp.scl = (0.5, 1, 1)
    sp.frame = trf.Quat([1, 0, 0], np.pi/6)*sp.frame

    s = new.sphere('sph', u=4, v=3)
    s.show_frame() # this one is just to create the gp object
    s.key(1)

    sp_pts = sp.pts.in_world().co
    for frame_number in range(0, np.shape(sp.pts.co)[0]):
        s.loc = sp_pts[frame_number, :]
        s.frame = trf.Quat([0, 0, 1], 5*np.pi/180, origin=s.loc)*s.frame
        s.frame_gp.keyframe = frame_number+1
        s.show_frame()
        s.key(frame_number+1)

    env.Key().auto_lim()

def plane_slice():
    """
    Using the plane slicer to 'sculpt' simple objects.
    """
    r = 1
    n = 4
    sph = new.sphere(name='sphere', r=r)

    subtended_angle = 2*np.pi/n
    trans = r*np.cos(subtended_angle/2)
    sph.translate(z=trans)

    for _ in range(n-1):
        sph.slice_z().rotate(np.degrees((subtended_angle, 0, 0)))

    len_z = np.max(sph.v[:, -1]) - np.min(sph.v[:, -1])
    sph.translate(z=-0.8*len_z)
    sph.slice_z(slice_dir='pos')
    len_z = np.max(sph.v[:, -1]) - np.min(sph.v[:, -1])
    sph.translate(z=len_z)
    sph.morph(frame_start=151)  #pylint:disable=no-member
    return sph

def tongue(poly_smooth=True):
    """
    Morph should look like a tongue in one direction, and an alien helmet in another.

    During this, I learned that vertices should always be selected in an interval (it can be with a small epsilon), but exact values don't seem to work.
    """
    sph = new.sphere(name='tongue')
    sph.slice_x().slice_y().slice_z()

    eps = 0.002
    v = sph.v
    sel = np.logical_and.reduce((v[:, 0] > -eps, v[:, 0] < eps, v[:, 1] > -eps, v[:, 1] < eps)) #pylint: disable=no-member
    v[sel, 0:2] = v[sel, 0:2] - 0.2
    sph.v = v
    sph.morph(n_frames=25, frame_start=100) #pylint:disable=no-member
    env.Key().goto(125)
    sph.subsurf(2, 2)
    if poly_smooth:
        sph.shade('smooth')  #pylint:disable=no-member
    else:
        sph.shade('flat')  #pylint:disable=no-member

    return sph

def draw_basic():
    """Draw a loopy thing."""
    a = turtle.Draw('link')
    bmesh.ops.create_circle(a.bm, radius=0.2, segments=6)
    for vert in a.bm.verts[:]:
        vert.co += mathutils.Vector((0., -1., 0))
    a.spin(angle=np.pi, steps=3, axis='x', cent=(0., 0., 0.))
    for i in range(5):
        a.spin(angle=np.pi, steps=3, axis=(1., 1.0-2.0*(i%2), 0), cent=(2*i+1.0, 0., 0))
    return +a

def draw_atom():
    """Electron clouds-like structure."""
    a = turtle.Draw('cloud', coll_name='atom')
    a.ngon(n=2, r=0.1)
    for vert in a.bm.verts[:]:
        vert.co += mathutils.Vector((0., -1., 0))
    a.spin(angle=np.pi, steps=24, axis='x', cent=(0., 0., 0.))
    a.spin(angle=2*np.pi, steps=6, axis='y', cent=(0., 0., 0.), geom=turtle.Geom(a.bm).all, use_duplicate=True)
    cloud = +a
    cloud.scale((1, 0.6, 1))
    nucleus = new.sphere('nucleus', r=0.2, coll_name='atom')
    return (nucleus, cloud)

def draw_link(n_u=6, n_v=16, l=1, r_v=1, r_u=0.2):
    """Draw one link of the chain. Same as the example in bmesh.ops page"""
    a = turtle.Draw('link')
    u_start = a.ngon(n=n_u, r=r_u)
    for vert in u_start.v:
        vert.co += mathutils.Vector((0., -r_v, 0))
    u_end = a.spin(angle=np.pi, steps=n_v, axis='x', cent=(0., 0., 0.))

    n_start = a.extrude(u_end.e)
    for vert in n_start.v:
        vert.co += mathutils.Vector((0, 0, l))

    n_end = a.spin(angle=np.pi, steps=n_v, axis='x', cent=(0., 0., l))
    a.join(u_start.e + n_end.e)
    return +a

def draw_spring():
    """Illustrates how to skin a curve using the Draw class."""
    θ = np.radians(np.arange(0, 360*6+40, 40))
    z1 = np.sin(θ)
    y1 = np.cos(θ)
    x1 = θ/2

    spine = np.array([np.array((tx, ty, tz)) for tx, ty, tz in zip(x1, y1, z1)])
    a = turtle.Draw('testskin')
    a.skin(spine, n=4, r=0.3)
    return +a

def grease_pencil():
    """Illustrate making animated 2d plots with grease pencil."""
    # equivalent of MATLAB's figure()
    gp = new.pencil(gp_name='myGP', obj_name='myGPobj', coll_name='Pencil', layer_name='sl1')

    θ = np.radians(np.arange(0, 360*2+1, 1))
    z1 = np.sin(θ)
    y1 = np.cos(θ)
    x1 = θ/2

    # equivalent of plot
    pc1 = trf.PointCloud(np.vstack((x1, y1, z1)).T, trf.normal2tfmat((1, 1, 1)))
    pc2 = trf.PointCloud(np.vstack((x1, y1, z1)).T, trf.normal2tfmat((0, 0, 1)))
    gp.stroke(pc1, color=2, layer='sl1', keyframe=0)
    # pressure controls thickness of individual points
    gp.stroke(pc2, color=1, layer='sl3', keyframe=10, pressure=np.linspace(0, 3, len(θ)))
    # strength seems to control transparencu of individual points
    gp.stroke(pc1, color=2, layer='sl1', keyframe=20, strength=np.linspace(0, 1, len(θ)))
    gp.keyframe = 30

    # show the frame for point cloud 1
    # pcf = pc1.frame.as_points()
    # gp.layer = 'crd'
    # gp.stroke(trf.PointCloud(pcf.co[[0, 1]]), color='crd_i', line_width=80)
    # gp.stroke(trf.PointCloud(pcf.co[[0, 2]]), color='crd_j', line_width=80)
    # gp.stroke(trf.PointCloud(pcf.co[[0, 3]]), color='crd_k', line_width=80)
    emp = new.empty('pc1_frame', coll_name='Pencil')
    emp.frame = pc1.frame
    emp.show_frame()
    return gp

def bulge_tube():
    """
    Draws a tube with a bulge in the middle.
    Introduction to the Tube class.
    """
    θ = np.radians(np.arange(0, 360+40, 40))
    z1 = np.sin(θ)
    y1 = np.cos(θ)
    x1 = θ/2

    t = new.Tube('myTube', x=x1, y=y1, z=z1, n=4, th=0)
    t.shade('flat') # pylint: disable=no-member
    t.subsurf(2, 2)

    x = t.xsec.all[5]
    x.scale((3, 8, 1))
    x.twist(-45)

    # show coordinate frames
    for i, x in enumerate(t.xsec.all):
        e = new.empty(name=str(i), coll_name='bulge_tube_frames')
        e.frame = x.frame
        e.show_frame()
    return t

def spring():
    """Animating a spring using the Tube class."""
    θ = np.radians(np.arange(0, 360*6+40, 40))
    z1 = np.sin(θ)
    y1 = np.cos(θ)
    x1 = θ/2
    s = new.Tube('spring', x=x1, y=y1, z=z1)
    s.shade('smooth') #pylint: disable=no-member
    s.subsurf(2, 2)
    s.xsec.centers = np.vstack((x1/2, y1, z1)).T
    s.morph(frame_start=100) #pylint: disable=no-member
    return s

def mobius():
    """Makes a mobius strip using the Tube class"""
    θ = np.radians(np.arange(0, 360+40, 40))
    r = 1.5
    x1 = r*np.cos(θ)
    y1 = r*np.sin(θ)
    z1 = np.zeros_like(θ)

    spine = np.array([np.array((tx, ty, tz)) for tx, ty, tz in zip(x1, y1, z1)])
    normals = np.vstack((spine[1, :] - spine[0, :], spine[2:, :] - spine[:-2, :], spine[-1, :] - spine[-2, :]))

    t = new.Tube('mobius', x=θ, y=np.zeros_like(θ), z=np.zeros_like(θ), n=8, th=0)
    t.shade('flat') #pylint: disable=no-member
    t.subsurf(3, 3)
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

    X[0].origin = trf.PointCloud((2, 0, 0), np.eye(4))
    X[-1].origin = trf.PointCloud((2, 0, 0), np.eye(4))
    return t


def handler1():
    """Event handler example for manipulating one object based on the status of another."""
    s1 = new.sphere('sph1', coll_name='handler')
    s2 = new.sphere('sph2', coll_name='handler')
    
    def receiver(x): # pylint: disable=unused-argument # event receiver functions need one input argument
        s2.show_frame()

    # when s1 changes location, show s2's frame
    pn.add_handler(s1, 'loc', receiver, 'post')

    s2.loc = (0, 2, 0)
    s1.loc = (0, -2, 0)

def handler2():
    """Event handler demonstration to create a simple projection"""
    def receiver_func(self): # self is s1 if a handler is imposed on s1
        s2.loc = (self.loc[0], self.loc[1], 0) # projection on the XY plane

    s1 = new.sphere('sph1', r=0.4)
    s2 = new.sphere('sph2', r=0.7)
    s1.add_handler('loc', receiver_func)

    s1.loc = (0, 0, 0)

    n_frames = 25
    for kc in range(1, n_frames):
        s1.loc = (np.sin(kc*2*np.pi/n_frames), kc*2*np.pi/n_frames, 2*np.cos(kc*2*np.pi/n_frames))
        s1.key(kc, 'l')
        s2.key(kc, 'l')

    env.Key().auto_lim()


def main():
    """
    Runs all the demos. Avoid using this!
    """
    all_mem = pn.module_members(sys.modules[__name__], False)
    all_func = [eval(name) for name, typ in all_mem.items() if typ == 'function' and name != 'main'] #pylint: disable=eval-used
    for func in all_func:
        func()
