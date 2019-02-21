"""
Analyze mkturk behavior data.

Assumptions:
 - All images in the image database are in the imgroot (imagebags) folder
 - There can be multiple copies of that image
 - Image database (created in this file) assigns image copies to different objects
 - Unique image level ID is given by mkturkHash property of the image object
"""

import datetime
import json
import os
import pickle
import re
import subprocess
import sys
import numpy as np

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '.'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

import pntools as my

PATH_LEVELS = ['dbxroot', 'imgroot', 'dataset', 'noun', 'mesh', 'variation'] # mkturk resource organization
TF_NAMES = ['ty', 'tz', 'rxy', 'rxz', 'ryz', 'scale'] # transform names
DBX_AUTH = os.path.join(DEV_ROOT, '_auth/mkturk_dropbox.json') # path to dropbox authentication file
CACHE_PATH = os.path.join(DEV_ROOT, '_temp')
DBX_PATH_IMGDB = '/mkturkfiles/imagebags/objectome' # path to the image databse

#pylint:disable=no-member

def fetch(agent='Sausage', startDate='20190201', endDate='20190205', docTypes=None, cachePath=CACHE_PATH, dbxdl=True, returnDict=True):
    """
    Fetch data from firestore and dropbox.
    
    :param agent: Name of the agent
    :param startDate: yyyymmdd
    :param endDate: yyyymmdd
    :param docTypes: list. possible values are ['task', 'images'] <default>, ['task'], or ['images']
    :param cachePath: Path to local cache. Directory must exist.
    :param dbxdl: bool. Download text files in the query from dropbox if set to true.
    :param returnDict: bool. Return a list of dictionaries if set to true, or return a list of mkturk.session objects if set to false
    :returns: Returns a list of dictionaries/mkturk.session objects, one for each firestore file.
    """
    behDl = {}
    outFiles = []
    if not docTypes:
        docTypes = ['task', 'images']
    for docType in docTypes:
        outFile = f'{cachePath}/{agent}_{docType}_{startDate}to{endDate}.json'
        outFiles.append(outFile)

        # download data from firestore to the local cache if there is no cached copy
        if not os.path.exists(os.path.realpath(outFile)):
            proc = subprocess.run(f'node mkturk_getData.js -a {agent} -t {docType} -s {startDate} -e {endDate} -o {outFile}', encoding='utf-8', stdout=subprocess.PIPE) # --no-print to suppress output
            if proc.returncode != 0:
                raise RuntimeError('Data download failed!')
        
        # read from local cache
        behDl[docType] = json.loads(open(outFile).read())

    behFire = []
    if 'task' in docTypes and 'images' in docTypes:
        for file_t, file_i in zip(behDl['task'], behDl['images']):
            b, bi = behDl['task'][file_t], behDl['images'][file_i]
            commonAttr = list(set(b.keys()).intersection(set(bi.keys())) - set(['Doctype']))
            for attr in commonAttr:
                assert b[attr] == bi[attr]
            behFire.append({**b, **bi})
    elif len(docTypes) == 1:
        for file_ti in behDl[docTypes[0]]:
            b = behDl[docTypes[0]][file_ti]
            behFire.append({**b})

    if not dbxdl:
        if returnDict:
            return behFire
        else:
            return [session(k) for k in behFire]

    # download from dropbox only if docTypes has both 'task' and 'images'?
    outFile = f'{cachePath}/{agent}_{startDate}to{endDate}.dbxdl'
    dlTime = datetime.datetime.now().isoformat()
    outFiles.append(outFile)
    if not os.path.exists(os.path.realpath(outFile)):
        import dropbox
        dbx = dropbox.Dropbox(json.loads(open(DBX_AUTH).read())['DBX_MKTURK_TOKEN'])
        behDbx = [json.loads(dbx.files_download(file_['DataFileName'])[1].content) for file_ in behFire]
        # combine data from firestore and dropbox
        beh = [{k: v for filepart in [fireFile]+dbxFile for k, v in filepart.items()} for fireFile, dbxFile in zip(behFire, behDbx)]
        with open(outFile, 'wb') as f:
            pickle.dump([beh, dlTime], f)
        print("Saved query data at: ", outFile)

    with open(outFile, 'rb') as f:
        beh, dlTime = pickle.load(f)
    if returnDict:
        return beh
    else:
        return [session(k) for k in beh]

class SessionGroupOps(my.Tracker):
    """
    Operations to be performed across sessions.
    Meant to decorate the class session.

    merge [take multiple session objects and turn it into one]
    merge_days
    """
    pass

@SessionGroupOps
@my.AddMethods([my.cm.properties])
class session:
    """
    Encapsulate one session of mkturk behavior data from firestore.
    
    :param b: dictionary
    :param bi: json import of the corresponding _images file
        load behavior using:
            b = json.loads(open(fName).read())
        If you're using firestore and downloaded a series of behavioral
        files into one json object, then you can make a list of session
        objects using:
            beh = [session(file, behAll[file]) for file in behAll]
        Note that time is in ms
        
    List of variables and their description:
        https://github.com/dicarlolab/mkturk/tree/master/public

    TODO: If only the file name is given, then get it from the database directly
    TODO: Method to create trial objects
    TODO: Time unit management
    """
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

@my.AddMethods([my.cm.properties])
class img:
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

class ImgGroupOps(my.Tracker):
    """
    Group operations on mkturk image objects.
    """
    def __init__(self, clsToTrack):
        """Meta data of all images."""
        super().__init__(clsToTrack)
        self.load()
    
    def load(self):
        """
        Creates objects from all .png files in the DBX_PATH_IMGDB folder.
        """
        imgMeta, _ = my.dbxmeta(dbxAuth=DBX_AUTH, dbxPath=DBX_PATH_IMGDB, cachePath=CACHE_PATH)
        self.all_ = [img(entry) for entry in imgMeta if '.png' in entry.name]
        imgDb = {entry.id_desc:entry for entry in self.all_}
        # fails if mkturk.img.id_desc is not unique for all images!
        assert np.shape(list(imgDb.keys())) == np.shape(self.all_)

img = ImgGroupOps(img)
