import matplotlib.pyplot as plt
import multiprocessing as mp

import pntools as pn

mp.set_executable(pn.locate_command('python', 'conda').split('\r\n')[0])

def plotter(arr, queue):
    plt.figure()
    plt.plot(arr)
    plt.show()
    queue.put(plt)

class Plot:
    """ 
    p1 = Plot([0, 1, 2, 3, -10])
    -p1
    """
    def __init__(self, arr, targ=plotter):
        self.ydata = arr
        self._q = mp.Queue()
        self.p = mp.Process(target=plotter, args=(arr, self._q))
        self.p.start()

    def __neg__(self):
        self.p.terminate()

    def wait(self):
        self.p.join()
        return self._q.get()
    

if __name__ == '__main__':
    # worker needs to be imported, but other than that, this works great from the blender console!
    p = mp.Process(target=worker, args=([0, 1, 2, 3],))
    p.start()
