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
2. sync VSCode settings (automated this using the extension)
3. git pull
4. Check requirements using shift+f6 (blender --python
   _requirementsCheck.py)
5. Start blender using VSCode extension
   - automated 3, 4, and 5 using the multi-command extension
6. Clean up workspace (this probably won't work unless you import bpn?)
7. Run scripts (blender extension, add shortcut f6) and develop!
8. During development, update documentation, notes and readme.md
9. git Commit and push
10. Sync VSCode settings (automated this using the extension setting)

## Current workflow

1. Start VSCode
2. Press shift+f6 to start a sesstion
3. Start coding! Use f6 to run scripts

Don't use system exits! This will terminate blender as well

## Setting up VSCode for blender + python development

Environment variables: add paths to env variables so that blender and
python bundled with blender show up when you query blender and python,
and the corresponding pip

## Using the bpn module