"""
Human anatomy model manipulation
"""

import os

import bpy #pylint: disable=import-error

import bpn

# ULTIMATE_HUMAN_ANATOMY = "D:\\Dropbox (MIT)\\Anatomy\\Workspace\\Ultimate_Human_Anatomy_Rigged_Blend_2-81\\skeletalSystem_originAtCenter_xForward.blend"
SKELETON = "C:\\Dropbox (MIT)\\Anatomy\\Workspace\\Ultimate_Human_Anatomy_Rigged_Blend_2-81\\skeletalSystem_originAtCenter_xForward.blend"

def load(obj_list=None, coll_name='Bones', fname=None):
    """
    Load anatomical meshes from the SKELETON file.
    :param obj_list: (list) list of strings specifying the names of bones.
    :param coll_name: (string) target collection to put the bones into.
    """
    if fname is None:
        fname = SKELETON

    assert os.path.exists(fname)
    if obj_list is None:
        obj_list = ['Humerus_R', 'Scapula_R', 'Clavicle_R', 'Radius_R', 'Ulna_R']
    with bpy.data.libraries.load(fname) as (data_from, data_to):
        data_to.objects = [name for name in data_from.objects if name in obj_list]
    
    ret = {}
    for obj in data_to.objects:
        if obj is not None:
            obj = bpn.utils.enhance(obj)
            ret[obj.name] = obj
            obj.to_coll(coll_name)
    
    return ret

def load_coll(coll_name='Skeletal_Sys', fname=None):
    """
    Load anatomical meshes from the SKELETON file.
    :param obj_list: (list) list of strings specifying the names of bones.
    :param coll_name: (string) target collection to put the bones into.
    """
    if fname is None:
        fname = SKELETON
    assert os.path.exists(fname)
    with bpy.data.libraries.load(fname) as (data_from, data_to):
        data_to.collections = [name for name in data_from.collections if name in coll_name]
    
    for coll in data_to.collections:
        bpy.context.scene.collection.children.link(coll)
