"""
Turtle module
"""
import inspect
import numpy as np
from numpy.linalg.linalg import inv, norm

import bpy #pylint: disable=import-error
import bmesh #pylint: disable=import-error
import mathutils #pylint: disable=import-error

import pntools as pn

from .core import Msh
from . import new
from .utils import clean_names
from . import trf
from .trf import normal2tfmat

class Draw:
    """
    Turtle-like access to bmesh functions.
    """
    def __init__(self, name=None, **kwargs):
        self.names, _ = clean_names(name, kwargs, {'msh_name':'draw_msh', 'obj_name':'draw_obj', 'priority_obj':'new', 'priority_msh':'new'})
        self.bm = bmesh.new()
        self.all_geom = ()
    
    @property
    def geom_last(self):
        """Returns last created geometry."""
        if not self.all_geom:
            return self.all_geom
        return self.all_geom[-1]

    # Creation functions - set add to self.all_geom and return last 
    # (or call a method that does this job)
    def ngon(self, **kwargs):
        """
        For basic polygon creation. 
        See bpn.new.ngon for input management
        See bpn.vef.ngon for math
        Supercedes a circle because of stupid return type in a circle.
        a = Draw()
        geom = a.ngon(n=6, r=1)
        """
        kwargs_current, kwargs_forward = pn.clean_kwargs(kwargs, {'return_type':'vef', 'fill':False}, {'fill':['fill'], 'return_type':['return_type', 'out']})
        v, e, f = new.ngon(**{**kwargs_current, **kwargs_forward})
        self.addvef(v, e, f)
        return self.geom_last

    # Operations
    def spin(self, geom=None, angle=np.pi, steps=10, axis=(1.0, 0.0, 0.0), cent=(0.0, 1.0, 0.0), use_duplicate=False):
        """spin"""
        if not geom:
            if not self.geom_last:
                geom = self.bm.verts[:] + self.bm.edges[:]
            else:
                geom = self.geom_last.v + self.geom_last.e
        if isinstance(axis, str):
            ax = [0, 0, 0]
            if 'x' in axis:
                ax[0] = 1
            if 'y' in axis:
                ax[1] = 1
            if 'z' in axis:
                ax[2] = 1
            axis = tuple(ax)
        self.all_geom += (Geom(bmesh.ops.spin(
            self.bm,
            geom=geom,
            angle=angle,
            steps=steps,
            axis=axis,
            cent=cent,
            use_duplicate=use_duplicate)['geom_last']),)
        return self.geom_last

    def extrude(self, geom=None):
        """Extrusion by guessing the type of extrusion."""
        if not geom:
            geom = self.geom_last
        if not isinstance(geom, Geom):
            # geom is a list of BMVert, BMEdge and BMFace elements
            assert all([isinstance(ele, (bmesh.types.BMVert, bmesh.types.BMEdge, bmesh.types.BMFace)) for ele in geom])
            geom = Geom(geom)

        # there are only edges present
        if geom.nE == geom.n:
            self.all_geom += (Geom(bmesh.ops.extrude_edge_only(
                self.bm, edges=geom.e)['geom']),)
            return self.geom_last

    def join(self, geom_edges):
        """Joining things. How to auto-detect loops? Add Weld vertices, etc here."""
        out = bmesh.ops.bridge_loops(self.bm, edges=geom_edges)
        self.all_geom += (Geom(out['edges'] + out['faces']),)
        return self.geom_last

    def addvef(self, v, e, f):
        """Add vertices, edges and faces a bmesh!"""
        out = {'verts':[], 'edges':[], 'faces':[]}
        for tv in v:
            vert = self.bm.verts.new(tv)
            vert.index = len(self.bm.verts)-1
            out['verts'].append(vert)
        self.bm.verts.ensure_lookup_table()
        for te in e:
            edge = self.bm.edges.new([self.bm.verts[k] for k in te])
            edge.index = len(self.bm.edges)-1
            out['edges'].append(edge)
        self.bm.edges.ensure_lookup_table()
        for tf in f:
            face = self.bm.faces.new([self.bm.verts[k] for k in tf])
            face.index = len(self.bm.faces)-1
            out['faces'].append(face)
        self.bm.faces.ensure_lookup_table()
        self.all_geom += (Geom(out['verts'] + out['edges'] + out['faces']),)
        return self.geom_last

    def skin(self, pts, **kwargs):
        """
        Apply skin to a path specified by pts.
        :param pts: (2d numpy array of size nPtsx3)
        """
        normals = np.vstack(([0, 0, 1], pts[1, :] - pts[0, :], pts[2:, :] - pts[:-2, :], pts[-1, :] - pts[-2, :]))
        for i in range(np.shape(pts)[0]):
            if i == 0:
                tc = self.ngon(**kwargs)
            else:
                tc = self.extrude(tc.e)
            tfmat = normal2tfmat(normals[i+1, :], 'rxry')
            tfmat_prev = normal2tfmat(normals[i, :], 'rxry')
            for v in tc.v:
                v.co = mathutils.Vector(tfmat@inv(tfmat_prev)@np.array(v.co))
            tc.center = pts[i, :]

    def export(self):
        """
        Exports geometry from each of the sub-steps. 
        """
        return [geom.export() for geom in self.all_geom]

    def __pos__(self):
        """
        Create the object and add it to the scene.
        Returns bpn.core.Msh
        """
        self.__neg__()
        return Msh(msh_name=self.names['msh_name'], obj_name=self.names['obj_name'], coll_name=self.names['coll_name'])

    def __neg__(self):
        """
        Finishes drawing. Returns blender mesh. 
        Doesn't make an object or put it in the scene.
        """
        bpyMsh = bpy.data.meshes.new(self.names['msh_name'])
        self.bm.to_mesh(bpyMsh)
        self.bm.free()
        return bpyMsh

