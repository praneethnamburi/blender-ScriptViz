"""
Transformations sub-module.

In the spirit of developing hierarchical objects, this module introduces
CoordFrame class. A co-ordinate system in this context is defined by a
4x4 matrix, or an origin and three unit vectors. Origin and axes are
specified with respect to world coordinates.

Points in the world can be transformed:
1) with respect to a coordinate frame, OR
    - These operations do not affect the coordinate frame wrt to the
      world frame.
2) by 'binding' them to a coordinate frame, and transforming the frame.
    - Affecting the coordinate frame changes the location of the points
      in the world frame.

Points and co-ordinates can be more 'tightly' bound, where the
coordinate system itself is defined with respect to the points. Consider
the DirectedSubMsh for example. The normal, or k direction is set
externally, but the X direction is set according to the vector from the
center of the points in the mesh to the first point in the mesh.

The 'general' matrix transformation function is given by trf.transform.
It allows you to specify "I have locations of points pts in a frame
pt_frame. Apply the transformation matrix to these points, in a
transformation frame tf_frame, and return the locations in the frame
out_frame."

It is useful to categorize transforms into three types:
1) Keep the frame, and transform points within the frame
   (PointCloud.transform).
2) Transform the frame, and keep relative locations of the points
   (PointCloud.CoordFrame.transform).
3) Re-frame the points in a new coordinate frame (PointCloud.reframe).

PointCloud.transform is useful for transforming point locations in a
given frame, while keeping the frame. 

CoordFrame.transform is useful for moving around coordinate frames. When
a PointCloud's frame is transformed using this method, point locations
relative to the frame don't change. In other words, points move around
in world frame, but the locations within their frame (basis) does not
change.

PointCloud.reframe is used for maintaining the locations of points in
world frame, but assigning a new basis!
"""
import math
import numpy as np
from numpy.linalg.linalg import inv, norm
from sklearn.decomposition import PCA


class CoordFrame:
    """
    Coordinate frame defined by origin and unit vectors.
    Unit vectors are given in 'world' coordinates, where origin in zero, and matrix is eye(4)

    For the bpn module, this class is meant to enforce the idea that every transformation is applied within the context of a give coordinate frame.

    Applying a transformation in this frame:
        new_crd = self.m@tfmat@inv(self.m)@crd
        inv(m)@crd -> brings world coordinates into space defined by the current coordinate system
        tfmat@ -> applies transformation in current space.
        m@ -> moves coordinates back into world space.

    Convention for this module:
        The 'parent' of any CoordFrame object IS the world frame.
        In other words, the columns of 'm', i.e., this frame's unit vectors, are defined in world frame.
    """
    def __init__(self, m=None, **kwargs):
        self._m = m4(m, **kwargs)

    @property
    def m(self):
        """4x4 transformation matrix to bring points from this frame to the world."""
        return self._m

    @m.setter
    def m(self, new_m):
        self._m = new_m

    @property
    def origin(self):
        """Origin of the coordinate system."""
        return self._m[0:3, 3]
    @origin.setter
    def origin(self, new_origin):
        new_origin = np.array(new_origin)
        assert len(new_origin) == 3
        self._m[0:3, 3] = new_origin

    @property
    def i(self):
        """X unit vector represented in world coordinates."""
        return self._m[0:3, 0]
    @i.setter
    def i(self, new_i):
        new_i = np.array(new_i)
        assert len(new_i) == 3 # not enforcing i to be a unit vector!
        self._m[0:3, 0] = new_i

    @property
    def j(self):
        """X unit vector represented in world coordinates."""
        return self._m[0:3, 1]
    @j.setter
    def j(self, new_j):
        new_j = np.array(new_j)
        assert len(new_j) == 3
        self._m[0:3, 1] = new_j

    @property
    def k(self):
        """X unit vector represented in world coordinates."""
        return self._m[0:3, 2]
    @k.setter
    def k(self, new_k):
        new_k = np.array(new_k)
        assert len(new_k) == 3
        self._m[0:3, 2] = new_k

    def as_points(self):
        """Return coordinate frame as a set of four points in world coordinates."""
        v = np.vstack((self.origin, self.origin+self.i, self.origin+self.j, self.origin+self.k))
        return PointCloud(v, np.eye(4))

    def transform(self, tfmat, tf_frame=None):
        """
        Transform the coordinate frame in reference frame tf_frame (defaults to world frame).
        Returns a CoordFrame object (a new one)

        This is used for "change frame, keep point relationships the frame" transform
        """
        tfmat = np.array(tfmat)
        assert np.shape(tfmat) == (4, 4)
        return self.as_points().transform(tfmat, tf_frame).as_frame()

    # These two functions are here for clarity
    def from_world(self, coord_world):
        """Return point locations in the current frame of reference."""
        coord_local = apply_matrix(inv(self.m), coord_world)
        return coord_local
    
    def to_world(self, coord_local):
        """Return point locations in the world frame."""
        coord_world = apply_matrix(self.m, coord_local)
        return coord_world
    
    def __repr__(self):
        exponent = np.min((np.round(-np.log10(np.max(np.abs(self.m[:-1, :])))) + 3, 6))
        return self.__class__.__name__+'\n'+str(np.round(self.m*(10**exponent))/(10**exponent))


