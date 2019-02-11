"""
Analyze mkturk behavior data.
"""
#%%
#pylint: disable=fixme
import json
import os
import re
import subprocess
import numpy as np

# import sys
# if os.path.dirname(os.path.realpath(__file__)) not in sys.path:
#     sys.path.append(os.path.dirname(os.path.realpath(__file__)))

import pnTools as my

def fetch(agent='Sausage', startDate='20190201', endDate='20190205', docTypes=None, cachePath='./_temp'):
    """Fetch data from firestore/local cache."""
    _behAll = {}
    outFiles = []
    if not docTypes:
        docTypes = ['task', 'images']
    for docType in docTypes:
        outFile = f'{cachePath}/{agent}_{docType}_{startDate}to{endDate}.json'
        outFiles.append('outFile')

        # get the data from firestore if there is no cached copy
        if not os.path.exists(os.path.realpath(outFile)):
            proc = subprocess.run(f'node mkturkBeh_getData.js -a {agent} -t {docType} -s {startDate} -e {endDate} -o {outFile}', encoding='utf-8', stdout=subprocess.PIPE) # --no-print to suppress output
            if proc.returncode != 0:
                raise RuntimeError('Data download failed!')
        
        # read from local cache
        _behAll[docType] = json.loads(open(outFile).read())
        # TODO: Do an extra assertion here to match task and image files
    return _behAll, outFiles

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
    TODO: Method to create trial objects
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
        flds = ['CorrectItem', 'FixationGridIndex', 'Sample', 'StartTime', 'Test',\
                'SampleObjectRxy', 'SampleObjectRxz', 'SampleObjectRyz', 'SampleObjectScale', 'SampleObjectTy', 'SampleObjectTz',\
                'TestObjectRxy', 'TestObjectRxz', 'TestObjectRyz', 'TestObjectScale', 'TestObjectTy', 'TestObjectTz']
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

    @property
    def sampleObject_tfStr(self):
        """Trial-wise transformation string for the sample object."""
        tfStr = []
        tfNames = ['ty', 'tz', 'rxy', 'rxz', 'ryz', 'scale']
        for trialCount in range(self.nTrials):
            thisStr = ''
            for tfName in tfNames:
                thisStr += '_' + tfName.rstrip('cale')  + str(getattr(self, 'SampleObject'+tfName.capitalize())[trialCount])
            tfStr.append(thisStr)
        return tfStr

class mkturkImg:
    """
    Encapsulate an image stimulus.
    
    :param dbxEntry: Dropbox metadata. see dbxmeta().
    """
    # pylint: disable=no-member
    def __init__(self, dbxEntry):
        # import dropbox attributes (see dbxProperties)
        for attr in self.dbxProperties:
            setattr(self, attr, getattr(dbxEntry, attr))

        # parse the path
        pathSpl = np.array(self.path_display.split('/'))[1:]
        assert np.size(pathSpl) == np.size(self.pathLevels)+1
        for lvl, pathEntry in zip(self.pathLevels, pathSpl[:-1]):
            setattr(self, lvl, pathEntry)
        
        # parse the name
        _, self.ext = os.path.splitext(self.name)
        nameSplit = self.name.replace(self.ext, '').split('_')
        self.mkturkHash = nameSplit[2]
        if len(nameSplit) == 3:
            self.noTransform = True
            self._setDefaultTransform()
        else:
            self.noTransform = False
        for transform in nameSplit[3:]:
            thisTf = re.match(r"([a-z]+)([0-9\.\-]+)", transform).groups()
            setattr(self, thisTf[0], thisTf[1])

        # remove parsed dropbox attributes?

    @property
    def pathLevels(self):
        """Meaning of each level in dropbox path."""
        return ['dbxroot', 'imgroot', 'dataset', 'noun', 'mesh', 'variation']

    @property
    def dbxProperties(self):
        """Dropbox metadata from dropbox.files.metadata object."""
        return ['content_hash', 'size', 'name', 'path_display']

    @property
    def transformNames(self):
        """Transforms performed on the object to make the 2d image."""
        return ['ty', 'tz', 'rxy', 'rxz', 'ryz', 's']

    @property
    def defaultTransform(self):
        """Transformation values when no transform is performed."""
        return [0, 0, 0, 0, 0, 1]

    def _setDefaultTransform(self):
        for tf, tfVal in zip(self.transformNames, self.defaultTransform):
            setattr(self, tf, tfVal)

    @property
    def transform(self):
        """Transform of the 3d object before 2d projection."""
        return [getattr(self, tf) for tf in self.transformNames]

    @property
    def fpath_rec(self):
        """Reconstructed file path of the mkturk image. Use path_display to get the full path and file name."""
        return f'/{self.dbxroot}/{self.imgroot}/{self.dataset}/{self.noun}/{self.mesh}/{self.variation}'

    @property
    def tfStr(self):
        """Transformation string."""
        return f'_ty{self.ty}_tz{self.tz}_rxy{self.rxy}_rxz{self.rxz}_ryz{self.ryz}_s{self.s}'

    @property
    def fname_rec(self):
        """Reconstructed file name of the mkturk image. Use the name or path_display attributes to get the file name."""
        return f'{self.dataset}_{self.noun}_{self.mkturkHash}{self.tfStr}{self.ext}'

    @property
    def id(self):
        """
        ID of an object is the mkturk hash.
        Unique to an image. 
        Copies of the image in different directories will have the same id.
        """
        return self.mkturkHash

    @property
    def id_desc(self):
        """Descriptive identification string for the image."""
        return f'{self.dataset}_{self.noun}{self.tfStr}'