class Geom:
    """Simplifying BMesh geometry object."""
    def __init__(self, geom, tags=''):
        if isinstance(geom, bmesh.types.BMesh):
            self.geom = geom.verts[:]+geom.edges[:]+geom.faces[:]
        else:
            self.geom = geom
        self.call_stack = {k.function:k.filename for i, k in enumerate(inspect.stack()) if i in (1, 2, 3, 4)}
        self.tags = tags

    @property
    def v(self):
        """Vertices"""
        return [ele for ele in self.geom if isinstance(ele, bmesh.types.BMVert)]

    @property
    def e(self):
        """Edges"""
        return [ele for ele in self.geom if isinstance(ele, bmesh.types.BMEdge)]

    @property
    def f(self):
        """Faces"""
        return [ele for ele in self.geom if isinstance(ele, bmesh.types.BMFace)]

    @property
    def n(self):
        """Number of elements in geometry."""
        return len(self.geom)
    
    @property
    def nV(self):
        """Number of vertices in geometry."""
        return len(self.v)

    @property
    def nE(self):
        """Number of edges in geometry."""
        return len(self.e)

    @property
    def nF(self):
        """Number of faces in geometry."""
        return len(self.f)
    
    @property
    def vef(self):
        """Tuple (v, e, f)"""
        return (self.v, self.e, self.f)

    @property
    def all(self):
        """All vetices, edges and faces in one list"""
        return self.v + self.e + self.f

    @property
    def center(self):
        """Center of the geometry."""
        return mathutils.Vector(tuple(np.mean([np.array(tv.co) for tv in self.v], axis=0)))

    @center.setter
    def center(self, new_center):
        self.translate(np.array(new_center)-np.array(self.center))

    def translate(self, delta=0, x=0, y=0, z=0):
        """Translate current vertices by delta."""
        if 'numpy' in str(type(delta)):
            delta = tuple(delta)
        if delta == 0:
            delta = (x, y, z)
        assert len(delta) == 3
        delta = mathutils.Vector(delta)
        for v in self.v:
            v.co += delta

    def scale(self, delta, ref=None):
        """
        Scale current vertices by delta.
        Center for scaling is given by ref.
        If no value is specified, vertices are scaled around the geometry's center.
        """
        if isinstance(delta, (int, float)):
            delta = np.array((1, 1, 1))*float(delta)
        delta = np.array(delta)
        if not ref:
            ref = np.array(self.center)
        else:
            ref = np.array(ref)
        self.translate(0-ref)
        for v in self.v:
            v.co = np.array(v.co)*delta
        self.translate(ref)

    @property
    def v_np(self):
        """
        Numpy-access to vertices. For exporting.
        Returns: 
            idx: index of the vertex within the mesh
            pos: location in 3d
        """
        idx = np.zeros(self.nV, dtype=np.int32)
        pos = np.zeros((self.nV, 3))
        for iv, v in enumerate(self.v):
            idx[iv] = v.index
            pos[iv, :] = v.co
        return {'v_idx': idx, 'v_pos': pos}

    @property
    def e_np(self):
        """
        Numpy-access to edges. For exporting.
        Returns: 
            idx: index of the edge within the mesh
            vert_idx: index of vertices defining that edge
        """
        idx = np.zeros(self.nE, dtype=np.int32)
        vert_idx = np.zeros((self.nE, 2), dtype=np.int32)
        for ie, e in enumerate(self.e):
            idx[ie] = e.index
            for iv, v in enumerate(e.verts):
                vert_idx[ie, iv] = v.index
        return {'e_idx': idx, 'e_verts': vert_idx}
    
    @property
    def f_np(self):
        """
        Numpy-access to faces. For exporting.
        """
        idx = np.zeros(self.nF, dtype=np.int32)
        edge_idx = []
        vert_idx = []
        for fi, f in enumerate(self.f):
            idx[fi] = f.index
            edge_idx.append(np.array([e.index for e in f.edges], dtype=np.int32))
            vert_idx.append(np.array([v.index for v in f.verts], dtype=np.int32))
        return {'f_idx': idx, 'f_edges': np.array(edge_idx), 'f_verts': np.array(vert_idx)}

    def export(self):
        """
        Exports geometry for later manipulation
        """
        return {'tags': self.tags, 'call_stack': self.call_stack, **self.v_np, **self.e_np, **self.f_np}

