"""
Loading and saving
"""
import os
import errno

import bpy #pylint: disable=import-error

from .env import ReportDelta

### Input-output functions
@ReportDelta
def loadSTL(files):
    """
    Load STL files from disk into a blender scene.
    
    :param files: list. Full file paths.
    :param collection: str. Blender collection name to load the STL into.
    :returns: report of scene change

    Recommended use:
        Instead of directly using this function, use 
        p = bpn.Msh(stl=fname, name='mySTL', coll_name='myColl')
    """
    if isinstance(files, str):
        files = [files]
    for f in files:
        if not os.path.exists(f):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), f)
        bpy.ops.import_mesh.stl(filepath=f)
