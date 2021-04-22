import matplotlib.pyplot as plt
import multiprocessing as mp
mp.set_executable("C:\\Users\\Praneeth\\anaconda3\\envs\\blenderSV\\python.exe")

def plotter(arr):
    plt.figure()
    plt.plot(arr)
    plt.show()

class Plot:
    """ 
    p1 = Plot([0, 1, 2, 3, -10])
    -p1
    """
    def __init__(self, arr, targ=plotter):
        self.ydata = arr
        self.p = mp.Process(target=targ, args=(arr,))
        self.p.start()
    
    def __neg__(self):
        self.p.terminate()
    

if __name__ == '__main__':
    # worker needs to be imported, but other than that, this works great from the blender console!
    p = mp.Process(target=worker, args=([0, 1, 2, 3],))
    p.start()