class PointCloud:
    """
    Encapsulate vertex locations with the reference frame.

        v = PointCloud(vert, local_frame)
        v.co    : coordinates in local reference frame, local_frame
        v.frame : frame of reference for these coordinates
    
    Remember: A coordinate frame IS a point cloud
    """
    def __init__(self, vert, frame=np.eye(4)):
        """
        :param vert: (2d numpy array) size nV x 3 specifying locations of points
        :param frame: (bpn.trf.CoordFrame) co-ordinate frame for the locations
        """
        if type(frame).__name__ != 'CoordFrame':
            frame = CoordFrame(frame)
        vert = np.array(vert)
        if np.shape(vert) == (3,): # only one point in the cloud
            vert = np.array([vert])
        assert np.shape(vert)[1] == 3
        self.co = vert
        self.frame = frame
    
    @property
    def n(self):
        """Number of points in the cloud."""
        return np.shape(self.co)[0]
    
    def as_frame(self):
        """
        Return point cloud as coordinate frame.
        First point is treated as origin.
        Unit vector from origin to second point is i
        Unit vector from origin to second point is j
        Unit vector from origin to second point is k
        """
        assert np.shape(self.co) == (4, 3)
        o = self.co[0, :]
        i = self.co[1, :] - o
        j = self.co[2, :] - o
        k = self.co[3, :] - o
        return CoordFrame(i=i, j=j, k=k, origin=o, unit_vectors=False)
    
    # The following methods all return a NEW point cloud.
    # They DO NOT modify the coordinates of this point cloud.
    # Modifying the point cloud in-place might make sense as meshes get bigger??
    # Since point clouds are meant for sub-meshes (small ones), I'll leave this design choice be for now.
    @property
    def center(self):
        """Center of the point cloud as a new pointcloud object"""
        return PointCloud(np.mean(self.co, axis=0, keepdims=True), self.frame)

    def in_frame(self, output_coord_system):
        """Return point cloud in the given frame of reference (output_coord_system)."""
        new_co = transform(np.eye(4), self.co, vert_frame_mat=self.frame, tf_frame_mat=self.frame, out_frame_mat=output_coord_system)
        return PointCloud(new_co, output_coord_system)

    def in_world(self):
        """
        Return point cloud in world.
        When the tf matrix becomes an identity matrix, this formula (see bpn.trf.transform):
            tfmat = inv(out_frame)@tf_frame@tfmat@inv(tf_frame)@vert_frame
        reduces to:
            tfmat = inv(out_frame)@vert_frame
        
        Then, if out_frame is identity (world frame), then this further reduces to:
            tfmat = vert_frame
        """
        out_frame_mat = np.eye(4)
        world_co = transform(np.eye(4), self.co, vert_frame_mat=self.frame, tf_frame_mat=self.frame, out_frame_mat=out_frame_mat)
        return PointCloud(world_co, out_frame_mat)

    def transform(self, tfmat, tf_frame=None):
        """
        Apply a transform in the frame of reference tf_frame.
        Defaults to applying a transform in the current frame of refrence.
        Returns:
            PointCloud

        This is "keep frame, change points relationships to the frame" transform
        """
        if tf_frame is None:
            tf_frame = self.frame
        co = transform(tfmat, self.co, vert_frame_mat=self.frame, tf_frame_mat=tf_frame, out_frame_mat=self.frame)
        return PointCloud(co, self.frame)

    def reframe(self, new_frame):
        """
        Re-frame the points. This maintains point locations in the world
        frame, but changes the current frame of reference.
        """
        # note that tf_frame_mat is meaningless when tfmat is an identity matrix
        co = transform(np.eye(4), self.co, vert_frame_mat=self.frame, tf_frame_mat=np.eye(4), out_frame_mat=new_frame)
        return PointCloud(co, new_frame)
    
    def reframe_pca(self, **mapping):
        """
        Re-frame the point cloud by changing directions according to principal components.
        Convention for the body:
            z_dir = 1 : up is positive
            z_dir = -1 : down is positive (for arm bones for example)
            x_dir positive is facing forward
            y_dir = z_dir x x_dir (vector satisfying the right hand rule)
        :param mapping: (dict) {'i':1, 'j':2} implies:
            i-direction of the new frame uses PC1
            j-direction of the new frame uses PC2
            Supply only two. The third one will be automatically computed assuming a right handed frame.
        """
        if not mapping:
            mapping = {'i':3, 'k':1}
        assert len(mapping) == 2
        pca = PCA(n_components=3)
        pca.fit(self.in_world().co)
        if 'i' in mapping:
            x_dir = pca.components_.T[:, np.abs(mapping['i'])-1]
            x_dir = x_dir if np.sign(mapping['i'])*x_dir[0] > 0 else -x_dir # prioritize 'front' of anatomy with positive i in mapping
        if 'j' in mapping:
            y_dir = pca.components_.T[:, np.abs(mapping['j'])-1]
            y_dir = y_dir if np.sign(mapping['j'])*y_dir[1] > 0 else -y_dir
        if 'k' in mapping:
            z_dir = pca.components_.T[:, np.abs(mapping['k'])-1]
            z_dir = z_dir if np.sign(mapping['k'])*z_dir[2] > 0 else -z_dir # prioritize 'down' facing with a negative k in mapping (e.g. arm bones)
        if 'i' not in mapping:
            x_dir = np.cross(y_dir, z_dir)
        if 'j' not in mapping:
            y_dir = np.cross(z_dir, x_dir)
        if 'k' not in mapping:
            z_dir = np.cross(x_dir, y_dir)
        return self.reframe(CoordFrame(i=x_dir, j=y_dir, k=z_dir, origin=self.frame.origin))

    # syntactic ease
    def __call__(self):
        """
        Calling a point cloud returns the coordinates in world frame.
        If there is only one point in the cloud, a 1-D array is returned.
        Convenient for origins - 
            o = PointCloud([a, b, c], frm)
            o() instead of o.co[0, :]
        """
        if self.n == 1:
            return self.in_world().co[0, :]
        return self.in_world().co

    def __repr__(self):
        exponent = np.min((np.round(-np.log10(np.max(np.abs(self.co)))) + 3, 6))
        return self.__class__.__name__+'\n'+str(np.round(self.co*(10**exponent))/(10**exponent))


