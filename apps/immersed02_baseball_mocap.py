from bpn_init import *

fname = r"P:\data\20210311 - Coach Todd Baseball pitch\Pitching_01_02_Fill500Frm.csv"
bp = ot.Log(fname)

# convert position to world coordinates
pos = {}
for mname in bp.pos:
    pos[mname] = bp.pos[mname]()

data = pos["Ref_RWristLat"]
data_rate = 180 # Hz
anim_rate = env.Key().fps # Hz

traj_win_pre = 2. # s
traj_win_post = 0. # s

anim_start = 10*60. # s
anim_end = 10*60+30. # s duration of the animation

traj_frame_pre = np.round(traj_win_pre*data_rate)
traj_frame_post = np.round(traj_win_post*data_rate)

anim_frame = env.Key().start
data_time = anim_start

p = Pencil(name="Trajectory_pred")
p.layer = "Ref_RWristLat"

ts = {}
for sph_name in pos.keys():
    ts[sph_name] = new.sphere(name=sph_name, r=0.3)
    ts[sph_name].shade("smooth")

stroke_list = list()
while data_time <= anim_end:
    data_center_frame = int(np.round(data_time*data_rate))
    p.keyframe = anim_frame
    stroke_list.append(p.stroke(trf.PointCloud(data[int(data_center_frame-traj_frame_pre):int(data_center_frame+traj_frame_post), :])))
    for sph_name in ts:
        ts[sph_name].loc = pos[sph_name][data_center_frame, :]
        ts[sph_name].key(anim_frame, 'l')
    anim_frame = anim_frame + 1
    data_time = data_time + 1/anim_rate

# plot a mesh for an overview of the 'entire' animated trajectory
data_msh = data[int(np.round(anim_start*data_rate)-traj_frame_pre):int(np.round(anim_end*data_rate)+traj_frame_post)]
traj_msh = new.mesh(name="Trajectory_path", x=data_msh[:,0], y=data_msh[:,1], z=data_msh[:,2])

env.Key().auto_lim()

#%%
data = []
data_len = []
with open(fname, newline='') as f:
    reader = csv.reader(f)
    for row in reader:
        data.append(row)
        data_len.append(len(row))

#%%
from decord import VideoReader
vid_name = r"C:\Temp\Pitching_01-Camera 1 (#83729).mp4"
vr = VideoReader(vid_name)
#%%
len(vr)
# %%
x = vr[0:10].asnumpy()
np.shape(x)

#%%
import matplotlib.pyplot as plt
fig = plt.figure(figsize=(4,3), dpi=300)
ax1 = fig.add_axes([0, 0, 0.5, 1], label="image")
ax2 = fig.add_axes([0, 0, 0.5, 1], label="plot")
ax1.axis('off')
ax2.axis('off')

h_im = ax1.imshow(x[0][:, :, 1].astype(float), cmap=plt.get_cmap("gray"))
h, = ax2.plot(x[0][:, 1, 0], antialiased=True)
h_im.set_clim(0., 50.)

for i in range(0, 10):
    h_im.set_data(x[i][:, :, 1].astype(float)-x[0][:, :, 1].astype(float))
    h_im.set_clim(0., 50.)
    h.set_ydata(x[0][:, i, 0])
    plt.savefig("C:\\Temp\\test{:04d}.png".format(i), transparent=True)

