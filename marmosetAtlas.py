"""
Visualize and manipulate marmoset atlases
"""
import sys
import glob
import os

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
import pnTools as my
import bpn
from bpn import bpy

@my.checkIfOutputExists
def marmosetAtlasPath(src='bma'):
    """Return the marmoset atlas directory."""
    if src == 'bma':
        if sys.platform == 'linux':
            fPath = "/media/praneeth/Reservoir/GDrive Columbia/issalab_data/\
                    Marmoset brain/Woodward segmentation/meshes/"
        else:
            fPath = "D:\\Google Drive (pn2322@columbia.edu)\\issalab_data\\\
                    Marmoset brain\\Woodward segmentation\\meshes\\"
    return os.path.realpath(fPath)

@my.baseNames
@my.checkIfOutputExists
def getMshNames(fPath=marmosetAtlasPath(), searchStr='*52*.stl'):
    """Get mesh names of marmoset atlas brain matching the pattern in searchStr."""
    mshNames = glob.glob(os.path.join(fPath, searchStr))
    return mshNames

@bpn.ReportDelta
def loadSTL(fPath=None, searchStr='*smooth*.stl', collName = 'Collection'):
    """Import brain meshes into blender and report changes in output"""
    if fPath is None:
        fPath = marmosetAtlasPath()
    fNames = getMshNames(fPath, searchStr)
    for fName in fNames:
        bpy.ops.import_mesh.stl(filepath=my.getFileName_full(fPath, fName))

# TODO: make a blender decorator to put imports in a specified collection!!

# what to do if this module is run as a script
if __name__ == '__main__':
    loadSTL(searchStr='*52*.stl')