def transform(tfmat, vert, vert_frame_mat=np.eye(4), tf_frame_mat=None, out_frame_mat=None):
    """
    Most general form of applying a transformation matrix.

    Apply transformation matrix tfmat on vertices with coordinates specified in vert_frame (current/input frame of reference).
    Apply the transformation in the coordinate frame given by tf_frame
    Output the vertices in out_frame

    #1. Bring vertices to world frame
    vert = vert_frame.to_world(vert)
    #2. Bring vertices to tf frame
    vert = tf_frame.from_world(vert)
    #3. Apply the transformation matrix in tf frame
    vert = apply_matrix(tfmat, vert)
    #4. Bring vertices to world frame
    vert = tf_frame.to_world(vert)
    #5. Bring vertices to out frame
    vert = out_frame.from_world(vert)
    """
    # if output frame is not specified, set it to input frame.
    if out_frame_mat is None:
        out_frame_mat = vert_frame_mat
    # if the frame of reference for transformation is not specified, perform transform in the vertex frame of reference.
    if tf_frame_mat is None:
        tf_frame_mat = vert_frame_mat
    if type(vert_frame_mat).__name__ == 'CoordFrame':
        vert_frame_mat = vert_frame_mat.m
    if type(tf_frame_mat).__name__ == 'CoordFrame':
        tf_frame_mat = tf_frame_mat.m
    if type(out_frame_mat).__name__ == 'CoordFrame':
        out_frame_mat = out_frame_mat.m
    # ensure 4x4
    vert_frame_mat = m4(vert_frame_mat)
    tf_frame_mat = m4(tf_frame_mat)
    out_frame_mat = m4(out_frame_mat)
    tfmat = m4(tfmat)

    mat = inv(out_frame_mat)@tf_frame_mat@tfmat@inv(tf_frame_mat)@vert_frame_mat
    return apply_matrix(mat, vert)

