# bpn

The goal of this project is to ease the process of 3D scientific data
visualization.

We aim to achieve this by:

1. Easing the burden that python's package management system puts on
   blender python developers because blender comes bundled with python.
2. Providing a way to clean up and inject modules into blender's python
   console.
3. Providing instructions on how to set up a development workflow using
   blender, python and VSCode.
4. How do I use the python debugger as much as possible?
   - Simple use case: visualization in blender not required during debugging
   - Visualization is required in blender while debugging

## Installation instructions

1. Download blender (in zip format)
2. Make sure that the path string to the blender executable has the
   string 'blender' in it
3. set paths
4. install pip for blender's python
5. install all the required packages using blender --python
   $_requirementsCheck.py
6. Setting up VSCode for blender python development
7. Add-ons

## Development workflow

1. Start VSCode
2. sync VSCode settings
3. git pull
4. Check requirements using shift+f6 (blender --python
   _requirementsCheck.py) (add an exit blender command here)
5. Start blender using VSCode extension
6. Clean up workspace (this probably won't work unless you import bpn?)
7. Run scripts (blender extension, add shortcut f6) and develop!
8. During development, update documentation, notes and readme.md
9. git Commit and push
10. Sync VSCode settings

## Setting up VSCode for blender + python development

## Using the bpn module