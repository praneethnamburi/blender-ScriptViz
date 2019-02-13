"""
Analyze mkturk behavior data.

Assumptions:
 - All images in the image database are in the imgroot (imagebags) folder
 - There can be multiple copies of that image
 - Image database (created in this file) assigns image copies to different objects
 - Unique image level ID is given by mkturkHash property of the image object
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

PATH_LEVELS = ['dbxroot', 'imgroot', 'dataset', 'noun', 'mesh', 'variation']
TF_NAMES = ['ty', 'tz', 'rxy', 'rxz', 'ryz', 'scale']
DBX_AUTH = './_auth/mkturk_dropbox.json'
DBX_PATH_IMGDB = '/mkturkfiles/imagebags/objectome'
CACHE_PATH = './_temp'

def fetch(agent='Sausage', startDate='20190201', endDate='20190205', docTypes=None, cachePath='./_temp'):
    """
    Fetch data from firestore/local cache.
    
    :param agent: Name of the agent
    :param startDate: yyyymmdd
    :param endDate: yyyymmdd
    :param docTypes: list. possible values are ['task', 'images'] <default>, ['task'], or ['images']
    :param cachePath: Path to local cache. Directory must exist.
    :returns: Returns a list of dictionaries
    """
    _behDl = {}
    outFiles = []
    if not docTypes:
        docTypes = ['task', 'images']
    for docType in docTypes:
        outFile = f'{cachePath}/{agent}_{docType}_{startDate}to{endDate}.json'
        outFiles.append('outFile')

        # download data from firestore to the local cache if there is no cached copy
        if not os.path.exists(os.path.realpath(outFile)):
            proc = subprocess.run(f'node mkturkBeh_getData.js -a {agent} -t {docType} -s {startDate} -e {endDate} -o {outFile}', encoding='utf-8', stdout=subprocess.PIPE) # --no-print to suppress output
            if proc.returncode != 0:
                raise RuntimeError('Data download failed!')
        
        # read from local cache
        _behDl[docType] = json.loads(open(outFile).read())

    _behAll = []
    if 'task' in docTypes and 'images' in docTypes:
        for file_t, file_i in zip(_behDl['task'], _behDl['images']):
            b, bi = _behDl['task'][file_t], _behDl['images'][file_i]
            commonAttr = list(set(b.keys()).intersection(set(bi.keys())) - set(['Doctype']))
            for attr in commonAttr:
                assert b[attr] == bi[attr]
            _behAll.append({**b, **bi})
    elif len(docTypes) == 1:
        for file_ti in _behDl[docTypes[0]]:
            b = _behDl[docTypes[0]][file_ti]
            _behAll.append({**b})
    return _behAll, outFiles

class behSession:
    """
    Encapsulate one session of mkturk behavior data from firestore.
    
    :param b: dictionary
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

    behSession.properties() is a useful method!
    TODO: If only the file name is given, then get it from the database directly
    TODO: Method to create trial objects
    TODO: Time unit management
    """
    # pylint: disable=no-member
    def __init__(self, b):
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
    def sampleObject_id_desc(self):
        """
        Trial-wise transformation string for the sample object.

        Note:
            dataset = SamplePathLevels[trialIdx, 2]
            noun = SamplePathLevels[trialIdx, 3]
            mesh = SamplePathLevels[trialIdx, 4]
            variation = SamplePathLevels[trialIdx, 5]
            TODO: change how this is computed based on whether the data is from firestore or dropbox. Currently only works for firestore.
        """
        SamplePathLevels = np.array([k.rstrip('/').lstrip('/').split('/') for k in self.ImageBagsSample])
        trialIdx = self.SampleBagIdx[self.Sample]

        id_desc = []
        for trialCount in range(self.nTrials):
            thisStr = ''
            for level in PATH_LEVELS[1:]: # skips dropbox root - all images should be in the imgroot (imagebags) folder
                thisStr += '_' + SamplePathLevels[trialIdx[trialCount], PATH_LEVELS.index(level)]
            for tfName in TF_NAMES:
                thisStr += '_' + tfName.rstrip('cale')  + str(getattr(self, 'SampleObject'+tfName.capitalize())[trialCount])
            id_desc.append(thisStr)
        return id_desc

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
        return PATH_LEVELS

    @property
    def dbxProperties(self):
        """Dropbox metadata from dropbox.files.metadata object."""
        return ['content_hash', 'size', 'name', 'path_display']

    @property
    def transformNames(self):
        """Transforms performed on the object to make the 2d image."""
        return [k.rstrip('cale') for k in  TF_NAMES]

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
        return f'ty{self.ty}_tz{self.tz}_rxy{self.rxy}_rxz{self.rxz}_ryz{self.ryz}_s{self.s}'

    @property
    def fname_rec(self):
        """Reconstructed file name of the mkturk image. Use the name or path_display attributes to get the file name."""
        return f'{self.dataset}_{self.noun}_{self.mkturkHash}_{self.tfStr}{self.ext}'

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
        """
        Descriptive identification string for the image.
        This should be unique to the file in objectome.
        Verification:
        Size of the number of png files in your database:
            allImgs = [mkturkImg(entry) for entry in imgMeta if '.png' in entry.name]
        should be equal to:
            np.shape(np.unique([entry.id_desc for entry in allImgs]))
        or,
            imgDb = {entry.id_desc:entry for entry in allImgs}
            np.shape(list(imgDb.keys()))
        """
        return f'_{self.imgroot}_{self.dataset}_{self.noun}_{self.mesh}_{self.variation}_{self.tfStr}'


class imgDb:
    """Create the image database."""
    def __init__(self):
        imgMeta, _ = my.dbxmeta(dbxAuth=DBX_AUTH, dbxPath=DBX_PATH_IMGDB, cachePath=CACHE_PATH)
        allImgs = [mkturkImg(entry) for entry in imgMeta if '.png' in entry.name]
        self.imgDb = {entry.id_desc:entry for entry in allImgs}
        assert np.shape(list(self.imgDb.keys())) == np.shape(allImgs) # fails if mkturkImg.id_desc is not unique for all images!
    def __call__(self):
        return self.imgDb

#%% Fetch behavior sessions from firestore only
behAll, _ = fetch(agent='Sausage', startDate='20190201', endDate='20190205', docTypes=['task', 'images'], cachePath=CACHE_PATH)
beh = [behSession(_file) for _file in behAll]
beh = [k for k in beh if k.nTrials > 10]

#%% Fetch behavior sessions from firestore and dropbox
import dropbox
dbx = dropbox.Dropbox(json.loads(open(DBX_AUTH).read())['DBX_MKTURK_TOKEN'])

behAll, _ = fetch(agent='Sausage', startDate='20190201', endDate='20190205', docTypes=['task'], cachePath=CACHE_PATH)
behDbx = [json.loads(dbx.files_download(_file['DataFileName'])[1].content) for _file in behAll]
behDbx = [behSession({k: v for filepart in file for k, v in filepart.items()}) for file in behDbx]

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
behDbx = json.loads(open('./_temp/tempSausage.txt').read())
behDbx = {**behDbx[0], **behDbx[1], **behDbx[2], **behDbx[3], **behDbx[4]}
behDbx['Ordered_Samplebag_Filenames'][behDbx['Sample'][0]]
#%%
['displayEnvironment', 'presentedStimuli', 'experimentalParams', 'params text file', 'TRIAL']


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
beh[1].SampleHashesPrefix
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
