"""
Second Group of classes that are built on top of core module.
They offer advanced customization, and creation of 'meaningful' objects

These classes don't have direct parallels in Blender 
(like the classes in Core except Thing and database creation)

Creating instances of classes in this module will still retrieve a current object, just like core classes.
For example, 
a = mantle.Pencil


Keyword arguments for classes in this module don't directly act on blender data instances (like in the core module)
Consequently, don't pass keyword arguments up the chain.

All classes in this module also require a name for creation.
They are some derivates of the CompoundObject class in core.
"""
import numpy as np

import pntools as pn
from pntools import sampled

from bpn import core, utils, trf

class Pencil(core.GreasePencilObject):
    """
    Create a new grease pencil object with advanced customization.
    """
    def __new__(cls, name, **kwargs): # pylint:disable=arguments-differ
        return super().__new__(cls, name)

    def __init__(self, name, **kwargs):
        names, kwargs00 = utils.clean_names(name, kwargs, {'layer_name':'main', 'priority_gp': 'current', 'priority_obj': 'current'}, mode='gp')
        gp_name = names['gp_name']
        obj_name = names['obj_name']
        coll_name = names['coll_name']
        layer_name = names['layer_name']

        # Create palette in the blender file
        kwargs01, kwargs02 = pn.clean_kwargs(kwargs00, {
            'palette_list': ['MATLAB', 'blender_ax'], 
            'palette_prefix': ['MATLAB_', ''], 
            'palette_alpha': [1, 0.8],
            })
        this_palette = {}
        for pal_name, pal_pre, pal_alpha in zip(kwargs01['palette_list'], kwargs01['palette_prefix'], kwargs01['palette_alpha']):
            this_palette = {**this_palette, **utils.color_palette(pal_name, pal_pre, pal_alpha)} # material library for this grease pencil
        for mtrl_name, rgba in this_palette.items(): # create material library
            utils.new_gp_color(mtrl_name, rgba) # will only create if it doesn't exist

        super().__init__(obj_name, core.GreasePencil(gp_name))
        self.data.layer = layer_name
        # assign colors to this pencil's material slots
        for color in this_palette:
            self.color = color

        custom, _ = pn.clean_kwargs(kwargs02, {'color': 'white', 'keyframe': 1})
        color = custom['color']
        if isinstance(color, int):
            # NOTE: This is confusing, because the color behavior is core.greasepencilobject is different!
            color = 'MATLAB_{:02d}'.format(color)
        self.color = color
        self.keyframe = custom['keyframe']
        self.to_coll(coll_name)


def figure(name=None, **kwargs):
    if name is None:
        name = utils.new_name('figure')
    return Screen(name, **kwargs)

class Screen(Pencil):
    """
    Precursor to 2d plotting (figure)
    By default, it is an XY plot

    Screen and Screen.plot are the equivalent of Pencil and Pencil.stroke, just a bit easier to use in practice for making 2D plots
    """
    def __init__(self, name, **kwargs):
        """
        kwargs: 
            height or h (float) height (in m / number of litte squares) in blender
            width or w (float) width (in m / number of litte squares) in blender
            xlim (2-tuple of float) x limits
            ylim (2-tuple of float) y limits
            ncolors (int) number of colors to cycle through, use this only if the number of colors to cycle through is below the matplotlib default
            color (dict of str : rgba 4-tuple) color of the axes right now - perhaps replace this in the future with show_axes (bool)
            Any other kwargs that a Pencil object would take
        """
        if 'w' in kwargs:
            kwargs['width'] = kwargs.pop('w')
        self._width = kwargs.pop('width', 20.0)
        if 'h' in kwargs:
            kwargs['height'] = kwargs.pop('h')
        self._height = kwargs.pop('height', 15.0)
        self._xlim = kwargs.pop('xlim', None)
        self._ylim = kwargs.pop('ylim', None)
        self._plot_color_idx = 0
        self._ncolors = kwargs.pop('ncolors', None)
        self._color = kwargs.pop('color', {'black': (0.0, 0.0, 0.0, 1.0)})
        super().__init__(name, **{**{'layer_name':'ax'}, **kwargs})
        self.draw()
    
    @property
    def width(self):
        "Screen width"
        return self._width*self.scl[0]
    @width.setter
    def width(self, w):
        s = self.scl
        self.scl = (w/self._width, s[1], s[2])
    
    @property
    def height(self):
        "Screen height"
        return self._height*self.scl[1]
    @height.setter
    def height(self, h):
        s = self.scl
        self.scl = (s[0], h/self._height, s[2])

    @property
    def current_color(self):
        """Increment plot color in the palette, and return the next one."""
        current_color = self._plot_color_idx
        if self._ncolors is None:
            self._plot_color_idx  += 1
        else:
            self._plot_color_idx  = (self._plot_color_idx+1) % self._ncolors
        return current_color

    def draw(self):
        """Primary function to re-draw the plot."""
        # Similar to your update_plots strategy in MATLAB GUIs
        self.draw_axes()

    def draw_axes(self, **kwargs):
        """Draw a rectangular box. Re-draws strokes every time!"""
        screen_points = trf.PointCloud(self.loc + np.vstack((
            [0, 0, 0],
            [self._width, 0, 0],
            [self._width, self._height, 0],
            [0, self._height, 0],
            [0, 0, 0]
        )), self.frame)
        ax_defaults = {'layer': 'ax', 'color':'black', 'keyframe':0, 'pressure':1.5, 'strength':1.0}   
        return super().stroke(screen_points, **{**ax_defaults, **kwargs})

    def plot(self, arg1, arg2=None, **kwargs):
        """(x, y) plot"""
        # Not yet sure if this is a good idea, why not just use the for loop in the calling function?
        if arg2 is None and isinstance(arg1, (list, tuple)):
            ret = []
            for arg in arg1:
                ret.append(self.plot(arg, None, **kwargs))
            return ret
        
        if arg2 is None:
            if isinstance(arg1, sampled.Data):
                x = arg1.t
                y = arg1()
            else:
                y = arg1
                x = np.arange(np.shape(y)[0], dtype=float)
        else:
            x, y = arg1, arg2
            assert len(x) == np.shape(y)[0]
        if not isinstance(x, np.ndarray):
            x = np.array(x)
        if not isinstance(y, np.ndarray):
            y = np.array(y)
        self._xlim = kwargs.pop('xlim', self._xlim)
        self._ylim = kwargs.pop('ylim', self._ylim)
        if self._xlim is None:
            self._xlim = (np.min(x), np.max(x))
        if self._ylim is None:
            self._ylim = (np.min(y), np.max(y))

        if y.ndim == 2: # call the plotter recursively when y is multiple timecourses
            assert len(x) == y.shape[0]
            ret = []
            for col_count in range(y.shape[1]):
                ret.append(self.plot(x, y[:, col_count], **kwargs))
            return ret
        
        def _norm_inp(d, d_lim): # scale the input between 0 and 1
            do = d_lim[0]
            dw = d_lim[1] - d_lim[0]
            d[d < d_lim[0]] = np.nan
            d[d > d_lim[1]] = np.nan
            return (d - do)/dw
            
        x_plt = _norm_inp(x, self._xlim)*self._width
        y_plt = _norm_inp(y, self._ylim)*self._height
        pc = trf.PointCloud(np.vstack((x_plt, y_plt, np.zeros_like(x_plt))).T, self.frame)
        plot_defaults = {'layer':'plot', 'color':self.current_color, 'keyframe':0, 'pressure':1.0, 'strength':1.0}
        return super().stroke(pc, **{**plot_defaults, **kwargs})
