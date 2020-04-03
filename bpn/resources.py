"""
Module for interfacing with resources.
e.g. skeletal system.
"""
import os

import bpy #pylint: disable=import-error

from . import new, utils

SKELETON = "D:\\Dropbox (MIT)\\Anatomy\\Workspace\\Ultimate_Human_Anatomy_Rigged_Blend_2-81\\skeletalSystem_originAtCenter_xForward.blend"
RIGS = "D:\\Dropbox (Personal)\\Animation\\Rigs.blend"

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
    
    col = new.collection(coll_name)
    for obj in data_to.objects:
        if obj is not None:
            col.objects.link(obj)
    
    return {bone:utils.get(bone) for bone in bones}

def load_rig(rig='circularRig'):
    """
    Camera and lighting system that were manually created before.
    Automate this!
    """
    assert os.path.isfile(RIGS)
    with bpy.data.libraries.load(RIGS) as (data_from, data_to):
        data_to.collections = [name for name in data_from.collections if name in rig]
    for col in data_to.collections:
        if col is not None:
            bpy.context.scene.collection.children.link(col)
