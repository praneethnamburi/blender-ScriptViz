"""
Module for interfacing with resources.
e.g. skeletal system.
"""
import os

import bpy #pylint: disable=import-error

from . import utils

SKELETON = "D:\\Dropbox (MIT)\\Anatomy\\Workspace\\Ultimate_Human_Anatomy_Rigged_Blend_2-81\\skeletalSystem_originAtCenter_xForward.blend"

def load_bones(bones=None, coll_name='Bones'):
    """
    Load meshes of bones from the SKELETON file.
    :param bones: (list) list of strings specifying the names of bones.
    :param coll_name: (string) target collection to put the bones into.
    """
    assert os.path.exists(SKELETON)
    if bones is None:
        bones = ['Humerus_R', 'Scapula_R', 'Clavicle_R', 'Radius_R', 'Ulna_R']
    with bpy.data.libraries.load(SKELETON) as (data_from, data_to):
        data_to.objects = [name for name in data_from.objects if name in bones]
    
    ret = {}
    for obj in data_to.objects:
        if obj is not None:
            obj = utils.enhance(obj)
            ret[obj.name] = obj
            obj.to_coll(coll_name)
    
    return ret
