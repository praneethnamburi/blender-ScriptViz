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

import os
os.chdir('D:\\Workspace\\blenderPython')

import numpy as np
import matplotlib.pyplot as plt

plt.plot(np.cumsum([46, 113, 141, 225, 247]))
plt.show();
