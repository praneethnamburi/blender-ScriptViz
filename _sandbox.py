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

fname = 'D:\\Workspace\\blenderPython\\apps\\animation\\armReach_ineffTrial.xlsx'
sheet_name = 'animation'
pt_names = ['RH_AcromioClavicular', 'RH_ElbowLat', 'RH_ElbowMed']

data = pd.read_excel(fname, sheet_name)

pd.unique(data['object'])
pd.unique(data['attribute'])

np.sum([data['object'] == 'RH_AcromioClavicular'])

# create a frame from 3 points
loc = lambda ob: np.vstack(data[(data['object'] == ob) & (data['attribute'] == 'location')]['value'].apply(eval).to_numpy())
norm = lambda n: np.sqrt(np.sum(n**2, axis=1, keepdims=True))
hat = lambda n: n/norm(n)

pos = {ob: loc(ob) for ob in pt_names}
origin = pos['RH_AcromioClavicular']
j_hat = hat((pos['RH_ElbowLat'] + pos['RH_ElbowMed'])/2 - origin)
k_hat = hat(np.cross(pos['RH_ElbowLat'] - origin, pos['RH_ElbowMed'] - origin))
i_hat = np.cross(j_hat, k_hat) # should already be normalized
assert all(np.isclose(norm(i_hat), 1))
