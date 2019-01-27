### Use the command blender --python launch.py in the terminal to launch blender
### Then use exec(bpy.loadStr) in the blender python console
import bpy #pylint: disable=import-error
import os

launchFileName = os.path.join(os.path.dirname(os.path.realpath(__file__)), '_launchContents.py')
bpy.loadStr = open(launchFileName).read()
os.system('pip freeze > requirements.txt')