"""
Work with optitrack files in python.

This module provides the ability to parse csv tracking data from the optitrack motion capture system. 
It offers three basic data structures - Marker, Chain, and Skeleton
Chains are a sequential collection of markers, and a skeleton is a collection of chains.
Each of these data types can be spliced in time using the Interval object from pntools.
"""
import os
import csv
import subprocess
import numpy as np
from decord import VideoReader

from bpn import trf
import pntools as pn

try:
    # for drawing - requires blender modules
    from bpn import new, env, utils
    from bpn.mantle import Pencil
    from bpn.utils import get
    BLENDER_MODE = True
except ImportError:
    BLENDER_MODE = False

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

    if BLENDER_MODE:
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
    def __init__(self, name, marker_list, color='white'):
        for m in marker_list:
            assert isinstance(m, Marker)
        self._marker_list = marker_list
        self.name = name
        self.parent = self.markers[0].parent # assumes all markers are from the same data session
        self._color = color

    @property
    def marker_names(self):
        return [m.name for m in self._marker_list]

    @property
    def markers(self):
        return self._marker_list

    @property
    def interval(self):
        return self._marker_list[0].interval

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, col):
        self._color = col

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

    if BLENDER_MODE:
        def show(self, intvl=(0., 2.), start_frame=1, color=None, **kwargs):
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

            if color is None:
                color = self._color

            intvl.iter_rate = env.Key().fps
            p = Pencil(self.name, color=color, **kwargs)
            for center_frame, _, index in intvl:
                p.keyframe = index + start_frame
                p.stroke(self.get_snapshot(center_frame))


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

    if BLENDER_MODE:
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


