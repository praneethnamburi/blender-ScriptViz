"""
Work with optitrack files in python. This module can be used without blender.
"""
import os
import csv
import numpy as np
from decord import VideoReader

from bpn import trf
import pntools as pn

# for drawing - requires blender modules
from bpn import new, env, utils
from bpn.mantle import Pencil
from bpn.utils import get

class Log:
    """
    Read Optitrack log files (CSV export)
    Example:
        fname = r"P:\data\20210311 - Coach Todd Baseball pitch\Pitching_01_02_Fill500Frm.csv"
        bp = ot.Log(fname)
    """
    def __init__(self, fname, coord_frame=trf.CoordFrame(i=(-1, 0, 0), j=(0, 0, 1), k=(0, 1, 0))):
        self.fname = fname
        self.disp_scale = 100.

        data = []
        data_len = []
        with open(self.fname, newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                data.append(row)
                data_len.append(len(row))

        hdr = dict(zip(data[0][0::2], data[0][1::2]))
        for key in hdr:
            if 'Frame Rate' in key:
                hdr[key] = float(hdr[key])
            if 'Total' in key:
                hdr[key] = int(hdr[key])
        self.hdr = hdr

        frame_num_col = 0
        time_col = 1
        pos_col_start = 2

        frame_hdr_row = 0
        while True:
            if data_len[frame_hdr_row] > 0:
                if data[frame_hdr_row][frame_num_col] == "Frame":
                    break
            frame_hdr_row += 1

        marker_name_row = 0
        while True:
            if data_len[marker_name_row] > 0:
                if data[marker_name_row][time_col] == "Name":
                    break
            marker_name_row += 1

        marker_names = np.unique(data[marker_name_row][pos_col_start:])
        marker_names_valid = [m.replace(':', '_') for m in marker_names]
        marker_name_row_valid = [m.replace(':', '_') for m in data[marker_name_row]]

        data_start_row = frame_hdr_row + 1

        n_data_rows = len(data)-data_start_row
        n_data_cols = len(data[data_start_row])

        data3d = np.array(data[data_start_row:])
        data3d[data3d==''] = 'nan'
        data3d = data3d.astype(float)

        self.pos = {}
        for marker_name in marker_names_valid:
            this_cols, = np.where(np.array(marker_name_row_valid) == marker_name) # assuming X, Y, Z sequence during export
            self.pos[marker_name] = Marker(marker_name, data3d[:, this_cols]/self.disp_scale, coord_frame, self).in_world()

        self._vid_frame = data3d[:, frame_num_col].astype(int)
        self._t = data3d[:, time_col]

    @property
    def t(self):
        return self._t

    @property
    def vid_frame(self):
        return self._vid_frame

    @property
    def n(self):
        return len(self.vid_frame)

    @property
    def marker_names(self):
        return list(self.pos.keys())
    
    @property
    def sr(self):
        """sampling rate"""
        return self.hdr['Export Frame Rate']

    @property
    def units(self):
        return str(self.disp_scale) + " " + self.hdr['Length Units']
    
    def load_videos(self):
        vids = pn.find("*Camera*.mp4", os.path.dirname(self.fname))
        if not vids:
            vids = pn.find("*Camera*.avi", os.path.dirname(self.fname))
        return [Vid(vid_name) for vid_name in vids]
    # elements for animation:
    # markers, connections, clips, chains (to measure length)

@pn.PortProperties(Log, 'parent')
class Marker(trf.PointCloud):
    def __init__(self, name, vert, frame, parent):
        """
        name   (str) - name of the marker
        vert   (n x 3 numpy array)
        frame  (4x4 frame, OR, trf.CoordFrame)
        parent (ot.Log) - Log file object
        """
        assert type(parent).__name__ == "Log"
        self.name = name
        super().__init__(vert, frame)
        self.parent = parent

        self.in_frame = self._pointcloud_to_marker(self.in_frame)
        self.in_world = self._pointcloud_to_marker(self.in_world)
        self.transform = self._pointcloud_to_marker(self.transform)
        self.reframe = self._pointcloud_to_marker(self.reframe)

        ## To automate this
        # {attr for attr_name, attr in trf.PointCloud.__dict__.items() if attr_name[0] != '_' and (not isinstance(attr, property)) and inspect.signature(attr).return_annotation == 'PointCloud'}
    @staticmethod
    def _pointcloud_to_marker(meth):
        def modifiedMethod(*args, **kwargs):
            pc = meth(*args, **kwargs)
            s = meth.__self__
            return Marker(s.name, pc.co, pc.frame, s.parent)
        return modifiedMethod

    def __getitem__(self, key):
        """Use an interval object to slice the marker"""
        assert type(key).__name__ == 'Interval'
        if key.sr != self.sr:
            key.sr = self.sr
        return Marker(self.name, self.co[key.start.sample:key.end.sample], self.frame, self.parent)

    def show_path(self):
        new.mesh(name=self.name, x=self.co[:,0], y=self.co[:,1], z=self.co[:,2])

    def show(self, intvl=(0., 2.), start_frame=1, r=0.2):
        if isinstance(intvl, (list, tuple)):
            assert len(intvl) == 2
            intvl  = Interval(intvl[0], intvl[1], sr=self[0].sr)
        assert isinstance(intvl, Interval)

        intvl.iter_rate = env.Key().fps
        ts_name = self.name + '_pos'
        if not get(ts_name):
            ts = new.sphere(name=ts_name, r=r)
            ts.shade("smooth")
        else:
            ts = get(ts_name)

        for center_frame, _, index in intvl:
            ts.loc = self.co[center_frame]
            ts.key(start_frame + index, 'l')

    def show_trajectory(self, intvl, keyframe=1, color=None, layer_name="main"):
        """Plot trajectory for a given time interval"""
        p = Pencil(self.name)
        if color is None:
            color = 'MATLAB_00'
        if isinstance(color, int):
            color = 'MATLAB_{:02d}'.format(color)
        if isinstance(color, str):
            pal = 'MATLAB'
            if 'crd' in color:
                pal = 'blender_ax'

        p.color = {color: utils.color_palette(pal)[color]}
        p.keyframe = keyframe

        p.stroke(self[intvl].in_world())


class Time:
    """
    Time when working with sampled data (including video). INTEGER IMPLIES SAMPLE NUMBER, FLOAT IMPLIES TIME.
    Use this to encapsulate sampling rate (sr), sample number (sample), and time (s).
    When the sampling rate is changed, the sample number is updated, but the time is held constant.
    When the time is changed, sample number is updated.
    When the sample number is changed, the time is updated
    When working in Premiere Pro, use 29.97 fps drop-frame timecode to show the actual time in video.
    You should see semicolons instead of colons
        inp hh;mm;ss;frame
            (str)   '00;09;53;29'
            (list)  [00, 09, 53, 29]
            (float) assumes provided input is a timestamp
            (int)   assumes the provided input is the sample number

        t = Time(12531, 180)
        t.s
        t.sample
    """
    def __init__(self, inp, sr=30.):
        assert isinstance(inp, (str, list, float, int))
        self._sr = float(sr)

        if isinstance(inp, str):
            inp = [int(x) for x in inp.split(';')]
        if isinstance(inp, list):
            assert len(inp) == 4
            self._sample = int((inp[0]*60*60 + inp[1]*60 + inp[2])*self.sr + inp[3])
        if isinstance(inp, float): # time to sample
            self._sample = int(inp*self.sr)
        if isinstance(inp, int):
            self._sample = inp
        self._s = float(self._sample)/self._sr

    @property
    def sr(self):
        return self._sr

    @sr.setter
    def sr(self, sr_val):
        """When changing the sampling rate, time is kept the same, and the sample number is NOT"""
        sr_val = float(sr_val)
        self._sr = sr_val
        self._sample = int(self._s*self._sr)

    @property
    def sample(self):
        return self._sample
    
    @sample.setter
    def sample(self, sample_val):
        self._sample = int(sample_val)
        self._s  = float(self._sample)/self._sr
    
    @property
    def s(self):
        """Return time in seconds"""
        return self._s

    @s.setter
    def s(self, s_val):
        """If time is changed, then the sample number should be reset as well"""
        self._s = float(s_val)
        self._sample = int(self._s*self._sr)

    def __add__(self, other):
        x = self._arithmetic(other)
        return Time(x[2].__add__(x[0], x[1]), self.sr)

    def __sub__(self, other):
        x = self._arithmetic(other)
        return Time(x[2].__sub__(x[0], x[1]), self.sr)

    def _arithmetic(self, other):
        if isinstance(other, self.__class__):
            assert other.sr == self.sr
            return (self.sample, other.sample, int)
        elif isinstance(other, int):
            # integer implies sample, float implies time
            return (self.sample, other, int)
        elif isinstance(other, float):
            return (self.s, other, float)
        else:
            os.error("Unexpected input type! Input either a float for time, integer for sample, or time object")


class Interval:
    """
    Interval object with start and stop times. Implements the iterator protocol.
    Pictoral understanding:
    start           -> |                                           | <-
    frames          -> |   |   |   |   |   |   |   |   |   |   |   | <- [self.sr, len(self)=12, self.t_data, self.t]
    animation times -> |        |        |        |        |         <- [self.iter_rate, self._index, self.t_iter]
    Frame sampling is used to pick the nearest frame corresponding to the animation times
    Example:
        intvl = ot.Interval(('00;09;51;03', 30), ('00;09;54;11', 30), sr=180, iter_rate=env.Key().fps)
        intvl.iter_rate = 24 # say 24 fps for animation
        for nearest_sample, time, index in intvl:
            print((nearest_sample, time, index))
    """
    def __init__(self, start, end, zero=None, sr=None, iter_rate=None):
        self.start = self._process_inp(start)
        self.end = self._process_inp(end)
        if sr is not None:
            self.sr = sr
        assert self.start.sr == self.end.sr # interval is defined for a specific sampled dataset
        if zero is None:
            self.zero = self.start
        else:
            self.zero = self._process_inp(zero)
        self._index = 0
        if iter_rate is None:
            self.iter_rate = self.sr # this will be the animation fps when animating data at a different rate
        else:
            self.iter_rate = float(iter_rate)

    @staticmethod
    def _process_inp(inp):
        if type(inp).__name__ == 'Time':
            return inp
        elif isinstance(inp, (tuple, list)):
            assert len(inp) == 2
            return Time(inp[0], inp[1])
        return Time(inp) # string, float and int get processed here

    @property
    def sr(self):
        return self.start.sr
    
    @sr.setter
    def sr(self, sr_val):
        sr_val = float(sr_val)
        self.start.sr = sr_val
        self.end.sr = sr_val
        
    @property
    def dur_s(self):
        """Duration in seconds"""
        return self.end.s - self.start.s
    
    @property
    def dur_sample(self):
        """Duration in number of samples"""
        return self.end.sample - self.start.sample + 1 # includes both start and end samples
    
    def __len__(self):
        return self.dur_sample

    # iterator protocol - you can do: for sample, time, index in interval
    def __iter__(self):
        """Iterate from start sample to end sample"""
        return self
    
    def __next__(self):
        index_interval = 1./self.iter_rate
        if self._index <= int(self.dur_s*self.iter_rate)+1:
            time = self.start.s + self._index*index_interval
            nearest_sample = self.start.sample + int(self._index*index_interval*self.sr)
            result = (nearest_sample, time, self._index)
        else:
            self._index = 0
            raise StopIteration
        self._index += 1
        return result
    
    # time vectors
    @property
    def t_iter(self):
        """Time Vector for the interval at iteration frame rate"""
        return self._t(self.iter_rate)

    @property
    def t_data(self):
        """Time vector at the data sampling rate"""
        return self._t(self.sr)

    @property
    def t(self):
        """Time Vector relative to t_zero"""
        tzero = self.zero.s
        return [t - tzero for t in self.t_data]
        
    def _t(self, rate):
        _t = [self.start.s]
        while _t[-1] <= self.end.s:
            _t.append(_t[-1] + 1./rate)
        return _t


class Chain:
    """
    Collection of markers. Sequence matters.
    Example:
        bp = ot.Log(fname)
        c = ot.Chain('Spine', [bp.pos['Spine_' + x] for x in 'L4 T11 T4 C3'.split(' ')])
        c.show(start_time=9.*60+51.25, end_time=9*60.+54+11/30)
    """
    def __init__(self, name, marker_list):
        for m in marker_list:
            assert type(m).__name__ == 'Marker'
        self._marker_list = marker_list
        self.name = name

    @property
    def markers(self):
        return [m.name for m in self._marker_list]

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._marker_list[key]
        return [m for m in self._marker_list if m.name == key][0]
    
    def get(self, sample_index):
        return trf.PointCloud( np.array( [m.co[sample_index] for m in self._marker_list] ) )
    
    def show(self, intvl=(0., 2.), start_frame=1, layer_name="main"):
        """
        intvl (Interval, tuple) - Interval object, or a tuple of (float, float) implying start and end time, 
            or a tuple of (int, int) implying start and end frame
        start_frame (int) - animation start frame
        """
        if isinstance(intvl, (list, tuple)):
            assert len(intvl) == 2
            intvl  = Interval(intvl[0], intvl[1], sr=self[0].sr)
        assert isinstance(intvl, Interval)

        intvl.iter_rate = env.Key().fps
        p = Pencil(self.name)
        p.layer = layer_name
        for center_frame, _, index in intvl:
            p.keyframe = index + start_frame
            p.stroke(self.get(center_frame))
        

class Skeleton:
    """
    Collection of chains
    """
    def __init__(self, name, chain_list):
        for c in chain_list:
            assert type(c).__name__ == "Chain"
        self._chain_list = chain_list
        self.name = name
    
    @property
    def _chains_all(self):
        return {c.name : c for c in self._chain_list}

    @property
    def _markers_all(self):
        _m_all = {}
        for c in self._chain_list:
            for m in c._marker_list:
                _m_all[m.name] = m
        return _m_all
    
    def __getitem__(self, key):
        if key in self.chains:
            return self._chains_all[key]
        return self._markers_all[key]

    @property
    def chains(self):
        return [c.name for c in self._chain_list]

    @property
    def markers(self):
        return list(self._markers_all.keys())
    
    def show(self, intvl=None, start_frame=1, layer_name="main", chains=True, markers=True):
        if chains:
            for c in self._chain_list:
                c.show(intvl, start_frame, layer_name)
        
        if markers:
            for m in self._markers_all.values():
                m.show(intvl, start_frame)
        
        env.Key().auto_lim()


class Vid(VideoReader):
    def __init__(self, fname):
        self.name = fname
        super().__init__(fname)

    @property
    def cam_id(self):
        return int(self.name.split("-Camera ")[-1].split(" (")[0])

    @property
    def cam_type(self):
        if ("-Camera " in self.name) and (" (#" in self.name):
            return "Optitrack " + self.name.split(" (#")[-1].split(").")[0]
        return "Unknown"

class Clip(Vid):
    """
    Clip is a Vid with start and stop
    """
    def __init__(self, start, stop):
        self.start = start
        self.stop = stop

if __name__ == '__main__':
    fname = r"C:\Temp\Pitching_01_02_Fill500Frm.csv"
    bp = Log(fname)
