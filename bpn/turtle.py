"""
Turtle module
"""
import os
import sys
from functools import partial
import numpy as np

import bpy #pylint: disable=import-error
import bmesh #pylint: disable=import-error

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

import bpn
import pntools as pn

from .utils import clean_names

class Draw:
    """
    Turtle-like access to bmesh functions.
    """
    def __init__(self, name=None, msh_name='autoMshName', obj_name='autoObjName', coll_name='Collection', priority='new', priority_msh='new'):
        _, self.msh_name, self.obj_name, self.coll_name = clean_names(Draw.__init__, name, msh_name, obj_name, coll_name, priority, priority_msh)
        self.bm = bmesh.new()
        self.geom_last = ()
    
    # Creation functions - set self.geom_last and return it
    def circle(self, **kwargs):
        """
        a = Draw()
        geom = a.circle(n=6, r=1)
        """
        kwargs_def = {'segments':8, 'radius':1}
        kwargs_alias = {'segments':['segments', 'seg', 'u', 'n'], 'radius':['radius', 'r']}
        kwargs, _ = pn.clean_kwargs(kwargs, kwargs_def, kwargs_alias)
        kwargs['cap_ends'] = False
        kwargs['cap_tris'] = False

        bmesh.ops.create_circle(self.bm, **kwargs)

        self.geom_last = Geom(self.bm)
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
        self.geom_last = Geom(bmesh.ops.spin(
            self.bm,
            geom=geom,
            angle=angle,
            steps=steps,
            axis=axis,
            cent=cent,
            use_duplicate=use_duplicate)['geom_last'])
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
            self.geom_last = Geom(bmesh.ops.extrude_edge_only(
                self.bm, edges=geom.e)['geom'])
            return self.geom_last

    def join(self, geom_edges):
        """Joining things. How to auto-detect loops? Add Weld vertices, etc here."""
        out = bmesh.ops.bridge_loops(self.bm, edges=geom_edges)
        self.geom_last = Geom(out['edges'] + out['faces'])
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
        self.geom_last = Geom(out['verts'] + out['edges'] + out['faces'])
        return self.geom_last

    def __pos__(self):
        """
        Create the object and add it to the scene.
        Returns bpn.Msh
        """
        self.__neg__()
        return bpn.Msh(msh_name=self.msh_name, obj_name=self.obj_name, coll_name=self.coll_name)

    def __neg__(self):
        """
        Finishes drawing. Returns blender mesh. 
        Doesn't make an object or put it in the scene.
        """
        bpyMsh = bpy.data.meshes.new(self.msh_name)
        self.bm.to_mesh(bpyMsh)
        self.bm.free()
        return bpyMsh

class Geom:
    """Simplifying BMesh geometry object."""
    def __init__(self, geom):
        if isinstance(geom, bmesh.types.BMesh):
            self.geom = geom.verts[:]+geom.edges[:]+geom.faces[:]
        else:
            self.geom = geom
    
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
