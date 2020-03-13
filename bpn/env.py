"""
Environment control in blender
"""
import bpy #pylint: disable=import-error
# import traceback

def reset():
    """
    Reset the current scene programatically.
    Script adapted from:
    https://developer.blender.org/T47418

    This is extremely useful for clearing the scene programatically during iterative development.
    """
    # bpy.ops.wm.read_factory_settings()
    for scene in bpy.data.scenes:
        for obj in scene.objects:
            try:
                scene.objects.unlink(obj)
            except AttributeError:
                # traceback.print_exc()
                pass
    # only worry about data in the startup scene
    for bpy_data_iter in (bpy.data.objects, bpy.data.meshes, bpy.data.collections):
        # may not work for collections - blender bug
        for id_data in bpy_data_iter:
            try:
                bpy_data_iter.remove(id_data)
            except AttributeError:
                pass

def shade(shading='WIREFRAME', area='Layout'):
    """
    Set 3D viewport shading
    """
    my_areas = bpy.data.screens[area].areas
    assert shading in ['WIREFRAME', 'SOLID', 'MATERIAL', 'RENDERED']

    for area in my_areas:
        for space in area.spaces:
            if space.type == 'VIEW_3D' and area.type == 'VIEW_3D':
                space.shading.type = shading
