"""
Module for interfacing with resources.
e.g. skeletal system.
"""
import os

import numpy as np

import bpy #pylint: disable=import-error

from . import new, utils, core, env

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
    
    for obj in data_to.objects:
        if obj is not None:
            utils.get(obj.name).to_coll(coll_name)
    
    return {bone:utils.get(bone) for bone in bones}

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
    def __init__(self, rig_name='CircularRig', size=0.15):
        assert not env.Props().get(rig_name)    
        self.rig_name = rig_name
        self.size = size
        
        self.targ = new.empty('target', 'SPHERE', size=0.25, coll_name=self.rig_name)
        self.targ.scl = size

        cam = core.Thing('Camera', 'Camera')
        self.camera = CircularRig.ObjectOnCircle(cam, self.rig_name, 2, self.size, self.targ)
        self.camera.scl = size

        key_light = core.Thing('Key', 'Light', 'SUN', energy=2.5, angle=0.2, color=(1., 1., 1.))
        self.key_light = CircularRig.ObjectOnCircle(key_light, self.rig_name, 2.5, self.size, self.targ)

        fill_light = core.Thing('Fill', 'Light', 'SUN', energy=0.2, angle=0.2, color=(1., 1., 1.))
        self.fill_light = CircularRig.ObjectOnCircle(fill_light, self.rig_name, 3, self.size, self.targ)

        back_light = core.Thing('Back', 'Light', 'SPOT', energy=15, spot_size=np.pi/6, spot_blend=0.15, shadow_soft_size=0.1, color=(1., 1., 1.))
        self.back_light = CircularRig.ObjectOnCircle(back_light, self.rig_name, 5, self.size, self.targ)

        self.key_light.theta = self.camera.theta - np.pi/4
        self.fill_light.theta = self.camera.theta + np.pi/3
        self.back_light.theta = self.camera.theta + 5*np.pi/6

        self.key_light.center = (0, 0, 0.15)
        self.fill_light.center = (0, 0, 0.15)
        self.back_light.center = (0, 0, 1)

    class ObjectOnCircle(core.Object):
        """
        Make an object from a 'thing' e.g. light, camera
        Put the object on a container, and make the object track a target
        :param this_thing: (core.thing, bpy.types.Camera, bpy.types.Light)
        :param coll_name: Collection name to put the thing
        :param r: (float) radius of the circle
        :param size: (float) overall 'size' of your rig
        :param targ: (core.Object, bpy.types.Object)
        """
        def __init__(self, this_thing, coll_name, path, size, targ=None):
            super().__init__(this_thing.name.lower(), this_thing, coll_name=coll_name)
            self.add_container(size=size)
            if isinstance(path, (int, float)):
                self.path = new.bezier_circle(r=path, curve_name=this_thing.name+'Path', obj_name=this_thing.name.lower()+'_path', coll_name=coll_name)
            if isinstance(path, core.Object):
                self.path = path
            self.container.follow_path(self.path)
            if targ is not None:
                self.track_to(targ)
        
        @property
        def theta(self):
            """Angle of the container object in the XY plane."""
            return self.offset2theta(self.container().constraints[0].offset_factor)
        
        @theta.setter
        def theta(self, new_theta):
            self.container().constraints[0].offset_factor = self.theta2offset(new_theta%(2*np.pi))
            bpy.context.view_layer.update()

        @property
        def center(self):
            """Location of the circular path object."""
            return self.path.loc

        @center.setter
        def center(self, new_center):
            self.path.loc = new_center
        
        @staticmethod
        def theta2offset(theta):
            """theta in radians"""
            return (0.75 - theta/(2*np.pi))%1.0
        
        @staticmethod
        def offset2theta(offset):
            """offset sets relative rig locations"""
            assert 0 <= offset <= 1
            return (3*np.pi/2 - 2*np.pi*offset)%(2*np.pi)


    @property
    def theta(self):
        """Camera angle in the XY plane."""
        return self.camera.theta

    @theta.setter
    def theta(self, new_theta):
        self.key_light.theta = new_theta + self.key_light.theta - self.camera.theta
        self.fill_light.theta = new_theta + self.fill_light.theta - self.camera.theta
        self.back_light.theta = new_theta + self.back_light.theta - self.camera.theta
        self.camera.theta = new_theta
        
    @property
    def center(self):
        """Center of the rig. Defined as the center of the camera path."""
        return self.camera.center

    @center.setter
    def center(self, new_center):
        new_center = np.array(new_center)
        assert len(new_center) == 3
        self.key_light.center = new_center + self.key_light.center - self.camera.center
        self.fill_light.center = new_center + self.fill_light.center - self.camera.center
        self.back_light.center = new_center + self.back_light.center - self.camera.center
        self.camera.center = new_center

    @property
    def target(self):
        """Location of the object that the camera and lights point to."""
        return np.array(self.targ.loc)

    @target.setter
    def target(self, new_target):
        new_target = np.array(new_target)
        assert len(new_target) == 3
        self.targ.loc = new_target

    @property
    def fov(self):
        """Horizontal field of view of the camera."""
        return 2*np.arctan(0.5*self.camera().data.sensor_width/self.camera().data.lens)*180/np.pi

    @fov.setter
    def fov(self, hor_angle_deg):
        self.camera().data.lens = 0.5*self.camera().data.sensor_width/np.tan(hor_angle_deg*np.pi/360)
        bpy.context.view_layer.update()

    def scale(self, scl_factor=1):
        """Scale the rig by scale factor in (int) scl_factor."""
        self.camera.path.scale(scl_factor)
        self.key_light.path.scale(scl_factor)
        self.fill_light.path.scale(scl_factor)
        self.back_light.path.scale(scl_factor)
        bpy.context.view_layer.update()

    def key(self, frame=None, targ='lens', value=None):
        """Camera and target keyframe insertion."""
        if frame is None:
            frame = bpy.context.scene.frame_current
        else:
            assert isinstance(frame, int)
        if value is None:
            value = self.camera().data.lens if targ in ('lens', 'fov') else value 
            value = self.target if targ == 'target' else value
            value = self.theta if targ == 'camera_angle' else value

        if targ in ('lens', 'fov'):
            if targ == 'lens':
                self.camera().data.lens = value
            else:
                self.fov = value
            self.camera().data.keyframe_insert(data_path='lens', frame=frame)
        
        if targ == 'target':
            self.target = value
            self.targ().keyframe_insert(data_path='location', frame=frame)
        
        if targ == 'camera_angle':
            self.camera.theta = value
            self.camera.container().constraints[0].keyframe_insert('offset_factor', frame=frame)
