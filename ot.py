"""
Work with optitrack files in python. This module can be used without blender.
"""
import os
import csv
import numpy as np
from decord import VideoReader

from bpn import trf
import pntools as pn

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
            self.pos[marker_name] = Marker(marker_name, data3d[:, this_cols], coord_frame, self).in_world()

        self.vid_frame = data3d[:, frame_num_col].astype(int)
        self.t = data3d[:, time_col]

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
