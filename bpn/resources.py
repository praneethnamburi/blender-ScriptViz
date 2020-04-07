"""
Module for interfacing with resources.
e.g. skeletal system.
"""
import os

import numpy as np

import bpy #pylint: disable=import-error
import mathutils #pylint: disable=import-error

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

class CircularRig:
    """
    Easily control a camera and lights rig.
    Set the positions of the camera and lights, and animate.

    Use these properties for initializing the rig:
        theta - angle of the camera in the XY plane (in radians)
        center - center of the camera path (defined as the center of the rig)

    Example:
        c = CircularRig()
        c.theta = -np.pi/2
    """
    def __init__(self):
        self.rig_name = 'circularRig'
        if self.rig_name not in [c.name for c in bpy.data.collections]:
            load_rig(self.rig_name)
        self.key_rel_theta = -np.pi/4
        self.fill_rel_theta = np.pi/3
        self.back_rel_theta = 5*np.pi/6
        self._set_lights_theta()
        self.key_rel_loc = np.array((0, 0, 0.15))
        self.fill_rel_loc = np.array((0, 0, 0.15))
        self.back_rel_loc = np.array((0, 0, 1))

    @property
    def theta(self):
        """Camera angle in the XY plane."""
        return self.offset2theta(bpy.data.objects['Container_camera'].constraints[0].offset_factor)

    @theta.setter
    def theta(self, new_theta):
        self.set_theta('camera', new_theta)
        self._set_lights_theta()

    def _set_lights_theta(self, new_theta=None):
        if new_theta is None:
            new_theta = self.theta
        self.set_theta('key', new_theta + self.key_rel_theta)
        self.set_theta('fill', new_theta + self.fill_rel_theta)
        self.set_theta('back', new_theta + self.back_rel_theta)

    def set_theta(self, obj_name, new_theta):
        """Set angle of an object"""
        assert obj_name in ('camera', 'key', 'fill', 'back')
        if obj_name != 'camera':
            obj_name = obj_name + 'Light'
        bpy.data.objects['Container_'+obj_name].constraints[0].offset_factor = self.theta2offset(new_theta%(2*np.pi))
        
    @property
    def center(self):
        """Center of the rig. Defined as the center of the camera path."""
        return np.array(bpy.data.objects['BezierCircle_camera'].location)

    @center.setter
    def center(self, new_center):
        new_center = np.array(new_center)
        assert len(new_center) == 3
        bpy.data.objects['BezierCircle_camera'].location = mathutils.Vector(new_center)
        self._set_loc()
    
    def _set_loc(self):
        bpy.data.objects['BezierCircle_keyLight'].location = mathutils.Vector(self.center + self.key_rel_loc)
        bpy.data.objects['BezierCircle_fillLight'].location = mathutils.Vector(self.center + self.fill_rel_loc)
        bpy.data.objects['BezierCircle_backLight'].location = mathutils.Vector(self.center + self.back_rel_loc)

    @property
    def target(self):
        """Location of the object that the camera and lights point to."""
        return np.array(bpy.data.objects['Target'].location)

    @target.setter
    def target(self, new_target):
        new_target = np.array(new_target)
        assert len(new_target) == 3
        bpy.data.objects['Target'].location = mathutils.Vector(new_target)

    @property
    def fov(self):
        """Horizontal field of view of the camera."""
        return 2*np.arctan(0.5*bpy.data.cameras['Main'].sensor_width/bpy.data.cameras['Main'].lens)*180/np.pi

    @fov.setter
    def fov(self, hor_angle_deg):
        bpy.data.cameras['Main'].lens = 0.5*bpy.data.cameras['Main'].sensor_width/np.tan(hor_angle_deg*np.pi/360)

    def scale(self, scl_factor=1):
        bpy.data.objects['BezierCircle_camera'].scale *= scl_factor
        bpy.data.objects['BezierCircle_keyLight'].scale *= scl_factor
        bpy.data.objects['BezierCircle_fillLight'].scale *= scl_factor
        bpy.data.objects['BezierCircle_backLight'].scale *= scl_factor

    def key(self, frame=None, targ='lens', value=None):
        """Camera and target keyframe insertion."""
        if frame is None:
            frame = bpy.context.scene.frame_current
        else:
            assert isinstance(frame, int)
        if value is None:
            value = bpy.data.cameras['Main'].lens if targ in ('lens', 'fov') else value 
            value = self.target if targ == 'target' else value
            value = self.theta if targ == 'camera_angle' else value

        if targ in ('lens', 'fov'):
            if targ == 'lens':
                bpy.data.cameras['Main'].lens = value
            else:
                self.fov = value
            bpy.data.cameras['Main'].keyframe_insert(data_path='lens', frame=frame)
        
        if targ == 'target':
            self.target = value
            bpy.data.objects['Target'].keyframe_insert(data_path='location', frame=frame)
        
        if targ == 'camera_angle':
            self.set_theta('camera', value)
            bpy.data.objects['Container_camera'].constraints[0].keyframe_insert('offset_factor', frame=frame)

    @staticmethod
    def theta2offset(theta):
        """theta in radians"""
        return (0.75 - theta/(2*np.pi))%1.0
    
    @staticmethod
    def offset2theta(offset):
        """offset sets relative rig locations"""
        assert 0 <= offset <= 1
        return (3*np.pi/2 - 2*np.pi*offset)%(2*np.pi)