class SubMsh:
    """
    Parts of a mesh given by vertex, edge and face indices.

    This is the most generic sub-msh. Reference frame is anything set by user.
    Defaults to parent (bpy.objects.msh)'s frame.
    
    Points and frame are not 'attached'. User freely manipulates points and the frame.

    Every sub-mesh should have a frame property.
    """
    def __init__(self, parent, **kwargs):
        """
        :param parent: (bpn.core.Msh)
        :param vi: (1D int32 numpy array) indices of parent vertices
        :param ei: (1D int32 numpy array) indices of parent edges
        :param fi: (1D int32 numpy array) indices of parent faces
        """
        kwargs_def = {'vi': [], 'ei': [], 'fi': [], 'tags': [], 'call_stack': None, 'frame': None}
        kwargs_alias = {'vi': ['vi', 'v_idx'], 'ei': ['ei', 'e_idx'], 'fi': ['fi', 'f_idx'], 'tags': ['tags'], 'call_stack': ['call_stack'], 'frame': ['frame', 'coord_frame', 'm']}
        kwargs_curr, _ = pn.clean_kwargs(kwargs, kwargs_def, kwargs_alias)
        self.parent = parent
        self.vi = kwargs_curr['vi']
        self.ei = kwargs_curr['ei']
        self.fi = kwargs_curr['fi']
        self.tags = kwargs_curr['tags']
        self.call_stack = kwargs_curr['call_stack']

        if not kwargs_curr['frame']:
            self._frame = self.parent.frame
        else:
            if not isinstance(kwargs_curr['frame'], trf.CoordFrame):
                self._frame = trf.CoordFrame(m=kwargs_curr['frame'])
            else:
                self._frame = kwargs_curr['frame']
        
        self._frame = self.frame # run the getter! This might seem trivial for this class, but look at the inherited classes and it should make sense
    
    @property
    def frame(self):
        """Frame of the current sub-mesh."""
        return self._frame
    
    @frame.setter
    def frame(self, new_frame):
        assert isinstance(new_frame, trf.CoordFrame)
        self._frame = new_frame

    @property
    def nV(self):
        """Number of vertices in the sub-mesh"""
        return np.size(self.vi)

    @property
    def pts(self):
        """Vertex positions in the parent mesh's frame of reference."""
        return trf.PointCloud(self.parent.v[self.vi, :], frame=self.parent.frame)
    
    @pts.setter
    def pts(self, ptcloud):
        """Write points back into the parent mesh."""
        assert isinstance(ptcloud, trf.PointCloud)
        assert ptcloud.n == self.nV
        v = self.parent.v
        v[self.vi, :] = ptcloud.in_frame(self.parent.frame).co
        self.parent.v = v

    def transform(self, tfmat):
        """Apply transform in the local reference frame."""
        self.pts = self.pts.in_frame(self.frame.m).transform(tfmat)

    def scale(self, s):
        """Apply scale transform in the local reference frame."""
        self.transform(trf.scaletf(s))

class CenteredSubMsh(SubMsh):
    """
    Sub-mesh whose origin is always at the center of the mesh.

    User can freely set unit vectors without modifying points, and modify points without affecting unit vector directions.
    Default frame is the unit vectors from parent.
    """
    @property
    def origin(self):
        """Origin of the mesh in world coordinates."""
        return self.pts.in_world().center
    
    @property
    def frame(self):
        # ensure i, j, k are unit vectors, and origin is at the center of the points
        return trf.CoordFrame(i=self._frame.i, j=self._frame.j, k=self._frame.k, origin=self.origin.co[0, :])

    @origin.setter
    def origin(self, new_origin):
        # moving the origin for this type of mesh will move the points!
        assert isinstance(new_origin, trf.PointCloud)
        self.pts = self.pts.in_world().transform(np.array(mathutils.Matrix.Translation(new_origin.in_world().co[0, :] - self.origin.co[0, :])))
        self._frame = self.frame
    
    @frame.setter
    def frame(self, new_frame):
        # user can manually change the reference frame. If the origin is different, then the points are going to move!
        assert isinstance(new_frame, trf.CoordFrame)
        # this line moves the points, and explicitly specifies that the new frame was specified in world coordinates.
        self.origin = trf.PointCloud(np.array([new_frame.origin]), trf.CoordFrame())
        # the orientation of the frame is simply taken from new_frame (vectors will be normalized!)
        self._frame = trf.CoordFrame(i=new_frame.i, j=new_frame.j, k=new_frame.k, origin=self.origin.co[0, :])
    