behAll, _ = fetch(agent='Sausage', startDate='20190201', endDate='20190205', docTypes=['task', 'images'], cachePath='./_temp')
beh = [behSession(behAll['task'][file_t], behAll['images'][file_i]) for file_t, file_i in zip(behAll['task'], behAll['images'])]
beh = [k for k in beh if k.nTrials > 10]

imgMeta, _ = my.dbxmeta(dbxAuth='./_auth/mkturk_dropbox.json', dbxPath='/mkturkfiles/imagebags/objectome', cachePath='./_temp')
allImgs = [mkturkImg(entry) for entry in imgMeta if '.png' in entry.name]
imgDb = {}
for entry in allImgs:
    # overwrites duplicates. use this only for the image and properties, not for the path.
    imgDb[entry.id] = entry

#%%
desc2hash = {}
for entry in allImgs:
    desc2hash[entry.id_desc] = entry.mkturkHash

tfStr_all = np.array([k.fname_rec for k in allImgs])
objHash = [desc2hash[k] for k in beh[1].sampleObject_tfStr]
np.shape(objHash)

#%%
np.shape(np.unique(np.array([img.id for img in allImgs])))
np.shape(list(desc2hash.keys()))
#%%
[beh[1].SampleObjects, beh[1].SampleBagNames, beh[1].SampleImageSetDir]
beh[1].properties()

beh[1].ImageBagsSample
# noun = beh[1].SampleNouns[beh[1].SampleBagIdx[beh[1].Sample]]
# dataset = beh[1].SampleImageSetDir.rstrip('/').split('/')[-1]

#%%
sampleBags = beh[1].ImageBagsSample[beh[1].SampleBagIdx[beh[1].Sample]]
np.shape(np.array([k.rstrip('/').split('/')[1:] for k in sampleBags]))


#%%
tmp1 = allImgs[0]
beh[0].properties()
vars(beh[0])
np.shape(beh[0].SampleHashesPrefix)
#%%
np.unique(beh[1].Test[:, 1])
np.where(beh[5].SampleObjectTy == 0)

#%%
allHash = [im.mkturkHash for im in allImgs]
uniqueHash = np.unique(allHash)
hashFreq = {}
for entry in uniqueHash:
    hashFreq[entry] = 0

for entry in allHash:
    hashFreq[entry] += 1

hashFreq = np.array(list(hashFreq.values()))
np.unique(hashFreq)

#%%
hashFreq['019fc5e03e97be0877eea98f7e53bf8cd5615fe0']
dupEntry = [k for k in allImgs if k.mkturkHash == '019fc5e03e97be0877eea98f7e53bf8cd5615fe0']
[k.fpath for k in dupEntry]

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
