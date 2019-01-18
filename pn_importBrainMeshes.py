import os
import errno
#import bpy (always give bpy as input to the functions! you need the one from the other workspace)

def getFileName_full(fPath, fName):
    fullName = os.path.join(os.path.normpath(fPath), fName)
    if not os.path.exists(fullName):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), fullName)
    return fullName

def myImportFunc(thisbpy, fPath = "D:\\GDrive Columbia\\issalab_data\\Marmoset brain\\Woodward segmentation\\meshes", fName = "bma-1-region_seg_24.stl"):
    thisbpy.ops.import_mesh.stl(filepath=getFileName_full(fPath, fName))