from bpn_init import *
pn.reload()
env.reset()

class GP:
    def __init__(self, name=None, **kwargs):
        names, kwargs = utils.clean_names(name, kwargs, None, 'gp')
        self.g = new.greasepencil(names['gp_name'])
        self.c = new.collection(names['coll_name'])
        self.o = new.obj(self.g, self.c, names['obj_name'])
        self.mtrl_lib = None # material library for this grease pencil
        
        self.l = self.layer(names['layer_name']) # current layer
        self.kf = 0 # current keyframe
        self.mtrl = None # current material
    
    def layer(self, layer_name):
        """
        Returns a reference to an existing layer.
        Creates a layer if it doesn't exist.
        """
        if layer_name in [l.info for l in self.g.layers]:
            self.l = self.g.layers[layer_name]
        else:
            self.l = self.g.layers.new(layer_name)
        return self.l
    
    def new_color(self, mtrl_name, rgba):
        mtrl = bpy.data.materials.new(mtrl_name)
        bpy.data.materials.create_gpencil_data(mtrl)
        mtrl.grease_pencil.color = rgba
        self.g.materials.append(mtrl)
        return mtrl


def draw_line(gp_frame, p0: tuple, p1: tuple):
    # Init new stroke
    gp_stroke = gp_frame.strokes.new()
    gp_stroke.display_mode = '3DSPACE'  # allows for editing

    # Define stroke geometry
    gp_stroke.points.add(count=2)
    gp_stroke.points[0].co = p0
    gp_stroke.points[1].co = p1
    return gp_stroke


def plot(gp_frame, ptcloud):
    assert type(ptcloud).__name__ == 'PointCloud'
    gp_stroke = gp_frame.strokes.new()
    gp_stroke.display_mode = '3DSPACE'

    gp_stroke.points.add(count=ptcloud.n)
    for i, pt in enumerate(ptcloud.in_world().co):
        gp_stroke.points[i].co = tuple(pt)
    return gp_stroke

def plot_frame(gp_frame, crd_frame):
    assert type(crd_frame).__name__ == 'CoordFrame'
    for i in np.arange(3):
        gp_stroke = gp_frame.strokes.new()
        gp_stroke.display_mode = '3DSPACE'

        gp_stroke.points.add(count=2)
        gp_stroke.points[0].co = tuple(crd_frame.origin)
        gp_stroke.points[1].co = tuple(crd_frame.m[0:3, i])
        gp_stroke.line_width = 80
        gp_stroke.material_index = i
    


θ = np.radians(np.arange(0, 360*2+40, 40))
z1 = np.sin(θ)
y1 = np.cos(θ)
x1 = θ/2

col = new.collection('myColl')
gp = new.greasepencil('myGP')
gpo = new.obj(gp, col, 'myGPobj')

gp_layer = gp.layers.new('Sl1')
gp_frame1 = gp_layer.frames.new(3, active=True)
gp_stroke1 = plot(gp_frame1, PC(np.vstack((x1, y1, z1)).T, trf.normal2tfmat((1, 1, 1))))
# gp_stroke1.line_width = 100

this_frm = Frm(trf.normal2tfmat((1, 1, 1)))
# print([a for a in gp.layers])
# gp_frame2 = gp_layer.frames.new(4)
plot_frame(gp_frame1, this_frm)

def gp_add_color(this_gp, mtrl_name, rgba):
    mtrl = bpy.data.materials.new(mtrl_name)
    bpy.data.materials.create_gpencil_data(mtrl)
    mtrl.grease_pencil.color = rgba
    this_gp.materials.append(mtrl)
    return mtrl

mtrl1 = gp_add_color(gp, 'crd_i', (237/255, 32/255, 76/255, 0.8))
gp_add_color(gp, 'crd_j', (129/255, 231/255, 31/255, 0.8))
gp_add_color(gp, 'crd_k', (14/255, 157/255, 190/255, 0.8))

print(mtrl1.name)
