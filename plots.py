import matplotlib.pyplot as plt
import multiprocessing as mp

import pntools as pn

mp.set_executable(pn.locate_command('python', 'conda').split('\r\n')[0])

class Spawn:
    def __init__(self, func):
        self.func = func
    def __call__(self, *args, **kwargs):
        self._proc = mp.Process(target=self.func, args=args, kwargs=kwargs)
        self._proc.start()
        return self
    def __neg__(self):
        self._proc.terminate()

def _plot(arr):
    plt.figure()
    plt.plot(arr)
    plt.show()

plot = Spawn(_plot)

if __name__ == '__main__':
    # worker needs to be imported, but other than that, this works great from the blender console!
    p = plot([2, 3, 4, 23])
    p.terminate()
