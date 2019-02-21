#%%
import json
import os
import sys
import numpy as np

PATH_TO_ADD = os.path.realpath('.')
if PATH_TO_ADD not in sys.path:
    sys.path.append(PATH_TO_ADD)

import mkturk as mk
import pntools as my

from importlib import reload

#%%
behAll, _ = mk.fetch(agent='Sausage', startDate='20190201', endDate='20190205', docTypes=['task', 'images'], cachePath=mk.CACHE_PATH)

#%%
[type(k) for k in behAll]
#%% Fetch behavior sessions from firestore only
beh = [mk.session(_file) for _file in behAll]
beh = [k for k in beh if k.nTrials > 10]

#%% Fetch behavior sessions from firestore and dropbox
import dropbox
dbx = dropbox.Dropbox(json.loads(open(mk.DBX_AUTH).read())['DBX_MKTURK_TOKEN'])

behDbx = [json.loads(dbx.files_download(_file['DataFileName'])[1].content) for _file in behAll]
behDbx = [mk.session({k: v for filepart in file for k, v in filepart.items()}) for file in behDbx]

#%%
behDbx[0].sampleObject_id_desc

#%%
behSess = beh[1]
trialCount = 0

h_PN = [imgDb[k].id[:7] for k in behSess.sampleObject_id_desc]
h_EI = behSess.SampleHashesPrefix[behSess.Sample]

print('PN points to:', vars([imgDb[k] for k in imgDb if h_PN[trialCount] in imgDb[k].id[:7]][trialCount])['path_display'])
print('EI points to:', vars([imgDb[k] for k in imgDb if h_EI[trialCount] in imgDb[k].id[:7]][trialCount])['path_display'])

#%%
['displayEnvironment', 'presentedStimuli', 'experimentalParams', 'params text file', 'TRIAL']

#%%
beh[0].properties()
vars(beh[0])
np.shape(beh[0].SampleHashesPrefix)
#%%
np.unique(beh[1].Test[:, 1])
np.where(beh[5].SampleObjectTy == 0)

#%%
allHash = [im.mkturkHash for im in mkturkImg.all_]
uniqueHash = np.unique(allHash)
hashFreq = {}
for entry in uniqueHash:
    hashFreq[entry] = 0

for entry in allHash:
    hashFreq[entry] += 1

hashFreq = np.array(list(hashFreq.values()))
np.unique(hashFreq)

#%%
import matplotlib.pyplot as plt

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