def v4(vert):
    """
    coordinates (nVertex x 3) -> (nVertex x 4) for applying 4x4 transformation matrices.
    """
    assert np.shape(vert)[1] == 3
    return np.concatenate((vert, np.ones([np.shape(vert)[0], 1])), axis=1)

def m4(m=None, **kwargs):
    """
    Construct a 4x4 transformation matrix from various types of inputs.
        m4(m=mat) mat is either 3x3 or 4x4 (2d numpy array, 2d list)
        m4(i=i1, j=j1, k=k1, origin=o1) i, j, k vectors (doesn't have to be unit    vectors, they will be normalized in here) and origin
        m4(i=i1, j=j1, k=k1) In this case, origin is assumed to be at world origin
        m4() This will return a 4x4 identity matrix (world coordinate frame)
        m4(mat)
    CAUTION:
        m4(mat, unit_vectors=False) default: unit_vectors=True
    """
    if not kwargs and m is None:
        # return world coordinate system if no inputs are given
        return np.eye(4)

    # by default, i, j, k are unit vectors
    # This is my convention
    # This is not the case for blender's matrix_world
    # to remove this restriction, pass unit_vectors=False as input
    if 'unit_vectors' not in kwargs: 
        kwargs['unit_vectors'] = True

    if m is not None:
        m = np.array(m)
        assert np.shape(m) in ((3, 3), (4, 4))
        i = m[0:3, 0]
        j = m[0:3, 1]
        k = m[0:3, 2]
        if np.shape(m) == (4, 4):
            origin = m[0:3, 3]
        if kwargs['unit_vectors']:
            i = norm_vec(i)
            j = norm_vec(j)
            k = norm_vec(k)

    # if conflicting input is given, individual assignments over-ride matrix assignment
    if 'origin' in kwargs:
        origin = kwargs['origin']
    if 'center' in kwargs:
        origin = kwargs['center']
    
    if 'i' in kwargs:
        i = kwargs['i']
        assert len(i) == 3
        if kwargs['unit_vectors']:
            i = norm_vec(i)
    if 'j' in kwargs:
        j = kwargs['j']
        assert len(j) == 3
        if kwargs['unit_vectors']:
            j = norm_vec(j)
    if 'k' in kwargs:
        k = kwargs['k']
        assert len(k) == 3
        if kwargs['unit_vectors']:
            k = norm_vec(k)
    
    if 'origin' not in locals():
        origin = np.zeros(3) 
    
    return np.array([\
        [i[0], j[0], k[0], origin[0]],\
        [i[1], j[1], k[1], origin[1]],\
        [i[2], j[2], k[2], origin[2]],\
        [0, 0, 0, 1]\
        ])

