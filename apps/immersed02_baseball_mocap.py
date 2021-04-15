fname = r"P:\data\20210311 - Coach Todd Baseball pitch\Pitching_01_02_Fill500Frm.csv"
bp = Log(fname)

# convert position to world coordinates
pos = {}
for mname in bp.pos:
    pos[mname] = bp.pos[mname]()

data = pos["Ref_RWristLat"]
data_rate = 180 # Hz
anim_rate = env.Key().fps # Hz

traj_win = np.r_[-2., 2.] # s

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
        ts[sph_name].loc = pos[sph_name]()[data_center_frame, :]
        ts[sph_name].key(anim_frame, 'l')
    anim_frame = anim_frame + 1
    data_time = data_time + 1/anim_rate

# plot a mesh for an overview of the 'entire' animated trajectory
data_msh = data[int(np.round(anim_start*data_rate)-traj_frame_pre):int(np.round(anim_end*data_rate)+traj_frame_post)]
traj_msh = new.mesh(name="Trajectory_path", x=data_msh[:,0], y=data_msh[:,1], z=data_msh[:,2])
