from bpn_init import *
pn.reload()
env.reset()

class GP:
    """
    Does a fine job creating a new grease pencil custom object.
    What if I want to make one from an existing grease pencil object?
    """
    def __init__(self, name=None, **kwargs):
        names, kwargs = utils.clean_names(name, kwargs, {'priority_gp':'new'}, 'gp')
        self.g = new.greasepencil(names['gp_name'])
        self.c = new.collection(names['coll_name'])
        self.o = new.obj(self.g, self.c, names['obj_name'])
        
        kwargs, _ = pn.clean_kwargs(kwargs, {
            'palette_list': ['MATLAB', 'blender_ax'], 
            'palette_prefix': ['MATLAB_', ''], 
            'palette_alpha': [1, 0.8],
            })
        this_palette = {}
        for pal_name, pal_pre, pal_alpha in zip(kwargs['palette_list'], kwargs['palette_prefix'], kwargs['palette_alpha']):
            this_palette = {**this_palette, **utils.color_palette(pal_name, pal_pre, pal_alpha)} # material library for this grease pencil
        for mtrl_name, rgba in this_palette.items(): # create material library
            self.new_color(mtrl_name, rgba)

        self._layer = None
        self._keyframe = None # current keyframe
        self.layer = names['layer_name'] # current layer (also makes a default keyframe at 0!)
        
        self._color = None # name of the current material
        self.color = 0 # initalize to the first one
    
    @property
    def color_index(self):
        """Index of the current color."""
        return {m.name : i for i, m in enumerate(self.o.material_slots)}[self._color]

    @property
    def color(self):
        """Return the name of the current color."""
        return self._color

    @color.setter
    def color(self, this_color):
        """
        Set the current stroke material (self._color).
        this_color is either a string, a number, a dict, or a tuple.
        string - material name
        number - material index
        tuple - 4-element tuple : select the closest color
        dict - create new material
            one key, value pair {name: 4-tuple rgba}
            if material with that name exists, create a new name
        """
        if isinstance(this_color, int):
            assert this_color < len(self.o.material_slots)
            color_name = {i : m.name for i, m in enumerate(self.o.material_slots)}[this_color]
        if isinstance(this_color, dict):
            assert len(this_color) == 1 # supply only one color at a time?'
            key = list(this_color.keys())[0] # key is the name
            val = list(this_color.values())[0]
            # pick a new name if a material with current name exists
            this_color[utils.new_name(key, [m.name for m in bpy.data.materials])] = this_color.pop(key)
            assert len(val) == 4
            for v in val:
                assert 0.0 <= v <= 1.0
            self.new_color(key, val)
            color_name = key # convert it into a number 
        if isinstance(this_color, str):
            assert this_color in [m.name for m in self.o.material_slots]
            color_name = this_color

        self._color = color_name

    @property
    def layer(self):
        """Returns the current layer."""
        return self._layer
    
    @layer.setter
    def layer(self, layer_name):
        """
        Returns a reference to an existing layer.
        Creates a layer if it doesn't exist.
        """
        if layer_name in [l.info for l in self.g.layers]:
            self._layer = self.g.layers[layer_name]
        else:
            self._layer = self.g.layers.new(layer_name)
            self.keyframe = 0 # make a default keyframe at 0 with every new layer

    @property
    def keyframe(self):
        """Returns the current keyframe."""
        return self._keyframe
    
    @keyframe.setter
    def keyframe(self, keynum):
        """
        Returns reference to the keyframe given by keynum for the
        current layer.
        Inserts a keyframe in the current layer if there isn't one.
        """
        assert isinstance(keynum, int)
        if keynum not in [kf.frame_number for kf in self.layer.frames]:
            self._layer.frames.new(keynum)
        self._keyframe = [kf for kf in self.layer.frames if kf.frame_number == keynum][0]

    def new_color(self, mtrl_name, rgba):
        """
        Add a new color to the current object's material slot.
        Create the material if it doesn't exist.
        Update the rgba if material with mtrl_name already exists.
        Add it to the material slot of the current object.
        Returns:
            Material object (bpy.data.materials)
        """
        if mtrl_name in [m.name for m in bpy.data.materials]:
            mtrl = bpy.data.materials[mtrl_name]
        else:
            mtrl = bpy.data.materials.new(mtrl_name)
        bpy.data.materials.create_gpencil_data(mtrl)
        mtrl.grease_pencil.color = rgba
        if mtrl_name not in [m.name for m in self.g.materials if m is not None]:
            self.g.materials.append(mtrl)
        return mtrl
    
    def stroke(self, ptcloud, color=None, layer=None, keyframe=None, line_width=40):
        """
        Make a new stroke 
            1) in the current layer, 
            2) at the current keyframe,
            3) in the current color.
        Allow settings for color, layer, keyframe 
        (which change the current settings)
        Add pressure and strength arrays
        """
        if layer is not None:
            self.layer = layer
        if color is not None:
            self.color = color
        if keyframe is not None:
            self.keyframe = keyframe
        assert type(ptcloud).__name__ == 'PointCloud'
        gp_stroke = self.keyframe.strokes.new()
        gp_stroke.display_mode = '3DSPACE'

        gp_stroke.points.add(count=ptcloud.n)
        gp_stroke.points.foreach_set('co', tuple(ptcloud.in_world().co.flatten())) # more efficient
        # for i, pt in enumerate(ptcloud.in_world().co):
        #     gp_stroke.points[i].co = tuple(pt)
        gp_stroke.material_index = self.color_index
        gp_stroke.line_width = line_width
        return gp_stroke


gp = GP(gp_name='myGP', obj_name='myGPobj', coll_name='myColl', layer_name='sl1')

θ = np.radians(np.arange(0, 360*2+1, 1))
z1 = np.sin(θ)
y1 = np.cos(θ)
x1 = θ/2

gp.stroke(PC(np.vstack((x1, y1, z1)).T, trf.normal2tfmat((1, 1, 1))), color=2, layer='sl1', keyframe=0)
gp.stroke(PC(np.vstack((x1, y1, z1)).T, trf.normal2tfmat((0, 0, 1))), color=1, layer='sl3', keyframe=10)
gp.stroke(PC(np.vstack((x1, y1, z1)).T, trf.normal2tfmat((1, 1, 1))), color=2, layer='sl1', keyframe=20, line_width=100)
gp.keyframe = 30

# bpy.data.grease_pencils[0].layers['sl1'].frames[1].clear() # removes the stroke, but there is still a keyframe
# bpy.data.grease_pencils[0].layers['sl1'].clear() # removes all keyframes and strokes

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
        print(dir(gp_stroke))


# θ = np.radians(np.arange(0, 360*2+40, 40))
# z1 = np.sin(θ)
# y1 = np.cos(θ)
# x1 = θ/2

# col = new.collection('myColl')
# gp = new.greasepencil('myGP')
# gpo = new.obj(gp, col, 'myGPobj')

# gp_layer = gp.layers.new('Sl1')
# gp_frame1 = gp_layer.frames.new(3, active=True)
# gp_stroke1 = plot(gp_frame1, PC(np.vstack((x1, y1, z1)).T, trf.normal2tfmat((1, 1, 1))))
# # gp_stroke1.line_width = 100

# this_frm = Frm(trf.normal2tfmat((1, 1, 1)))
# plot_frame(gp_frame1, this_frm)
