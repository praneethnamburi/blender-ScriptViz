import matplotlib.pyplot as plt
import pntools as pn

@pn.Spawn
def plot(q, arr_x, arr_y=None, ion=False):
    """
    example:
        p = plot([2, 3, 43, 23])
        p.send("plt.xlim(0.5, 5)")
        -p
    """
    plt.figure()
    if arr_y is None:
        plt.plot(arr_x)
    else:
        plt.plot(arr_x, arr_y)
    if ion:
        while True:
            plt.pause(0.1)
            msg = q.get()
            if (msg.lower() == 'done'):
                break
            exec(msg)
        print("Received Done!")
    else:
        plt.show()
    
@pn.Spawn
def twinPlots(x,y1,y2):
    """
    Plots the length of muscles and the length of skin over an ultrasound trial.
    times: list of time points, size n, from fm.ot[i].t
    m_tw    length: list of muscle lengths, size n
    s_length: list of skin lengths, size n, from fm.ot[i].
    """

    x1 = []
    x2 = []
    if len(y1) != len(x):
        for i in range(len(y1)):
            x1.append(i*len(x)/len(y1))
    else:
        x1 = x
    
    fig, ax1 = plt.subplots()

    ax1.set_xlabel('Time(s)')
    ax1.set_ylabel('Muscle Length (pixels)')
    ax1.plot(x1,y1,color='r')
    ax1.tick_params(axis='y',labelcolor='r')

    if len(y2) != len(x):
        for i in range(len(y2)):
            x2.append(i*len(x)/len(y2))
    else:
        x2 = x

    ax2 = ax1.twinx()
    ax2.set_ylabel('Skin Length (mm)')
    ax2.plot(x2,y2,color='b')
    ax2.tick_params(axis='y',labelcolor='b')

    fig.tight_layout()
    plt.show()
