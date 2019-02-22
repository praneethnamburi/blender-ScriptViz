#pylint:disable=no-member

#%%
import os
os.chdir('C:\\Workspace\\blenderPython\\apps') # location of this file
#%%
import sys
import numpy as np
import matplotlib.pyplot as plt

DEV_ROOT = os.path.realpath('..') # development root
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)
os.chdir(DEV_ROOT)

import mkturk as mk

#%%
mk.session.clean()
mk.fetch(agent='Sausage', startDate='20190201', endDate='20190205', returnDict=False)
beh = mk.session.query('nTrials > 10')

#%%
np.shape(beh)
#%%
imgDb = mk.img.dictAccess('id_desc')
behSess = beh[1]
trialCount = 0

h_PN = [imgDb[k].id[:7] for k in behSess.sampleObject_id_desc]
h_EI = behSess.SampleHashesPrefix[behSess.Sample]

print('PN points to:', vars([imgDb[k] for k in imgDb if h_PN[trialCount] in imgDb[k].id[:7]][trialCount])['path_display'])
print('EI points to:', vars([imgDb[k] for k in imgDb if h_EI[trialCount] in imgDb[k].id[:7]][trialCount])['path_display'])

#%%
allHash = [im.mkturkHash for im in mk.img.all_]
uniqueHash = np.unique(allHash)
hashFreq = {}
for entry in uniqueHash:
    hashFreq[entry] = 0

for entry in allHash:
    hashFreq[entry] += 1

hashFreq = np.array(list(hashFreq.values()))
np.unique(hashFreq)

#%%
h = plt.figure(figsize=(16, 10))
nRows = 3
nCols = 2
allAx = h.subplots(nRows, nCols, sharey=False, sharex=True)
for sessionCount in range(np.size(beh)):
    rowCount = sessionCount // nCols
    colCount = sessionCount % nCols
    #hIm = allAx[rowCount][colCount].plot(np.sort(beh[sessionCount].rts_valid))
    hIm = allAx[rowCount][colCount].hist(beh[sessionCount].rts[np.logical_and(beh[sessionCount].correctTrials, beh[sessionCount].CorrectItem == 0)], bins=np.linspace(0, 2000, 40), density=True)
    allAx[rowCount][colCount].set_title(beh[sessionCount].Taskdoc)
    plt.xlabel('Time ' + beh[0].timeUnits)
    
plt.xlim(0, 2000)
h.suptitle('Response times')
