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
            
        x_plt = pn.scale_data(x, self._xlim, clip=True)*self._width
        y_plt = pn.scale_data(y, self._ylim, clip=True)*self._height
        pc = trf.PointCloud(np.vstack((x_plt, y_plt, np.zeros_like(x_plt))).T, self.frame)
        plot_defaults = {'layer':'plot', 'color':self.current_color, 'keyframe':0, 'pressure':1.0, 'strength':1.0}
        return self.stroke(pc, **{**plot_defaults, **kwargs})

class Space(Pencil):
    """
    Precursor to 3d plotting (figure)

    Space and Space.plot are the equivalent of Pencil and Pencil.stroke, just a bit easier to use in practice for making 2D plots
    """
    def __init__(self, name, type='3D', **kwargs):
        """
        name (str) name of the object
        type (str) ['2D', '3D':default]
        kwargs: 
            height or h (float) height (in m / number of litte squares in blender)
            width or w (float) width (in m / number of litte squares in blender)
            depth or d (flowat) depth (in m / number of little squares in blender)
            xlim (2-tuple of float) x limits
            ylim (2-tuple of float) y limits
            zlim (2-tuple of float) z limits
            ncolors (int) number of colors to cycle through, use this only if the number of colors to cycle through is below the matplotlib default
            color (dict of str : rgba 4-tuple) color of the axes right now - perhaps replace this in the future with show_axes (bool)
            Any other kwargs that a Pencil object would take
        """
        assert type in ('2D', '3D')
        self.type = type
        
        if 'w' in kwargs:
            kwargs['width'] = kwargs.pop('w')
        self._width = kwargs.pop('width', 20.0)
        if 'h' in kwargs:
            kwargs['height'] = kwargs.pop('h')
        self._height = kwargs.pop('height', {'2D':15.0, '3D': 20.0}[self.type])
        
        if self.type == '3D':
            if 'd' in kwargs:
                kwargs['depth'] = kwargs.pop('d')
            self._depth = kwargs.pop('depth', 20.0) 
        else:
            self._depth = 0.0

        self._xlim = kwargs.pop('xlim', None)
        self._ylim = kwargs.pop('ylim', None)
        self._zlim = kwargs.pop('zlim', None)

        self._plot_color_idx = 0
        self._ncolors = kwargs.pop('ncolors', None)
        self._color = kwargs.pop('color', {'black': (0.0, 0.0, 0.0, 1.0)})

        self.plot_data = [] # store data from each plot
        
        super().__init__(name, **{**{'layer_name':'ax'}, **kwargs})
        self.draw()

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
        """Draw a cube. Re-draws strokes every time!"""
        screen_points = trf.PointCloud(self.loc + np.vstack((
            [0, 0, 0],
            [self._width, 0, 0],
            [self._width, self._height, 0],
            [0, self._height, 0],
            [0, 0, 0],
            [np.nan, np.nan, np.nan],
            [0, 0, self._depth],
            [self._width, 0, self._depth],
            [self._width, self._height, self._depth],
            [0, self._height, self._depth],
            [0, 0, self._depth],
            [np.nan, np.nan, np.nan],
            [0, 0, 0],
            [0, 0, self._depth],
            [np.nan, np.nan, np.nan],
            [self._width, 0, 0],
            [self._width, 0, self._depth],
            [np.nan, np.nan, np.nan],
            [self._width, self._height, 0],
            [self._width, self._height, self._depth],
            [np.nan, np.nan, np.nan],
            [0, self._height, 0],
            [0, self._height, self._depth],
        )), self.frame)
        ax_defaults = {'layer': 'ax', 'color':'black', 'keyframe':0, 'pressure':1.5, 'strength':1.0}   
        return super().stroke(screen_points, **{**ax_defaults, **kwargs})

    def plot(self, arg1, arg2=None, arg3=None, **kwargs):
        """
        3D plots - 
            plot(x, y, z)
            plot(arr) # arr is n points x 3 or trf.PointCloud
        2D plots - 
            plot(x, y) # x is n x 1, y is n x 1
            plot(x, y) # x is n x 1, y is n x m (the function will be called multiple times with each n x 1 array)
            plot(d:sampled.Data) # x will be time d.t and y will be d()
            plot(y) # x will be similar to list(range(len(y)))
            plot(list_or_tuple) # this can be a list of tuple of sampled.Data, or numpu arrays, and it will be called recursively
        """
        if self.type == '3D':
            if arg2 is None:
                assert arg3 is None
                if isinstance(arg1, trf.PointCloud): # this function ignores the frame, so make sure the coordinates are in the correct frame before plotting!
                    x, y, z = arg1.x, arg1.y, arg1.z
                else:
                    if not isinstance(arg1, np.ndarray):
                        arg1 = np.array(arg1)
                    assert 3 in tuple(np.shape(arg1))
                    if arg1.shape[0] == 3 and arg1.shape[1] != 3:
                        arg1 = arg1.T
                    x, y, z = arg1[:, 0], arg1[:, 1], arg1[:, 2]
            else:
                x, y, z = np.array(arg1), np.array(arg2), np.array(arg3)
        elif self.type == '2D':
            assert arg3 is None
            if arg2 is None and isinstance(arg1, (list, tuple)): # multiple plots, use recursion to plot
                ret = []
                for arg in arg1:
                    ret.append(self.plot(arg, None, **kwargs))
                return ret
            
            if arg2 is None:
                if isinstance(arg1, sampled.Data): # plot(d:sampled.Data)
                    x = arg1.t
                    y = arg1()
                else: # plot(y)
                    y = arg1
                    x = np.arange(np.shape(y)[0], dtype=float)
            else: # plot(x, y)
                x, y = arg1, arg2
                assert len(x) == np.shape(y)[0]
            if not isinstance(x, np.ndarray):
                x = np.array(x)
            if not isinstance(y, np.ndarray):
                y = np.array(y)
            if y.ndim == 2: # call the plotter recursively when y is multiple timecourses
                assert len(x) == y.shape[0]
                ret = []
                for col_count in range(y.shape[1]):
                    ret.append(self.plot(x, y[:, col_count], **kwargs))
                return ret
            z = np.zeros_like(x)
        
        self._xlim = kwargs.pop('xlim', self._xlim)
        self._ylim = kwargs.pop('ylim', self._ylim)
        self._zlim = kwargs.pop('zlim', self._zlim)
        if self._xlim is None:
            self._xlim = (np.min(x), np.max(x))
        if self._ylim is None:
            self._ylim = (np.min(y), np.max(y))
        
        x_plt = pn.scale_data(x, self._xlim, clip=True)*self._width
        y_plt = pn.scale_data(y, self._ylim, clip=True)*self._height
        if self.type == '2D':
            z_plt = z
        else:
            if self._zlim is None:
                self._zlim = (np.min(z), np.max(z))
            z_plt = pn.scale_data(z, self._zlim, clip=True)*self._depth
        pc = trf.PointCloud(np.vstack((x_plt, y_plt, z_plt)).T, self.frame)
        plot_defaults = {'layer':'plot', 'color':self.current_color, 'keyframe':0, 'pressure':1.0, 'strength':1.0}
        final_kwargs = {**plot_defaults, **kwargs}
        stroke = self.stroke(pc, **final_kwargs)
        if self.type == '2D':
            this_plot_data = PlotData(x, self._xlim, self._width, y, self._ylim, self._height)
        else:
            this_plot_data = PlotData(x, self._xlim, self._width, y, self._ylim, self._height, z, self._zlim, self._depth)
        ret = pn.dotdict({
            'params': final_kwargs,
            'stroke': stroke,
            'data': this_plot_data,
        })
        self.plot_data.append(ret)
        return ret

class PlotData:
    def __init__(self, x, xlim, width, y, ylim, height, z=None, zlim=None, depth=None) -> None:
        self.x, self.y, self.z = x, y, z
        self.xlim, self.ylim, self.zlim = xlim, ylim, zlim
        self.width, self.height, self.depth = width, height, depth
    
    @property
    def x_plt(self):
        return pn.scale_data(self.x, self.xlim, clip=True)*self.width
    
    @property
    def y_plt(self):
        return pn.scale_data(self.y, self.ylim, clip=True)*self.height
    
    @property
    def z_plt(self):
        if self.depth is None:
            return
        return pn.scale_data(self.z, self.zlim, clip=True)*self.depth

    def __call__(self):
        return trf.PointCloud(np.vstack((self.x_plt, self.y_plt, self.z_plt)).T)
    
    @property
    def zero_location(self):
        return (
            pn.scale_data(0, self.xlim, clip=False)*self.width,
            pn.scale_data(0, self.ylim, clip=False)*self.height,
            pn.scale_data(0, self.zlim, clip=False)*self.depth,
        )
    