def apply_matrix(mat, vert):
    """
    Apply matrix transformation to a set of vertices.
    :param mat: (2D numpy array) 4 x 4, or 3 x 3 transformation matrix
    :param vert: (2D numpy array) nV x 3
    """
    return (m4(mat)@v4(vert).T).T[:, 0:3]

def normal2tfmat(n, out=None):
    """
    normal2tfmat takes a unit vector (n) and computes a transformation matrix required to transform the point (0, 0, 1) to n.
    If n is not a unit vector, it normalizes it.

    Note that this transformation is not unique, and there is one free parameter.

    Given a direction vector, create a transformation matrix that transforms a shape in the XY plane to the direction of the normal by first rotating along Y axis, and then along X axis.
    n is a 3-element 1-D numpy array

    n is assumed to be the new k_hat, and a two transformation matrices are computed at first:
        RxRy (Rotate around Y-axis first, and then X)
        RyRx (Rotate around X-axis first, and then Y)

    Note that these are not the only two possible transformation matrices. My goal is to minimize twist.
    (Intuitively, these minimize twist, but I am yet to prove this mathematically)

    Of the two possible transformation matrices, the one that displaces x and y the least is chosen.

    The output is still unique. Meaning, given a normal, the algorithm always spits out a unique transformation matrix.
    """
    assert len(n) == 3
    n = norm_vec(n)
    nx = n[0]
    ny = n[1]
    nz = n[2]
    # rotate around y first, then x (RxRy)
    def RxRy():
        d = np.sqrt(1-nx**2)
        if math.isclose(d, 0): # nx == 1
            Rx = np.eye(3) # no rotation around x axis
        else:
            Rx = np.array([\
                [1, 0, 0],\
                [0, nz/d, ny/d],\
                [0, -ny/d, nz/d]\
                ])
        Ry = np.array([\
            [d, 0, nx],\
            [0, 1, 0],\
            [-nx, 0, d]\
            ])
        return Rx@Ry

    def disp_RxRy(): # dispalcement in i and j vectors caused by this transformation
        d = np.sqrt(1-nx**2)
        i_disp_RxRy = np.sqrt(2*(1-d))
        if math.isclose(d, 0): # nx == 1
            j_disp_RxRy = 0
        else:
            if math.isclose(1-nz/d, 0):
                j_disp_RxRy = 0
            else:
                j_disp_RxRy = np.sqrt(2*(1-nz/d))
        return i_disp_RxRy + j_disp_RxRy

    # rotate around x first, then y (RyRx)
    def RyRx():
        d = np.sqrt(1-ny**2)
        if math.isclose(d, 0): # ny == 1
            Ry = np.eye(3)
        else:
            Ry = np.array([\
                [nz/d, 0, nx/d],\
                [0, 1, 0],\
                [nx/d, 0, nz/d]\
                ])
        Rx = np.array([\
            [1, 0, 0],\
            [0, d, -ny],\
            [0, ny, d]\
            ])
        return Ry@Rx # x first, then y
    
    def disp_RyRx():
        d = np.sqrt(1-ny**2)
        if math.isclose(d, 0):
            i_disp_RyRx = 0
        else:
            if math.isclose(1-nz/d, 0):
                i_disp_RyRx = 0
            else:
                i_disp_RyRx = np.sqrt(2*(1-nz/d))
        j_disp_RyRx = np.sqrt(2*(1-d))
        return i_disp_RyRx + j_disp_RyRx

    # of the two possible transformations, return the one causing the least displacement in i, and j vectors. 
    # Why not explicity comput i and j vectors that give the least amount of displacement?
    # This code favors RxRy (if both produce equal displacements in i and j, then RxRy is picked
    if not out:
        if disp_RxRy() <= disp_RyRx():
            return RxRy()
        else:
            return RyRx()
    else:
        assert isinstance(out, str)
        assert out.lower() in ('rxry', 'ryrx')
        if out.lower() == 'rxry':
            return RxRy()
        else:
            return RyRx()

