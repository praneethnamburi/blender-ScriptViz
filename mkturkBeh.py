"""
Analyze mkturk behavior data.
"""

#%%
import json
import os
import subprocess
import numpy as np

agent = 'Sausage'
startDate = '20190201'
endDate = '20190205'
outFile = f'./_temp/{agent}{startDate}to{endDate}.json'

# get the data from firestore if there is no cached copy
if not os.path.exists(os.path.realpath(outFile)):
    subprocess.run(f'node mkturkBeh_getData.js -a {agent} -s {startDate} -e {endDate} -o {outFile} --no-print')
behAll = json.loads(open(outFile).read()) # download behavior

class behSession:
    """
    Encapsulate one session of mkturk behavior data.
    
    :param fName: File name of mkturk behavior
    :param b: json import of that file
        load behavior using:
            b = json.loads(open(fName).read())
        If you're using firestore and downloaded a series of behavioral
        files into one json object, then you can make a list of behSession
        objects using:
            beh = [behSession(file, behAll[file]) for file in behAll]
    TODO: If only the file name is given, then get it from the database directly
    """
    # pylint: disable=no-member
    def __init__(self, fName, b):
        self.fName = fName
        for attr in b:
            if isinstance(b[attr], list):
                setattr(self, attr, np.array(b[attr])) # lists to numpy arrays
            elif isinstance(b[attr], dict) and len(list(b[attr].keys())[0]) == 1:
                setattr(self, attr, np.array([np.array(k) for k in b[attr].values()]).T) # 2d numpy arrays
            else:
                setattr(self, attr, b[attr])
        self.nTrials = np.size(self.Response)

    @property
    def accuracy(self):
        """Accuracy for that session, across all trials."""
        return np.mean(self.Response == self.CorrectItem)

beh = [behSession(file, behAll[file]) for file in behAll]

#%%
type(beh[0])

#%%
import matplotlib.pyplot as plt
import numpy as np

α = np.linspace(0, 20, 100)
h = plt.figure(figsize=(16, 10))
nRows = 2
nCols = 2
allAx = h.subplots(nRows, nCols)
for imCount in range(nRows*nCols):
    rowCount = imCount // nCols
    colCount = imCount % nCols
    hIm = allAx[rowCount][colCount].plot(α, np.sin(α))
