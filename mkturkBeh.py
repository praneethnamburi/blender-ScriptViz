"""
Analyze mkturk behavior data.
"""
#pylint: disable=fixme

#%%
import json
import os
import subprocess
import numpy as np

agent = 'Sausage'
docTypes = ['task', 'images']
startDate = '20190201'
endDate = '20190205'
outFiles = []
behAll = {}
for docType in docTypes:
    outFile = f'./_temp/{agent}_{docType}_{startDate}to{endDate}.json'
    outFiles.append('outFile')

    # get the data from firestore if there is no cached copy
    if not os.path.exists(os.path.realpath(outFile)):
        proc = subprocess.run(f'node mkturkBeh_getData.js -a {agent} -t {docType} -s {startDate} -e {endDate} -o {outFile}', encoding='utf-8', stdout=subprocess.PIPE) # --no-print to suppress output
        if proc.returncode != 0:
            raise RuntimeError('Data download failed!')
    behAll[docType] = json.loads(open(outFile).read()) # download behavior
    # TODO: Do an extra assertion here

class behSession:
    """
    Encapsulate one session of mkturk behavior data.
    
    :param b: json import of the _task file
    :param bi: json import of the corresponding _images file
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
    TODO: Time unit management
    """
    # pylint: disable=no-member
    def __init__(self, b, bi):
        # The common attribues should have the same values
        commonAttr = list(set(b.keys()).intersection(set(bi.keys())) - set(['Doctype']))
        for attr in commonAttr:
            assert b[attr] == bi[attr]

        b = {**b, **bi}
        for attr in b:
            if attr == 'Doctype':
                continue
            elif isinstance(b[attr], list):
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
        #pylint:disable=expression-not-assigned
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
    def correctTrials(self):
        """
        Trials where the monkey chose the correct item. 
        Excludes invalid trials because CorrectItem can only be 0 or 1.
        """
        return self.Response == self.CorrectItem

    @property
    def accuracy(self):
        """Accuracy within session across valid trials."""
        return np.mean(self.correctTrials)

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

beh = [behSession(behAll['task'][file_t], behAll['images'][file_i]) for file_t, file_i in zip(behAll['task'], behAll['images'])]
beh = [k for k in beh if k.nTrials > 10]

#%%



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