import os

import numpy as np
import pntools as pn
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
    c.append(ot.Chain('Hips', [rsession.pos['Ref_LHip'], rsession.pos['Ref_Spine01'], rsession.pos['Ref_RHip']], color='tomato'))
    return ot.Skeleton('Sk' + rsession.fname.split('\\')[-1].split('.')[0], c)

def timestamps():
    sr = 25 # zoom recording's sr
    # r01
    t0 = pn.SampledTime(4560, sr)
    event = {}
    # Things to do
    #   right to left vs left to right weight shift comparison

    # instruction - slowly shift over to the other leg
    event[0] = pn.Interval(5520, 5569, sr=sr) # feedback - 
    # instruction - make a gesture downward your push-off leg and simultaneously upward your receiving leg
    event[1] = pn.Interval(5593, 5693, sr=sr) # feedback - good
    # sk[1].show(event[1].change_sr(sk[1].sr) - t0)
    # moving from the right leg to the left - simultaneous up and down cycles
    event[2] = pn.Interval(6063, 6163, sr=sr) # feedback - very good
    # sk[1].show(event[2].change_sr(sk[1].sr) - t0)
    # put the hands on top your Ilia and think about which way the pelvic action interact with up-down gesture
    event[3] = pn.Interval(6717, 6789, sr=sr) # feedback - good
    # sk[1].show(event[3].change_sr(sk[1].sr) - t0)
    # Ilium directs itself more and more towards the push-off leg
    event[4] = pn.Interval(7035, 7170, sr=sr) # feedback - good
    event[5] = pn.Interval(7175, 7280, sr=sr)
    # and then when you change the Ilium, you enter the second phase of the upward cycle on the new leg
    event[6] = pn.Interval(7359, 7480, sr=sr)
    # Pause - something is not right here, can you put the pelvis more towards the right leg?
    event[7] = pn.Interval(7745, 7800, sr=sr) # feedback - good


    t_pose = {}
    t_pose['Arrival'] = pn.SampledTime(7916, sr)
    return event, t_pose

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

    def ev_show(ev, sk, t0):
        sk.show(ev.change_sr(sk.sr) - t0.change_sr(sk.sr))

if __name__ == '__main__':
    fname_all, r = load_rumba()
    sk = [make_skeleton(rsession) for rsession in r]
    # sk.show(pn.Interval('00;00;00;01', '00;00;04;29', sr=30, iter_rate=env.Key().fps).change_sr(rsession.sr))
    # sk.show(pn.Interval(int(rsession.sample[0]), int(rsession.sample[-1]), sr=rsession.sr, iter_rate=env.Key().fps))
    if BLENDER_MODE:
        env.Key().fps = 25
        sk[-1].show(pn.Interval(int(sk[-1].sample[0]), int(sk[-1].sample[-240]), sr=sk[-1].sr, iter_rate=env.Key().fps))
    