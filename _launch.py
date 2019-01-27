### This code does some package management across machines, and then loads a command into blender's workspace
import os
import subprocess

## Package management (need to add exception handling here)
# Get list of installed packages
proc = subprocess.Popen('pip freeze', stdout=subprocess.PIPE, shell=True)
out = proc.communicate()
currPkgs = out[0].decode("utf-8").rstrip('\n').split('\n')

# Read from requirements.txt if it is there
reqPkgs = [line.rstrip('\n') for line in open('requirements.txt')]

# If there are missing packages, ask for installation
missingPkgs = list(set(reqPkgs) - set(currPkgs))
for pkgName in missingPkgs:
    thisCmd = 'pip install ' + pkgName
    exCode = os.system(thisCmd)
    
# If some packages are not listed, ask for uninstall
extraPkgs = list(set(currPkgs) - set(reqPkgs))
for pkgName in extraPkgs:
    thisCmd = 'pip uninstall ' + pkgName
    exCode = os.system(thisCmd)

# update requirements file after install process!
os.system('pip freeze > requirements.txt')

### REMEMBER!! When you install a new package, update requirements.txt!
# Do this by typing 'pip freeze > requirements.txt' into the terminal

## Exporting commands into blender's workspace
# Use the command blender --python launch.py in the terminal to launch blender
# Then use exec(bpy.loadStr) in the blender python console
import bpy #pylint: disable=import-error
launchFileName = os.path.join(os.path.dirname(os.path.realpath(__file__)), '_launchContents.py')
bpy.loadStr = open(launchFileName).read()