def twisttf(θ):
    """Twist transform is simply a rotation transform around Z."""
    m = np.array([\
        [np.cos(θ), -np.sin(θ), 0],\
        [np.sin(θ), np.cos(θ), 0],\
        [0, 0, 1]\
        ])
    return m

def scaletf(s):
    """Construct a scale transformation matrix from a 3-element s."""
    if isinstance(s, (int, float)):
        s = np.array((1, 1, 1))*float(s)
    s = np.array(s)
    m = np.array([\
        [s[0], 0, 0],\
        [0, s[1], 0],\
        [0, 0, s[2]]\
        ])
    return m

def norm_vec(vec):
    """Return unit vector, and return zero for zero vector."""
    if math.isclose(norm(vec), 0):
        return np.array(vec)
    return np.array(vec)/norm(vec)


class Quat:
    """
    Unit quaternions for 3D rotation.
    This class will force inputs to be unit vectors.
    q = cos(angle/2) + sin(angle/2)*unit_normal
    Example:
        q = Quat([1, 2, 3, 4]) # will be nomalized!
        q[:] will return the normalized quaternion
        q.angle (rotation angle)
        q.normal (normal along the rotation)
        q2*q -> multiply two quaternions (two successive transforms: q, followed by q2)
        q*v -> apply rotation to a 3-element vector v
    """
    def __init__(self, vec, theta=None):
        """
        Initialize a unit quaternion (for a rotation transform).
        :param vec: (tuple, list, numpy array) 
            4-element (w, x, y, z) if supplied without theta
            3-lement (x, y, z) if supplied with theta
        :param theta: (float) rotation angle in radians
        """
        if theta is None:
            assert np.size(vec) == 4
            self._vec = norm_vec(vec)
        else:
            assert np.size(vec) == 3
            self._vec = np.r_[np.cos(theta/2), np.sin(theta/2)*norm_vec(vec)]
    
    w = property(lambda s: s._vec[0])
    x = property(lambda s: s._vec[1])
    y = property(lambda s: s._vec[2])
    z = property(lambda s: s._vec[3])
    xyz = property(lambda s: s._vec[1:])
    angle = property(lambda s: 2*np.arccos(s.w))
    normal = property(lambda s: np.array(s.xyz)/np.sin(s.angle/2))

    def __getitem__(self, key): # q[:] will return the 4-element quaternion vector
        return self._vec[key]

    def __invert__(self): # ~q for conjugate
        return Quat(np.r_[self.w, -self.xyz])

    def __mul__(self, other):
        def _quat_quat_mul(q1, q2):
            q_w = q1.w*q2.w - np.dot(q1.xyz, q2.xyz)
            q_xyz = np.cross(q1.xyz, q2.xyz) + q1.w*q2.xyz + q2.w*q1.xyz
            return Quat(np.r_[q_w, q_xyz])

        def _quat_vec_mul(q, v):
            # q is a quaternion
            # v is nx3 numpy array, or a 3-element list, tuple or nparray
            α = q.angle
            u = q.normal
            udp = u*np.array([np.dot(v, u)]).T
            return (v - udp)*np.cos(α) + np.cross(u, v)*np.sin(α) + udp

        if isinstance(other, Quat):
            # multiplication of two quaternions
            return _quat_quat_mul(self, other)
        
        if isinstance(other, PointCloud):
            # simply transform the points in the point cloud
            # to do the transformation in a reference frame, use
            # q*this_point_cloud.in_frame()
            return PointCloud(_quat_vec_mul(self, other.co), other.frame)

        if isinstance(other, CoordFrame): 
            # rotate a Coordinate frame with the quaternion
            # assumes coordinate frame is specified in world coordinates
            return PointCloud(_quat_vec_mul(self, other.as_points().co), np.eye(4)).as_frame()

        # rotate a vector or nx3 points using the quaternion
        assert np.size(other) == 3 or np.size(other)/np.shape(other)[0] # 1x3 or nx3
        return _quat_vec_mul(self, np.array(other))
