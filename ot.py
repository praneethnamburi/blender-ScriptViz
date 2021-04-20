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
from bpn import new, env
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

    def show_path(self):
        new.mesh(name=self.name, x=self.co[:,0], y=self.co[:,1], z=self.co[:,2])

    def show(self, start_time=None, end_time=None, start_frame=1, r=0.2):
        if start_time is None:
            start_time = self.t[0]
        if end_time is None:
            end_time = np.min((self.t[-1], 2.0)) # 2 s is the default animation time
        anim_rate = env.Key().fps
        data_rate = self.sr

        ts_name = self.name + '_pos'
        if not get(ts_name):
            ts = new.sphere(name=ts_name, r=r)
            ts.shade("smooth")
        else:
            ts = get(ts_name)

        data_time = start_time
        anim_frame = start_frame
        while data_time <= end_time:
            center_frame = int(np.round(data_time*data_rate))
            ts.loc = self.co[center_frame]
            ts.key(anim_frame, 'l')
            anim_frame = anim_frame + 1
            data_time = data_time + 1./anim_rate

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
    
    def show(self, start_time=None, end_time=None, start_frame=1, layer_name="main"):
        """
        start_frame (int) - animation start frame
        """
        if start_time is None:
            start_time = self[0].t[0]
        if end_time is None:
            end_time = np.min((self[0].t[-1], 2.0)) # 2 s is the default animation time
        anim_rate = env.Key().fps
        data_rate = self[0].sr
        
        p = Pencil(self.name)
        p.layer = layer_name

        data_time = start_time
        anim_frame = start_frame
        while data_time <= end_time:
            center_frame = int(np.round(data_time*data_rate))
            p.keyframe = anim_frame
            p.stroke(trf.PointCloud( np.array( [m.co[center_frame] for m in self] ) ))
            anim_frame = anim_frame + 1
            data_time = data_time + 1./anim_rate

        env.Key().auto_lim()
        

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
    
    def show(self, start_time=None, end_time=None, start_frame=1, layer_name="main", chains=True, markers=True):
        if chains:
            for c in self._chain_list:
                c.show(start_time, end_time, start_frame, layer_name)
        
        if markers:
            for m in self._markers_all.values():
                m.show(start_time, end_time, start_frame)
        

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
