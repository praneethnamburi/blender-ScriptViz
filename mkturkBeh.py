"""
Analyze mkturk behavior data.
"""
import json
import os
import subprocess

agent = 'Sausage'
startDate = '20190201'
endDate = '20190205'
outFile = f'./_temp/{agent}{startDate}to{endDate}.json'

# get the data from firestore if there is no cached copy
if not os.path.exists(os.path.realpath(outFile)):
    subprocess.run(f'node mkturkBeh_getData.js -a {agent} -s {startDate} -e {endDate} -o {outFile} --no-print')

tmp1 = json.loads(open(outFile).read())
print(len(tmp1.keys()))


#%%
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

x = np.linspace(0, 20, 100)
plt.plot(x, np.sin(x))
plt.show() 

