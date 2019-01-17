import numpy as np

def pn_test():
    myPlot(2, 3)

def myPlot(x, y, z=None):
    print(x)
    print(y)
    if z == None:
        print(z)

if __name__ == '__main__':
    pn_test()