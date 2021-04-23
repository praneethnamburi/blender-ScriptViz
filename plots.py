import matplotlib.pyplot as plt
import pntools as pn

@pn.Spawn
def plot(q, arr, ion=False):
    """
    example:
        p = plot([2, 3, 43, 23])
        p.send("plt.xlim(0.5, 5)")
        -p
    """
    plt.figure()
    plt.plot(arr)
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