class Daemon:
    """
    Example:
        d = Daemon(base_dir='/home/praneeth/motive')
        d.report()
        d.convert_avi(verbose=True)
    Next:
        1. Delete avi files when the corresponding mp4 matches a duration check
        2. Saving serialized log files
    Workflow:

    """
    def __init__(self, base_dir=None, all_dir=None, nproc=None, load_videos=False):
        if base_dir is None:
            if os.name == 'nt':
                base_dir = "P:\data"
            else:
                base_dir = '/home/praneeth/nas/data'

        if all_dir is None:
            all_dir = [x for x in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, x)) and x[0] != '_']
            # self.all_dir = ['20200220 - foot nutations tensegrity', '20200221 - Arm reach EMG', '20200220 - Arm reach EMG', '20200219 - resistance bands', '20200206 FL EMG', '20200124 - Spiral line Functional lines', '20200123 - back functional line 2', '20200116 - back functional line', '20200115 - spine', '20200114', '20200109', '20200108']

        if nproc is None:
            if os.name == 'nt':
                nproc = 3
            else:
                nproc = 10

        assert isinstance(base_dir, str)
        assert isinstance(all_dir, list)
        assert isinstance(nproc, int)

        self.base_dir = base_dir
        self.all_dir = all_dir
        self.nproc = nproc
        self._videos = {}
        if load_videos:
            file_list = self.all_avi + self.all_mp4
            for f in file_list:
                self._videos[f.lstrip(self.base_dir)] = Vid(f)

    @property
    def videos(self):
        return self._videos

    @property
    def all_dirs(self):
        return [os.path.join(self.base_dir, x) for x in self.all_dir]

    def _proc_dir(self, pattern):
        path_or_file = self.all_dirs
        if isinstance(path_or_file, list):
            # assume each entry is either a directory or a file
            all_files = []
            for pf in path_or_file:
                assert os.path.isfile(pf) or os.path.isdir(pf)
                if os.path.isfile(pf):
                    all_files.append(pf)
                else: # add all avi files in directory
                    all_files += pn.find(pattern, pf)
        else:
            assert os.path.isfile(path_or_file) or os.path.isdir(path_or_file)
            if os.path.isfile(path_or_file):
                all_files = [path_or_file]
            else:
                all_files = pn.find(pattern, path_or_file)
        return all_files

    @property
    def all_avi(self):
        return self._proc_dir('*Camera *.avi')
    
    @property
    def all_mp4(self):
        return self._proc_dir('*Camera *.mp4')

    def report(self):
        all_avi = self.all_avi
        all_mp4 = self.all_mp4

        avi_size = sum(list(pn.file_size(all_avi).values()))
        mp4_size = sum(list(pn.file_size(all_mp4).values()))
        print(str(len(all_avi)) + ' AVI files taking up ' + '{:4.3f} GB'.format(avi_size))
        print(str(len(all_mp4)) + ' MP4 files taking up ' + '{:4.3f} GB'.format(mp4_size))

    def conversion_status(self):
        """Is there a corresponding MP4 file?"""
        avi_with_mp4 = []
        avi_without_mp4 = []
        for f in self.all_avi:
            if os.path.isfile(f[:-4]+'.mp4'):
                avi_with_mp4.append(f)
            else:
                avi_without_mp4.append(f)
        
        mp4_with_avi = []
        mp4_without_avi = []
        for f in self.all_mp4:
            if os.path.isfile(f[:-4]+'.avi'):
                mp4_with_avi.append(f)
            else:
                mp4_without_avi.append(f)

        return avi_with_mp4, avi_without_mp4, mp4_with_avi, mp4_without_avi

    @property
    def avi_with_mp4(self):
        return [f for f in self.all_avi if os.path.isfile(f[:-4]+'.mp4')]
    
    @property
    def avi_without_mp4(self):
        return [f for f in self.all_avi if not os.path.isfile(f[:-4]+'.mp4')]
    
    @property
    def mp4_with_avi(self):
        return [f for f in self.all_mp4 if os.path.isfile(f[:-4]+'.avi')]
    
    @property
    def mp4_without_avi(self):
        return [f for f in self.all_mp4 if not os.path.isfile(f[:-4]+'.avi')]

    def _to_commands(self, all_files, overwrite):
        """
        Use ffmpeg to convert avi to mp4 [preset for optitrack exports], including introducing the transpose
        Command template:
            "ffmpeg -i "rumba_001-Camera 21 (#83743).avi" -c:v h264_nvenc -vf "transpose=1" -preset fast "rumba_001-Camera 21.mp4"
        Example:
            convert_avi("P:\\data\\20210312 - Santosh Boxing", nproc=3, overwrite=False)
        """  
        all_cmds = []
        for f in all_files:
            fout = f[:-4]+'.mp4'
            if (not os.path.exists(fout)) or overwrite:
                all_cmds.append(['ffmpeg', '-y' if overwrite else '-n', '-i', f, '-c:v', 'h264_nvenc', '-vf', 'transpose=1', '-preset', 'fast', fout])

        return all_cmds
    
    def convert_avi(self, conversion_list=None, overwrite=False, verbose=False):
        """
        Parallel-process conversion of avi files in conversion_list
        NOTE: Adjust nproc according to your graphics card capability when using a gpu codec
        3 processes for RTX2080
        """
        if conversion_list is None:
            conversion_list = self.avi_without_mp4   
        all_cmds = self._to_commands(conversion_list, overwrite)
        pn.spawn_commands(all_cmds, nproc=self.nproc, retry=True, verbose=verbose)

    def n_frames(self, file_list=None):
        if file_list is None:
            file_list = self.all_avi
        ret = {}
        for f in file_list:
            ret[f.lstrip(self.base_dir)] = len(self.videos[f])
        return ret

    @property
    def video_size(self):
        return pn.file_size(self.all_avi + self.all_mp4)

    @property
    def big_videos(self):
        # return all videos with size > 4 GB
        return {f:s for f,s in self.video_size.items() if s > 4*1024}

    @staticmethod
    def vid_dur(vid_name):
        x = subprocess.getoutput("ffprobe -hide_banner -show_entries stream=duration '" + vid_name + "'")
        return float(x.split('[STREAM]')[-1].split('[/STREAM]')[0].split('duration=')[-1])

    def duration_check(self, verbose=True):
        """
        Return videos with mismatched duration.
        Example:
            matched_dur, mismatched_dur = d.duration_check()
            for fname, dur in mismatched_dur.items():
                print(dur, fname)
        
        dur is a tuple of mp4 duration and avi duration
        """
        avi_with_mp4 = self.avi_with_mp4
        matched_dur = {}
        mismatched_dur = {}
        for avi_name in avi_with_mp4:
            avi_dur = self.vid_dur(avi_name)
            mp4_dur = self.vid_dur(avi_name[:-4]+'.mp4')
            if avi_dur != mp4_dur:
                mismatched_dur[avi_name] = (avi_dur, mp4_dur)
            else:
                matched_dur[avi_name] = (avi_dur, mp4_dur)
        
        if verbose:
            for fname, dur in mismatched_dur.items():
                print(dur, fname)

        return matched_dur, mismatched_dur

    def fix_avi_with_problems(self, vid_list=None, verbose=False):
        if vid_list is None:
            matched_dur, mismatched_dur = self.duration_check()
            vid_list = list(mismatched_dur.keys())
        
        all_cmds = []
        for vid_name in vid_list:
            vid_fix_name = vid_name[:-4]+'_fixed.avi'
            all_cmds.append(['ffmpeg', '-err_detect', 'ignore_err', '-i', vid_name, '-c', 'copy', vid_fix_name])
        pn.spawn_commands(all_cmds, nproc=self.nproc, retry=True, verbose=verbose, wait=True)
        import shutil
        for vid_name in vid_list:
            vid_fix_name = vid_name[:-4]+'_fixed.avi'
            shutil.move(vid_fix_name, vid_name)

    def clean_avi(self):
        """Delete all AVI files with a corresponding mp4 if the pair passes duration check"""
        matched_dur, _ = self.duration_check()
        for avi_name in matched_dur:
            os.remove(avi_name)
            