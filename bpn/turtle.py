"""
Turtle module
"""
import os
import sys
import inspect
from copy import deepcopy
import numpy as np

import bpy #pylint: disable=import-error
import bmesh #pylint: disable=import-error
import mathutils #pylint: disable=import-error

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

import bpn
import pntools as pn

from . import new
from . import utils
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
        normals = np.vstack((pts[1, :] - pts[0, :], pts[2:, :] - pts[:-2, :], pts[-1, :] - pts[-2, :]))
        for i in range(np.shape(pts)[0]):
            if i == 0:
                tc = self.ngon(**kwargs)
                vertpos_orig = []
                for v in tc.v:
                    vertpos_orig.append(deepcopy(v.co))
            else:
                tc = self.extrude(tc.e)
            tfmat = normal2tfmat(normals[i, :])
            for v, v_orig in zip(tc.v, vertpos_orig):
                v.co = mathutils.Vector(tfmat@np.array(v_orig))
            tc.center = pts[i, :]

    def export(self):
        """
        Exports geometry from each of the sub-steps. 
        """
        return [geom.export() for geom in self.all_geom]

    def __pos__(self):
        """
        Create the object and add it to the scene.
        Returns bpn.Msh
        """
        self.__neg__()
        return bpn.Msh(msh_name=self.names['msh_name'], obj_name=self.names['obj_name'], coll_name=self.names['coll_name'])

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
    """Parts of a mesh given by vertex, edge and face indices"""
    def __init__(self, parent, **kwargs):
        """
        :param parent: (bpn.Msh)
        :param vi: (1D int32 numpy array) indices of parent vertices
        :param ei: (1D int32 numpy array) indices of parent edges
        :param fi: (1D int32 numpy array) indices of parent faces
        """
        kwargs_def = {'vi': [], 'ei': [], 'fi': [], 'tags': [], 'call_stack': None}
        kwargs_alias = {'vi': ['vi', 'v_idx'], 'ei': ['ei', 'e_idx'], 'fi': ['fi', 'f_idx'], 'tags': ['tags'], 'call_stack': ['call_stack']}
        kwargs_curr, _ = pn.clean_kwargs(kwargs, kwargs_def, kwargs_alias)
        self.parent = parent
        self.vi = kwargs_curr['vi']
        self.ei = kwargs_curr['ei']
        self.fi = kwargs_curr['fi']
        self.tags = kwargs_curr['tags']
        self.call_stack = kwargs_curr['call_stack']

    @property
    def v(self):
        """Vertex positions of the sub mesh"""
        return self.parent.v[self.vi, :]
    
    @v.setter
    def v(self, this_coords):
        """Update the parent vertices."""
        v = self.parent.v
        v[self.vi, :] = this_coords
        self.parent.v = v

    @property
    def center(self):
        """Center of all the vertices"""
        return np.mean(self.v, axis=0)

    @center.setter
    def center(self, new_center):
        new_center = np.array(new_center)
        self.v = self.v + new_center - self.center

    # Transformations inside an object are meaningless unless the object explicity has it's own coordinate system
    # This object's coordinate system is defined by the world coordinate system! If not, then the vertex coordinates returned should be relative to the 'center'
    def translate(self, delta=0, x=0, y=0, z=0):
        """Translate current vertices by delta."""
        if 'numpy' in str(type(delta)):
            delta = tuple(delta)
        if delta == 0:
            delta = (x, y, z)
        assert len(delta) == 3
        delta = np.array(delta)
        self.v += delta

    # def scale(self, delta, ref=None):
    #     """
    #     Scale current vertices by delta.
    #     Center for scaling is given by ref.
    #     If no value is specified, vertices are scaled around the geometry's center.
    #     """
    #     if isinstance(delta, (int, float)):
    #         delta = np.array((1, 1, 1))*float(delta)
    #     delta = np.array(delta)
    #     if not ref:
    #         ref = np.array(self.center)
    #     else:
    #         ref = np.array(ref)
    #     self.translate(0-ref)
    #     self.v = self.v*delta
    #     self.translate(ref)

class DirectedSubMsh(SubMsh):
    """
    SubMsh that has a 'direction'
    In general, this would make sense for sub-meshes whose vertices are all in the same plane.
    But, it doesn't have to be! With great power comes great responsibility.

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
        self._normal = normal
        super().__init__(parent, **kwargs)

    @property
    def normal(self):
        """Ensure a unit vector is returned."""
        n = np.array(self._normal)
        return n/np.linalg.norm(n)

    @normal.setter
    def normal(self, new_normal):
        new_normal = np.array(new_normal)
        assert len(new_normal) == 3

        curr_center = self.center
        m1 = normal2tfmat(self.normal)
        m2 = normal2tfmat(new_normal)
        crd = (self.v - curr_center).T
        new_crd = m2@np.linalg.inv(m1)@crd
        self.v = new_crd.T + curr_center
        self._normal = new_normal
    
    k_hat = normal

    @property
    def j_hat(self):
        """Y unit vector in local coordinate space."""
        x = self.v[0, :] - self.center
        y = np.cross(self.normal, x)
        return y/np.linalg.norm(y)
    
    @property
    def i_hat(self):
        """X unit vector in local coordinate space."""
        return np.cross(self.j_hat, self.normal)

    def twist(self, theta_deg=45):
        """Twist transform - clockwise rotation in local space."""
        self.apply_transform(trf.twisttf(np.radians(theta_deg)))
    
    def scale(self, delta):
        """Apply scaling along i_hat, j_hat, and k_hat."""
        self.apply_transform(trf.scaletf(delta))

    @property
    def coord_system(self):
        """Coordinate system of the current object."""
        return trf.CoordFrame(i=self.i_hat, j=self.j_hat, k=self.k_hat, origin=self.center)

    def apply_transform(self, tf, coord_system=np.array([None])):
        """
        Apply transformation in a coordinate system defined by coord_system. 
        In none is specified, then apply the transformation in the local coordinate frame.
        """
        if not all(coord_system):
            coord_system = self.coord_system
        assert isinstance(coord_system, trf.CoordFrame)
        v = self.v
        self.v = coord_system.apply_transform(v, tf)
