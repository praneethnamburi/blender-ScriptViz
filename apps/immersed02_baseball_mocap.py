pt_names = mw["pos"].keys()
posm = mw["pos"]
pos = {}
for pt_name in pt_names:
    print(pt_name)
    tmp_pos = np.array(posm[pt_name])
    pos[pt_name] = np.c_[-tmp_pos[:,0], tmp_pos[:,2], tmp_pos[:,1]]/100 # decimeters

# get pw - position of the wrist from MATLAB workspace
data = pos["Ref_RWristLat"] # converting from mm to cm, even though in blender, everything is in m
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
        ts[sph_name].loc = pos[sph_name][data_center_frame, :]
        ts[sph_name].key(anim_frame, 'l')
    anim_frame = anim_frame + 1
    data_time = data_time + 1/anim_rate

# plot a mesh for an overview of the 'entire' animated trajectory
data_msh = data[int(np.round(anim_start*data_rate)-traj_frame_pre):int(np.round(anim_end*data_rate)+traj_frame_post)]
traj_msh = new.mesh(name="Trajectory_path", x=data_msh[:,0], y=data_msh[:,1], z=data_msh[:,2])
