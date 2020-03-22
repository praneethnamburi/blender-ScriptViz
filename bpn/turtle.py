"""
Turtle module
"""
import os
import sys
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
from .utils import clean_names

class Draw:
    """
    Turtle-like access to bmesh functions.
    """
    def __init__(self, name=None, **kwargs):
        self.names, _ = clean_names(name, kwargs, {'msh_name':'draw_msh', 'obj_name':'draw_obj', 'priority_obj':'new', 'priority_msh':'new'})
        self.bm = bmesh.new()
        # self.geom_last = ()
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
