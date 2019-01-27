### This code makes it easier to manage packages across machines when developing with blender
# Use this code by typing blender --python _requirementsCheck.py in the terminal
# I have chosen to use the VSCode extension 'run in terminal' to send this file as an argument to blender along with the file I'd like to run
# blender --python _requirementsCheck.py --python ${file}
# Improve this file by adding some checks to make sure the correct pip and python are being used!
import os
import subprocess
import sys

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from bpn import bpy

## Package management (need to add exception handling here)
# Get list of installed packages
proc = subprocess.Popen('pip freeze', stdout=subprocess.PIPE, shell=True)
out = proc.communicate()
currPkgs = out[0].decode("utf-8").rstrip('\n').split('\n')

# Read from _requirements.txt if it is there
reqPkgs = [line.rstrip('\n') for line in open('_requirements.txt')]

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

# update _requirements file after install process!
os.system('pip freeze > _requirements.txt')

### REMEMBER!! When you install a new package, update _requirements.txt!
# Do this by typing 'pip freeze > _requirements.txt' into the terminal