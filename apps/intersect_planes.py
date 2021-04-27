from bpn_init import *

def demofunc(pl_z=-0.5):
    obj = new.sphere("sph", r=0.55)
    pl = new.plane("Plane")
    pl.loc = [0, 0, pl_z]
    c = get_circumference(obj, pl)
    return c


class Rachel:
    def __init__(self, b):
        self.pl = new.plane("Plane")
        self.b = b
        self.bcopy = b.deepcopy("CopyObj")
        self.mod = self.bcopy.get_modifier('boolean')
        self.mod.operation = 'INTERSECT'
        self.mod.object = self.pl()

    def z(self, z_val):
        self.pl.loc = [0, 0, z_val]

    @property
    def c(self):
        depsgraph = bpy.context.evaluated_depsgraph_get()
        bcopy_eval = self.bcopy().evaluated_get(depsgraph).to_mesh()
        edge_lengths = []
        face_centers = []
        for face in bcopy_eval.polygons:
            this_eL = 0
            for edge in face.edge_keys:
                this_eL += (bcopy_eval.vertices[edge[0]].co - bcopy_eval.vertices[edge[1]].co).length
            edge_lengths.append(this_eL)

            this_center = Vector()
            for v_idx in face.vertices:
                this_center += bcopy_eval.vertices[v_idx].co
            face_centers.append(this_center/len(face.vertices))
        return edge_lengths, face_centers

    def refresh(self):
        -self.bcopy.data
        -self.bcopy
        self.bcopy = self.b.deepcopy("CopyObj")
        


def get_circumference(obj, pl, clean=False):
    """
    obj is the object of interest
    pl is the intersecting plane
    """
    pmw = pl().matrix_world
    face = pl().data.polygons[0]
    plane_co = pmw @ face.center
    plane_no = pmw @ (face.center + face.normal) - plane_co
    bm = bmesh.new()
    bm.from_mesh(obj().data)
    bmesh.ops.bisect_plane(bm,
                geom=bm.faces[:] + bm.edges[:] + bm.verts[:],
                clear_inner=True,
                clear_outer=True,
                plane_co=plane_co,
                plane_no=plane_no,
                )
    me = bpy.data.meshes.new("Bisect")
    bm.to_mesh(me)
    bis = utils.enhance(bpy.data.objects.new("Bisect", me))
    bis.to_coll("Collection")
    bm.free()
    ret = sum(bis.eL)
    if clean:
        -bis
    return ret 