class DirectedSubMsh(SubMsh):
    """
    SubMsh that has a 'direction'
    In general, this would make sense for sub-meshes whose vertices are all in the same plane.
    But, it doesn't have to be!

    This direction is given by 'normal'
    It is a good idea to control the sub-msh using normal. 
    CAUTION: Changing vertex positions manually won't update the normal.

    The internal 3d coordinate system of a directed SubMsh is as follows:
        Normal specifies the 'z' direction
        Projection of the vector from the center of the mesh to the first vertex defines the 'x' direction
        90 degrees on the plane normal to the sub-mesh normal
        Origin is the center of the sub-mesh
    """
    def __init__(self, parent, normal, **kwargs):
        super().__init__(parent, **kwargs)
        # initalization sets _frame, but it needs to be modified without bringing the points along
        if not isinstance(normal, trf.PointCloud):
            normal = trf.PointCloud(normal, self.parent.frame)
        self.change_normal(normal)

    @property
    def origin(self):
        """Origin of the mesh in world coordinates."""
        return self.pts.in_world().center

    @property
    def frame(self):
        # ensure i, j, k are unit vectors, and origin is at the center of the points
        k_vec = self.normal
        pts_in_world = self.pts.in_world()
        x_vec = pts_in_world.co[0, :] - pts_in_world.center.co[0, :]
        j_vec = np.cross(k_vec, x_vec)
        i_vec = np.cross(j_vec, k_vec)
        return trf.CoordFrame(i=i_vec, j=j_vec, k=k_vec, origin=self.origin.co[0, :], unit_vectors=True)

    @property
    def normal(self):
        """By convention, the normal is the unit vector along k."""
        return self._frame.k
    
    @origin.setter
    def origin(self, new_origin):
        # moving the origin for this type of mesh will move the points!
        assert isinstance(new_origin, trf.PointCloud)
        tfmat = np.array(mathutils.Matrix.Translation(new_origin.in_world().co[0, :] - self.origin.co[0, :]))
        new_frame = trf.CoordFrame(tfmat@self.frame.m)
        self.frame = new_frame
 
    @frame.setter
    def frame(self, new_frame):
        # User can manually change the reference frame. Points follow frame.
        assert isinstance(new_frame, trf.CoordFrame)
        new_frame = trf.CoordFrame(new_frame.m) # to ensure new_frame matrix has unit vectors vectors
        # The relative positions of the points don't change because the points are following the frame
        self.pts = trf.PointCloud(self.pts.in_frame(self.frame).co, new_frame)
        self._frame = new_frame
    
    @normal.setter
    def normal(self, new_normal):
        """new_normal is a 'direction' in world coordinates."""
        assert isinstance(new_normal, trf.PointCloud)
        # normal2tfmat takes a unit vector (or normalizes it) and computes a transformation matrix required to transform the point (0, 0, 1) to nhat
        n2tf = trf.m4(normal2tfmat(new_normal.in_frame(self.frame).co[0, :]))
        # the new frame of reference is the transformed coordinate system pushed into the world.
        new_frame = trf.CoordFrame(self.frame.m@n2tf)
        self.frame = new_frame

    def change_normal(self, new_normal):
        """Change the normal WITHOUT moving the points."""
        assert isinstance(new_normal, trf.PointCloud)
        n = new_normal.in_world().co[0, :]
        self._frame.m[0:3, 2] = n/norm(n)
        self._frame = self.frame

    def twist(self, theta_deg=45):
        """Twist transform - clockwise rotation in local space."""
        self.transform(trf.twisttf(np.radians(theta_deg)))
    
#     def scale(self, delta):
#         """Apply scaling along i_hat, j_hat, and k_hat."""
#         self.apply_transform(trf.scaletf(delta))

#     @property
#     def coord_system(self):
#         """Coordinate system of the current object."""
#         crdmat = trf.m4(i=self.i_hat, j=self.j_hat, k=self.k_hat, origin=self.center)
#         return trf.CoordFrame(crdmat, None)

#     def apply_transform(self, tf):
#         """
#         Apply transformation in a coordinate system defined by coord_system. 
#         In none is specified, then apply the transformation in the local coordinate frame.
#         """
#         v = self.v
#         self.v = trf.transform(tf, v, tf_frame_mat=self.coord_system)
