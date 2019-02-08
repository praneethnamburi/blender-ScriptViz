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
        Note that time is in ms
        
    List of variables and their description:
        https://github.com/dicarlolab/mkturk/tree/master/public
    TODO: If only the file name is given, then get it from the database directly
    TODO: Tag trials - response
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
        self._timeUnits = 'ms'
        self._tmul = 1.0

        self.nTrials = np.size(self.Response)
        self.fixExtraTrial()
        self.refTime = self.StartTime[0] # use this as start of the task?        
 
    def properties(self):
        """Print all the properties in this class."""
        [print((k, type(getattr(self, k)), np.shape(getattr(self, k)))) for k in dir(self) if '_' not in k and 'method' not in k]

    def fixExtraTrial(self):
        """
        mkturk adds an extra entry to variables set up before the trial is finished.
        This function discards that extra entry.
        """
        flds = ['CorrectItem', 'FixationGridIndex', 'Sample', 'StartTime', 'Test']
        for fld in flds:
            if self.nTrials+1 in np.shape(getattr(self, fld)):
                setattr(self, fld, getattr(self, fld)[:-1])
       
    @property
    def timeUnits(self):
        """Units to be used when dealing with time. (s, ms)"""
        return self._timeUnits

    @timeUnits.setter
    def timeUnits(self, thisUnits):
        """Set the time units. Default is ms."""
        assert thisUnits in ['s', 'ms']
        self._timeUnits = thisUnits
        if thisUnits == 'ms':
            self._tmul = 1.0
        elif thisUnits == 's':
            self._tmul = 1/1000
        elif thisUnits == 'min':
            self._tmul = 1/(1000*60)
        elif thisUnits == 'hr':
            self._tmul = 1/(1000*60*60)

    @property
    def validTrials(self):
        """
        Boolean of shape (nTrials,).
        False if the trial timed out.
        """
        return self.Response != -1

    @property
    def accuracy(self):
        """Accuracy within session across valid trials."""
        return np.mean(self.Response[self.validTrials] == self.CorrectItem[self.validTrials])

    @property
    def rts(self):
        """Response times (includes invalid trials)."""
        return self.ResponseXYT[:, -1] - self.FixationXYT[:, -1]
    
    @property
    def rts_valid(self):
        """Returns response times (only valid trials)."""
        return self.rts[self.validTrials]

    @property
    def rt(self):
        """Mean Response time across valid trials."""
        return np.mean(self.rts[self.validTrials])


beh = [behSession(file, behAll[file]) for file in behAll]

#%%
import matplotlib.pyplot as plt

h = plt.figure(figsize=(16, 10))
nRows = 4
nCols = 2
allAx = h.subplots(nRows, nCols, sharey=False, sharex=True)
for sessionCount in range(np.size(beh)):
    rowCount = sessionCount // nCols
    colCount = sessionCount % nCols
    #hIm = allAx[rowCount][colCount].plot(np.sort(beh[sessionCount].rts_valid))
    hIm = allAx[rowCount][colCount].hist(beh[sessionCount].rts_valid, bins=np.linspace(0, 2000, 40), density=True)
    allAx[rowCount][colCount].set_title(beh[sessionCount].fName)
    
plt.xlim(0, 2000)
h.suptitle('Response times')
