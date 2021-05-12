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
