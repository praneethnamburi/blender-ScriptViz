"""
Transformations sub-module.

In the spirit of developing hierarchical objects, this module introduces CoordFrame class.
A co-ordinate system in this context is defined by a 4x4 matrix, or an origin and three unit vectors. Origin and axes are specified with respect to world coordinates.

Points in the world can be transformed:
1) with respect to a coordinate frame, OR
    - These operations do not affect the coordinate frame wrt to the world frame.
2) by 'binding' them to a coordinate frame, and transforming the frame.
    - Affecting the coordinate frame changes the location of the points in the world frame.

Points and co-ordinates can be more 'tightly' bound, where the coordinate system itself is defined with respect to the points. Consider the DirectedSubMsh for example. The normal, or k direction is set externally, but the X direction is set according to the vector from the center of the points in the mesh to the first point in the mesh.
"""

import numpy as np

class CoordFrame:
    """
    Coordinate frame defined by origin and unit vectors.
    Unit vectors are given in 'world' coordinates, where origin in zero, and matrix is eye(4)

    For the bpn module, this class is meant to enforce the idea that every transformation is applied within the context of a give coordinate frame.

    Applying a transformation in this frame:
        new_crd = self.m@tfmat@np.linalg.inv(self.m)@crd
        np.linalg.inv(m)@crd -> brings world coordinates into space defined by the current coordinate system
        tfmat@ -> applies transformation in current space.
        m@ -> moves coordinates back into world space.

    There are no 'setters' for the properties here on purpose.
    This is meant to be used as a 'read-only' class.
    Classes inheriting from CoordFrame can define setters based on the relationship between points and coordinate frame in that class.

    REMEMBER:
        The 'parent' of any CoordFrame object IS the world frame.
        In other words, the columns of 'm', i.e., this frame's unit vectors, are defined in world frame.
    """
    def __init__(self, **kwargs):
        self.m = m4(**kwargs)

    @property
    def origin(self):
        """Origin of the coordinate system."""
        return self.m[0:3, 3]

    @property
    def i(self):
        """X unit vector represented in world coordinates."""
        return self.m[0:3, 0]

    @property
    def j(self):
        """X unit vector represented in world coordinates."""
        return self.m[0:3, 1]

    @property
    def k(self):
        """X unit vector represented in world coordinates."""
        return self.m[0:3, 2]

    # These two functions are here for clarity
    def from_world(self, coord_world):
        """Return point locations in the current frame of reference."""
        coord_local = apply_matrix(np.linalg.inv(self.m), coord_world)
        return coord_local
    
    def to_world(self, coord_local):
        """Return point locations in the world frame."""
        coord_world = apply_matrix(self.m, coord_local)
        return coord_world


class PointCloud:
    """
    Encapsulate vertex locations with the reference frame.

        v = PointCloud(vert, local_frame)
        v.co    : coordinates in local reference frame, local_frame
        v.frame : frame of reference for these coordinates
    """
    def __init__(self, vert, frame=np.eye(4)):
        """
        :param vert: (2d numpy array) size nV x 3 specifying locations of points
        :param frame: (bpn.trf.CoordFrame) co-ordinate frame for the locations
        """
        if not isinstance(frame, CoordFrame):
            frame = CoordFrame(m=frame)
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
    
    @property
    def center(self):
        """Center of the point cloud as a new pointcloud object"""
        return PointCloud(np.mean(self.co, axis=0, keepdims=True), self.frame)

    # The following methods all return a NEW point cloud.
    # They DO NOT modify the coordinates of this point cloud.
    # Modifying the point cloud in-place might make sense as meshes get bigger??
    # Since point clouds are meant for sub-meshes (small ones), I'll leave this design choice be for now.
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

    def transform(self, tfmat):
        """Apply a transform in the current frame of reference."""
        co = transform(tfmat, self.co, vert_frame_mat=self.frame, tf_frame_mat=self.frame, out_frame_mat=self.frame)
        return PointCloud(co, self.frame)


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
    if isinstance(vert_frame_mat, CoordFrame):
        vert_frame_mat = vert_frame_mat.m
    if isinstance(tf_frame_mat, CoordFrame):
        tf_frame_mat = tf_frame_mat.m
    if isinstance(out_frame_mat, CoordFrame):
        out_frame_mat = out_frame_mat.m
    # ensure 4x4
    vert_frame_mat = m4(m=vert_frame_mat)
    tf_frame_mat = m4(m=tf_frame_mat)
    out_frame_mat = m4(m=out_frame_mat)
    tfmat = m4(m=tfmat)
    inv = np.linalg.inv

    mat = inv(out_frame_mat)@tf_frame_mat@tfmat@inv(tf_frame_mat)@vert_frame_mat
    return apply_matrix(mat, vert)

