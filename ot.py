"""
Work with optitrack files in python.

This module provides the ability to parse csv tracking data from the optitrack motion capture system. 
It offers three basic data structures - Marker, Chain, and Skeleton
Chains are a sequential collection of markers, and a skeleton is a collection of chains.
Each of these data types can be spliced in time using the Interval object from pntools.
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

DIST_UNITS = {'Millimeters':-3, 'Centimeters':-2, 'Meters':0}

class Log:
    """
    Read Optitrack log files (CSV export)
    Example:
        fname = r"P:\data\20210311 - Coach Todd Baseball pitch\Pitching_01_02_Fill500Frm.csv"
        bp = ot.Log(fname)
    """
    def __init__(self, fname, coord_frame=trf.CoordFrame(i=(-1, 0, 0), j=(0, 0, 1), k=(0, 1, 0))):
        self.fname = fname
        self.disp_scale = 100. # set during creation! DOES NOT impact export
        assert self.disp_scale in [1./1000, 1./100, 1./10, 1, 10, 100, 1000]

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

        self._sample = data3d[:, frame_num_col].astype(int)
        self._t = data3d[:, time_col]
            
        self.pos = {}
        for marker_name in marker_names_valid:
            this_cols, = np.where(np.array(marker_name_row_valid) == marker_name) # assuming X, Y, Z sequence during export
            self.pos[marker_name] = Marker(marker_name, data3d[:, this_cols]/self.disp_scale, coord_frame, self).in_world()

    @property
    def t(self):
        return self._t

    @property
    def sample(self):
        return self._sample

    def __len__(self):
        return len(self.sample)

    @property
    def marker_names(self):
        return list(self.pos.keys())
    
    @property
    def sr(self):
        """sampling rate"""
        return self.hdr['Export Frame Rate']

    @property
    def units(self):
        ux = {-3:'mm', -2:'cm', -1:'dm', 0:'m'}
        x = DIST_UNITS[self.hdr['Length Units']] + int(np.log10(self.disp_scale))
        return ux[x]

        # return str(self.disp_scale) + " " + self.hdr['Length Units']
    
    def load_videos(self):
        vids = pn.find("*Camera*.mp4", os.path.dirname(self.fname))
        if not vids:
            vids = pn.find("*Camera*.avi", os.path.dirname(self.fname))
        return [Vid(vid_name) for vid_name in vids]
    # elements for animation:
    # markers, connections, clips, chains (to measure length)


@pn.PortProperties(Log, 'parent')
class Marker(trf.PointCloud):
    def __init__(self, name, vert, frame, parent, interval=None):
        """
        name    (str) - name of the marker
        vert    (n x 3 numpy array)
        frame   (4x4 frame, OR, trf.CoordFrame)
        parent  (ot.Log) - Log file object
        interval (pn.Interval) - for placing the marker in time
        """
        assert isinstance(parent, Log)
        self.name = name
        super().__init__(vert, frame)
        self.parent = parent
        if interval is None:
            interval  = pn.Interval(int(parent.sample[0]), int(parent.sample[-1]), sr=parent.sr)
        assert isinstance(interval, pn.Interval)
        self._interval = interval # to place the marker in time

        self.in_frame = self._pointcloud_to_marker(self.in_frame)
        self.in_world = self._pointcloud_to_marker(self.in_world)
        self.transform = self._pointcloud_to_marker(self.transform)
        self.reframe = self._pointcloud_to_marker(self.reframe)

    @staticmethod
    def _pointcloud_to_marker(meth):
        def modifiedMethod(*args, **kwargs):
            pc = meth(*args, **kwargs)
            s = meth.__self__
            return Marker(s.name, pc.co, pc.frame, s.parent)
        return modifiedMethod

    def __getitem__(self, key):
        """Use an interval object to slice the marker"""
        if isinstance(key, pn.SampledTime):
            key = key.to_interval()
        assert isinstance(key, (pn.Interval, pn.SampledTime))
        if key.sr != self.sr:
            print("Warning: sampling rate of the key is changed to the marker's sampling rate")
            key.sr = self.sr
        return Marker(self.name, self.co[key.start.sample:key.end.sample+1], self.frame, self.parent, interval=key) # to include both start and end samples!

    def __len__(self):
        return len(self.sample)

    @property
    def interval(self):
        return self._interval

    @property
    def t(self):
        return self.parent.t[self._interval.start.sample:self._interval.end.sample+1]
    
    @property
    def sample(self):
        return self.parent.sample[self._interval.start.sample:self._interval.end.sample+1]

    def show_path(self):
        new.mesh(name=self.name, x=self.co[:,0], y=self.co[:,1], z=self.co[:,2])

    def show(self, intvl=(0., 2.), start_frame=1, r=0.2):
        if isinstance(intvl, (list, tuple)):
            assert len(intvl) == 2
            intvl  = pn.Interval(intvl[0], intvl[1], sr=self[0].sr)
        assert isinstance(intvl, pn.Interval)

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

    def show_trajectory(self, intvl=(0., 2.), keyframe=1, color='darkorange', **kwargs):
        """Plot trajectory for a given time interval"""
        p = Pencil(self.name, color=color, keyframe=keyframe, **kwargs)
        p.stroke(self[intvl].in_world())


@pn.PortProperties(Log, 'parent')
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
            assert isinstance(m, Marker)
        self._marker_list = marker_list
        self.name = name
        self.parent = self.markers[0].parent # assumes all markers are from the same data session

    @property
    def marker_names(self):
        return [m.name for m in self._marker_list]

    @property
    def markers(self):
        return self._marker_list

    @property
    def interval(self):
        return self._marker_list[0].interval

    def __getitem__(self, key):
        # integer - retrieve a marker by its position in the chain
        if isinstance(key, int):
            return self._marker_list[key]
        # string - retrieve a marker by its name by searching through the list
        if isinstance(key, str):
            return [m for m in self._marker_list if m.name == key][0]
        # pn.SampledTime, or pn.Interval - splice all markers in the chain, and return a new chain that is localized in time
        if isinstance(key, (pn.SampledTime, pn.Interval)):
            return Chain(self.name, [m[key] for m in self._marker_list])
    
    def get_snapshot(self, sample_index):
        """Positions of all markers in the chain at sample_index as a point cloud"""
        return trf.PointCloud( np.array( [m.co[sample_index] for m in self._marker_list] ) )
    
    def show(self, intvl=(0., 2.), start_frame=1, color='white', **kwargs):
        """
        intvl (pn.Interval, tuple) - Interval object, or a tuple of (float, float) implying start and end time, 
            or a tuple of (int, int) implying start and end frame
        start_frame (int) - animation start frame
        color (int, str, or dict) 
            - integers 0 to 7 - matlab color order
            - string - name of the color (anything from matplotlib's list will do)
                https://matplotlib.org/stable/gallery/color/named_colors.html
            - dict {name: [r, g, b, a]}
        kwargs - anything that Pencil takes
        """
        if isinstance(intvl, (list, tuple)):
            assert len(intvl) == 2
            intvl  = pn.Interval(intvl[0], intvl[1], sr=self[0].sr)
        assert isinstance(intvl, pn.Interval)

        intvl.iter_rate = env.Key().fps
        p = Pencil(self.name, color=color, **kwargs)
        for center_frame, _, index in intvl:
            p.keyframe = index + start_frame
            p.stroke(self.get_snapshot(center_frame))

    def __len__(self):
        """Number of markers in the chain"""
        return len(self._marker_list)
    
    def length(self, units='mm'):
        """Sequence especially matters here."""
        ux = {'mm':-3, 'cm':-2, 'dm':-1, 'm':0}
        assert units in ux.keys()
        log = self._marker_list[0].parent
        mul_units = 10.**(ux[log.units] - ux[units])
        le = np.zeros_like(log.t)
        for m1, m2 in zip(self._marker_list[:-1], self._marker_list[1:]):
            le += np.linalg.norm(m2.co-m1.co, axis=1)
        return le*mul_units


@pn.PortProperties(Log, 'parent')
class Skeleton:
    """
    Collection of chains
    """
    def __init__(self, name, chain_list):
        for c in chain_list:
            assert isinstance(c, Chain)
        self._chain_list = chain_list
        self.name = name
        self.parent = self.chains[0].markers[0].parent
    
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
        if isinstance(key, str): # should be either the name of a marker or a chain
            if key in self.chain_names:
                return self._chains_all[key]
            elif key in self.marker_names:
                return self._markers_all[key]
            else:
                raise KeyError(key, "Not a chain or marker in this skeleton")
        if isinstance(key, (pn.SampledTime, pn.Interval)): # new skeleton object, spliced in time
            return Skeleton(self.name, [c[key] for c in self._chain_list])

    @property
    def chain_names(self):
        return [c.name for c in self._chain_list]

    @property
    def marker_names(self):
        return list(self._markers_all.keys())
    
    @property
    def chains(self):
        return self._chain_list

    @property
    def markers(self):
        return list(self._markers_all.values())

    @property
    def interval(self):
        return self.chains[0].interval

    def show(self, intvl=None, start_frame=1, chains=True, markers=True, **kwargs):
        """kwargs are for Pencil"""
        if chains:
            for c in self._chain_list:
                c.show(intvl, start_frame=start_frame, **kwargs)
        
        if markers:
            for m in self._markers_all.values():
                m.show(intvl, start_frame=start_frame)
        
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
