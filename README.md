# bpn

The goal of this project is to ease the process of 3D scientific data visualization.

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

1. Download blender (get the 2.80 beta, and get the zip file, NOT a binary installer), or just follow this link: <https://builder.blender.org/download/>
2. Unzip into ~/blender, OR C:\blender. OSX users:
   - Create a folder "blender" in your home directory
   - Move the Contents folder inside blender application into the "blender" folder
4. Make sure that the path string to the blender executable has the
   string 'blender' in it
5. Set paths to blender and packaged python executables in blender
   - Check using terminal that when you do where/which blender and where/which python, you get the correct executables
   OSX users:
   - in VSCode: cmd+shift+P -> Install 'code' command in PATH
   - Go to the VSCode integrated terminal, and type code /etc/paths
   - Add the blender executable (within the package) and python executable (within the blender.app package) to the top of this directory.
   - example: /Users/younah/blender/Contents/MacOS
              /Users/younah/blender/Contents/Resources/2.80/python/bin
   - which blender and which python3.7m should point to the correct files inside your terminal
        - example: /Users/younah/blender/Contents/MacOS/blender
                   /Users/younah/blender/Contents/Resources/2.80/python/bin/python3.7m
6. Install JacquesLucke's blender development extension for VSCode
7. Set up keyboard shortcuts and settings in VSCode
8. Set blender executable path, environment path, in VSCode inside settings.JSON (or, in your *.code-workspace) folder
9. Install nodejs (to interface with firebase)
10. Git clone this repository
   - either from Praneeth's dropbox githosting, or
   - <https://github.com/issalab/praneethTutorial.git>
11. Run python _requirementsCheck.py, which should:
   1. Check if blender, and the correct python executables are visible to the terminal
   2. Make a startup file in blender's startup directory (for customizing blender's workspace variables)
   3. Install pip inside blender if it doesn't exist
   4. Use _requirements.txt to download and install packages into blender
   5. Print a summary of these changes, and update the _requirements.txt file
12. Setting up VSCode for blender python development
13. Add-ons
14. Edit your settings JSON file
   - set python interpreter path
   - set blender executable path (to the app or the executable inside the app?)
   - example:
    {
        "python.pythonPath": "/Users/younah/blender/Contents/Resources/2.80/python/bin/python3.7m",
        "git.autofetch": true,
        "git.enableSmartCommit": true,
        "blender.executables": [
            {
                "path": "/Users/younah/blender/Contents/MacOS/blender",
                "name": "",
                "isDebug": false
            }
        ]
    }
14. (optional?) Save your VSCode workspace
15. In the terminal, type which python3.7m (double-checking!)
16. If this is the python inside blender, then type python3.7m _requirementsCheck.py to install required packages into blender's python
17. In VSCode's command palette, type Blender: start (automate using multi-command)

## Development workflow

1. Start VSCode
2. sync VSCode settings (automated this using the extension)
3. git pull
4. Check requirements using shift+f6 (blender --python
   _requirementsCheck.py)
5. Start blender using VSCode extension
   - automated 3, 4, and 5 using the multi-command extension
6. Clean up workspace by typing exec(bpy.loadStr) into blender's python console. This will work if _requirementsCheck.py completed successfully.
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

## Folder structure

### _auth: Authentication

This folder contains authentication keys for interfacing with
applications. Don't commit this when working with multiple people.

### _dev: Developer notes

Notes for development and learning during the course of the project.
_requirements_topLevel.txt is meant to help with python's package
management. It is a good idea to add this to source control when
developing with multiple people, but this will eventually disappear from
distribution. So, only put things that you don't want to enventually
distribute.

### _ext: External dependencies

Keep this very selective.

### _temp: Temporary folder

Local cache for storing intermediate data generated by the software.

### node_modules

Dependencies for node (listed in package-lock.json). Keep the
node_modules folder out of source control.