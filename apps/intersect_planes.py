from bpn_init import *

def demofunc(pl_z=-0.5):
    obj = new.sphere("sph", r=0.55)
    pl = new.plane("Plane")
    pl.loc = [0, 0, pl_z]
    c = get_circumference(obj, pl)
    return c

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