#%%
fname = "C:\\Temp\\Pitching_01_02_Fill500Frm.csv"
bp = ot.Log(fname)
c = []
c.append(ot.Chain('Spine', [bp.pos['Spine_' + x] for x in 'L4 T11 T4 C3'.split(' ')]))
c.append(ot.Chain('ShoulderGirdle_top', [bp.pos['Ref_LAcromion'], bp.pos['Spine_C3'], bp.pos['Ref_RAcromion']]))
c.append(ot.Chain('ShoulderGirdle_bottom', [bp.pos['Ref_LAcromion'], bp.pos['Spine_T4'], bp.pos['Ref_RAcromion']]))
c.append(ot.Chain('LHip', [bp.pos['Ref_LHip'], bp.pos['Spine_L4']]))
c.append(ot.Chain('LFoot', [bp.pos['Ref_LBigToe'], bp.pos['Ref_LLitteToe']]))
c.append(ot.Chain('RFoot', [bp.pos['Ref_RBigToe'], bp.pos['Ref_RLittleToe']]))
c.append(ot.Chain('RightArmLat', [bp.pos['Ref_RAcromion'], bp.pos['Ref_RElbowLat'], bp.pos['Ref_RWristLat']]))
c.append(ot.Chain('RightArmMed', [bp.pos['Ref_RAcromion'], bp.pos['Ref_RElbowMed'], bp.pos['Ref_RWristMed']]))
c.append(ot.Chain('LeftArmLat', [bp.pos['Ref_LAcromion'], bp.pos['Ref_LElbowLat'], bp.pos['Ref_LWrist']]))
c.append(ot.Chain('Legs', [bp.pos['Ref_LBigToe'], bp.pos['Spine_L4'], bp.pos['Ref_RBigToe']]))
sk = ot.Skeleton('Sk1', c)
# this says that the timestamp is from a video that was captured at 30 Hz, but the interval is to act on data sampled at bp.sr Hz
intvl = []
intvl.append(pn.sampled.Interval('00;05;57;26', '00;06;01;29', sr=30, iter_rate=env.Key().fps).change_sr(bp.sr))
intvl.append(pn.sampled.Interval('00;08;08;01', '00;08;11;20', sr=30, iter_rate=env.Key().fps).change_sr(bp.sr))
intvl.append(pn.sampled.Interval('00;08;16;18', '00;08;20;28', sr=30, iter_rate=env.Key().fps).change_sr(bp.sr))
intvl.append(pn.sampled.Interval('00;08;29;06', '00;08;33;02', sr=30, iter_rate=env.Key().fps).change_sr(bp.sr))
intvl.append(pn.sampled.Interval('00;09;37;24', '00;09;42;28', sr=30, iter_rate=env.Key().fps).change_sr(bp.sr))
intvl.append(pn.sampled.Interval('00;09;48;10', '00;09;54;23', sr=30, iter_rate=env.Key().fps).change_sr(bp.sr))
intvl.append(pn.sampled.Interval('00;09;59;20', '00;10;05;27', sr=30, iter_rate=env.Key().fps).change_sr(bp.sr))
intvl.append(pn.sampled.Interval('00;10;14;15', '00;10;18;22', sr=30, iter_rate=env.Key().fps).change_sr(bp.sr))
intvl.append(pn.sampled.Interval('00;10;23;17', '00;10;27;00', sr=30, iter_rate=env.Key().fps).change_sr(bp.sr))
intvl.append(pn.sampled.Interval('00;10;32;00', '00;10;36;25', sr=30, iter_rate=env.Key().fps).change_sr(bp.sr))

x = bp.pos['Ref_RWristLat']
for count, this_intvl in enumerate(intvl):
    x.show_trajectory(this_intvl, color=count%7, keyframe=count+1)
    x.show_trajectory(this_intvl, color=count%7, keyframe=len(intvl)+1)

x.show_trajectory(intvl(0, 0), color='white', keyframe=len(intvl)+2)
curr_keyframe = len(intvl)+1

sk.show(intvl[0], start_frame=curr_keyframe+1+10, markers=False, color='white')
sk.show(intvl[-1], start_frame=curr_keyframe+1, markers=False, color=3)
env.Key().lim = [curr_keyframe+66, curr_keyframe+93] 
env.Key().fps = 12

cr = new.CircularRig()
cr.scale(10)
cr.center = [0, 0, 10]
cr.target = [-12, 2, 15]
cr.fov = 80

# Computed markers - ability to easily add and/or subtract marker coordinates
# Check - when using Pencil from Mantle, it will resist creating a new object, but new.Pencil always creates a new object?
# add ability to show computed markers
# add time interval objects for events
# events - tag and show multiple events
# show multiple events simultaneously to contrast them
# event dilation - events have internal markers based on physiological metrics, and the time can be dilated to each phase
# COM computation
# Markers, Chains, and Skeleton: Extract events

#%%
# Extract events, categorize them into practice, pitching without release, pitching with release
# Instability:
# Position of the spine
# Relationship to the back foot
# Mark the duration of the instability (compare to full speed)
# Timing of the start of instability (chair drill vs regular)
# Trajectory - how to separate the hands

#%% Working with events

intvl = pn.sampled.Interval(-2., 5., 0., sr=180., iter_rate=30.)
event_times = ['00;09;49;15', '00;10;51;12']
intervals = []
for e in event_times:
    intervals.append(intvl+pn.sampled.Time(e, 30.).change_sr(intvl.sr)) # 30 Hz is the sampling rate of the video where the timestamp was recorded, and the accompanying data has a rate of 180 Hz
