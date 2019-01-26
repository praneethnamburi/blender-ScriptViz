import sys
import glob

import bpy #pylint: disable=import-error

import pnTools as my
import bpnModule as bpn

@my.checkIfOutputExists
def marmosetAtlasPath(src='bma'):
    if src=='bma':
        if sys.platform == 'linux':
            fPath = "/media/praneeth/Reservoir/GDrive Columbia/issalab_data/Marmoset brain/Woodward segmentation/meshes/"
        else:
            fPath = "D:\\GDrive Columbia\\issalab_data\\Marmoset brain\\Woodward segmentation\\meshes"
    return fPath

@my.baseNames
@my.checkIfOutputExists
def getMshNames(fPath=None, searchStr='*smooth*.stl'):
    if fPath is None:
        # doing it this way because the module will not load if the brain atlas does not exist
        fPath = marmosetAtlasPath()
    mshNames = glob.glob(fPath + searchStr)
    return mshNames

## Blender usefulness exercise #3 - importing marmoset brain meshes
@bpn.reportDelta
def loadSTL(fPath=None, searchStr='*smooth*.stl', collName = 'Collection'):
    if fPath is None:
        fPath = marmosetAtlasPath()
    fNames=getMshNames(fPath, searchStr)
    for fName in fNames:
        bpy.ops.import_mesh.stl(filepath=my.getFileName_full(fPath, fName))

## make a blender decorator to put imports in a specified collection!!