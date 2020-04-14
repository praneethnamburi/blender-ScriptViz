"""
Sandbox. Not involving blender.

Mode 1:
Type code here, and press Ctrl+Enter (python.datascience.runFileInteractive)
This opens an ipython session and evaluates the code there.
In the current setup, I'm initiating the kernel from blender's python.

Mode 2:
To debug this code, simply insert breakpoint(s) and press f5 (make sure you don't have cells - #%%)

CAUTION: Use these modes only when debugger for blender is not active!
"""

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt

a = (np.sqrt(2)/2 - 4*(0.5**3))/(3*(0.5**3))
t = np.r_[0:1:0.1]

# cubic bezier
plt.plot((1-t)**3 + 3*t*((1-t)**2) + 3*(a*(t**2))*(1-t), 3*a*((1-t)**2)*t + 3*(1-t)*(t**2) + t**3, 'o')
# circle
plt.plot(np.cos(t*np.pi/2), np.sin(t*np.pi/2), 'o')
plt.axis('square')