def v4(vert):
    """
    coordinates (nVertex x 3) -> (nVertex x 4) for applying 4x4 transformation matrices.
    """
    assert np.shape(vert)[1] == 3
    return np.concatenate((vert, np.ones([np.shape(vert)[0], 1])), axis=1)

def m4(**kwargs):
    """
    Construct a 4x4 transformation matrix from various types of inputs.
        m4(m=mat) mat is either 3x3 or 4x4 (2d numpy array, 2d list)
        m4(i=i1, j=j1, k=k1, origin=o1) i, j, k vectors (doesn't have to be unit    vectors, they will be normalized in here) and origin
        m4(i=i1, j=j1, k=k1) In this case, origin is assumed to be at world origin
        m4() This will return a 4x4 identity matrix (world coordinate frame)
    """
    if not kwargs:
        # return world coordinate system if no inputs are given
        kwargs['m'] = np.eye(4)

    if 'm' in kwargs:
        kwargs['m'] = np.array(kwargs['m'])
        assert np.shape(kwargs['m']) in ((3, 3), (4, 4))
        i = kwargs['m'][0:3, 0]
        j = kwargs['m'][0:3, 1]
        k = kwargs['m'][0:3, 2]
        if np.shape(kwargs['m']) == (4, 4):
            origin = kwargs['m'][0:3, 3]

    # if conflicting input is given, individual assignments over-ride matrix assignment
    if 'origin' in kwargs:
        origin = kwargs['origin']
    if 'center' in kwargs:
        origin = kwargs['center']
    # by default, i, j, k are unit vectors
    # This is my convention
    # This is not the case for blender's matrix_world
    if 'unit_vectors' not in kwargs: 
        kwargs['unit_vectors'] = True
    if 'i' in kwargs:
        i = kwargs['i']
        assert len(i) == 3
        if kwargs['unit_vectors']:
            i = np.array(i)/np.linalg.norm(i)
    if 'j' in kwargs:
        j = kwargs['j']
        assert len(j) == 3
        if kwargs['unit_vectors']:
            j = np.array(j)/np.linalg.norm(j)
    if 'k' in kwargs:
        k = kwargs['k']
        assert len(k) == 3
        if kwargs['unit_vectors']:
            k = np.array(k)/np.linalg.norm(k)
    
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
    return (m4(m=mat)@v4(vert).T).T[:, 0:3]

def normal2tfmat(n):
    """
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
    n = np.array(n)
    assert len(n) == 3
    n = n/np.linalg.norm(n)
    nx = n[0]
    ny = n[1]
    nz = n[2]

    # rotate around y first, then x (RxRy)
    d = np.sqrt(1-nx**2)
    RxRy = np.array([\
        [d, 0, nx],\
        [-nx*ny/d, nz/d, ny],\
        [-nx*nz/d, -ny/d, nz]\
        ])
    i_disp_RxRy = np.sqrt(2*(1-np.sqrt(1-nx**2)))
    try:
        tmp = 1/np.sqrt(1-nx**2)
        j_disp_RxRy = np.sqrt(2*(1-nz/tmp))
    except ZeroDivisionError: # if nx approaches 1, then j_disp_RxRy = 0 (by visualization)
        j_disp_RxRy = 0
    disp_RxRy = i_disp_RxRy + j_disp_RxRy

    # rotate around x first, then y (RyRx)
    d = np.sqrt(1-ny**2)
    RyRx = np.array([\
        [nz/d, -nx*ny/d, nx],\
        [0, d, ny],\
        [-nx/d, -nz*ny/d, nz]\
        ])
    try:
        tmp = 1/np.sqrt(1-ny**2)
        i_disp_RyRx = np.sqrt(2*(1-nz/tmp))
    except ZeroDivisionError:
        i_disp_RyRx = 0
    j_disp_RyRx = np.sqrt(2*(1-np.sqrt(1-ny**2)))
    disp_RyRx = i_disp_RyRx + j_disp_RyRx

    # of the two possible transformations, return the one causing the least displacement in i, and j vectors. 
    # Why not explicity comput i and j vectors that give the least amount of displacement?
    # This code favors RxRy (if both produce equal displacements in i and j, then RxRy is picked
    if disp_RxRy <= disp_RyRx:
        return RxRy
    else:
        return RyRx

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
