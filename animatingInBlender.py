import bpy #pylint: disable=import-error

positions = (0,0,0), (-5,1,1), (1,3,3), (4,3,6), (4,10,6)

start_pos = (1,10,1)

ob = bpy.data.objects["Sphere"]

frame_num = 0

for position in positions:
    bpy.context.scene.frame_set(frame_num)
    ob.location = position
    ob.keyframe_insert(data_path="location", index=-1)
    frame_num += 20