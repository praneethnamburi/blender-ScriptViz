import os
import dill

import ot

try:
    from bpn import new, env, io
    BLENDER_MODE = True
except ImportError:
    BLENDER_MODE = False

def load_rumba():
    fdir = "C:\\Temp\\dl\\"
    fname_all = [fdir + "rumba" + x + ".csv" for x in ['', '_001', '_002', '_003']]
    fname_pkl = "rumba_all.pkl"
    if os.path.exists(fdir + fname_pkl):
        return dill.load(open(fdir + "rumba_all.pkl", mode='rb'))
    else:
        r = []
        for fname in fname_all:
            r.append(ot.Log(fname))        
        dill.dump((fname_all, r), open(fdir + fname_pkl, mode='wb'))

def make_skeleton(rsession):
    c = []
    c.append(ot.Chain('Spine', [rsession.pos['Ref_Spine' + x] for x in '01 02 03 04 05 06 07'.split(' ')], color='yellow'))
    # c.append(ot.Chain('Left_leg', [rsession.pos['Ref_' + x] for x in ''.split('')]))
    c.append(ot.Chain('Left_leg', [rsession.pos['Ref_L' + x] for x in 'LittleToe BigToe Heel Knee Hip'.split(' ')], color='green'))
    c.append(ot.Chain('Right_leg', [rsession.pos['Ref_R' + x] for x in 'LittleToe BigToe Heel Knee Hip'.split(' ')]))
    c.append(ot.Chain('Right_lat', [rsession.pos['Ref_Spine02']] + [rsession.pos['Ref_Lat' + x] for x in '02 03 04 05'.split(' ')]))
    c.append(ot.Chain('Shouldergirdle', [rsession.pos['Ref_LAcromion'], rsession.pos['Ref_Spine06'], rsession.pos['Ref_RAcromion']]))
    return ot.Skeleton('Sk' + rsession.fname.split('\\')[-1].split('.')[0], c)

if BLENDER_MODE:
    def create_rig():
        cr = new.CircularRig()
        cr.center = [13, 6, 14]
        cr.target = [13, 6, 10]
        cr.scale(20)
        cr.fov = 80
        cr.theta = cr.theta + np.pi
        return cr

    def render_animation(fpath="C:\\Temp\\dl\\rumba_001\\"):
        for frame in range(env.Key().start, env.Key().end+1):
            env.Key().goto(frame)
            io.render('{:05d}.png'.format(frame), out_type='img', fpath=fpath)

if __name__ == '__main__':
    fname_all, r = load_rumba()
    sk = [make_skeleton(rsession) for rsession in r]
    # sk.show(pn.Interval('00;00;00;01', '00;00;04;29', sr=30, iter_rate=env.Key().fps).change_sr(rsession.sr))
    # sk.show(pn.Interval(int(rsession.sample[0]), int(rsession.sample[-1]), sr=rsession.sr, iter_rate=env.Key().fps))
    if BLENDER_MODE:
        env.Key().fps = 25
        sk[-1].show(pn.Interval(int(sk[-1].sample[0]), int(sk[-1].sample[-240]), sr=sk[-1].sr, iter_rate=env.Key().fps))
    