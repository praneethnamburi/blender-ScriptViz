# Scripted visualizations in blender

The goal of this project is to script 3D scientific visualizations using blender.

To achieve this, we aim to bring together blender's powerful visualization toolkit with Anaconda's scientific computing and package management capabilities. For example, the code in ./apps/concepts/fourier_signal_composition.py was used to generate the following visualization.

![Frequency sweep illustration](./illustrations/fourier_freq_sweep.gif)

## Getting Started

See the detailed setup instructions at the end of the file.

## Contributing

This project is still a work in progress. Contributions and feedback are welcome!

## Authors

* **Praneeth Namburi** - [praneethnamburi](https://praneethnamburi.com)

## License

Files in the directories apps and illustrations are copyright praneethnamburi.

The general purpose blender scripting code (bpn, pntools) is under the MIT license.

## Acknowledgments

* All the wonderful people that make open source software
* Inspiration - 3blue1brown's videos and pedagogical clarity


## Setup instructions

These are detailed instructions that worked for me on a windows 10 laptop. 

### blender+Anaconda+VSCode

1. Download blender (get the zip file, NOT a binary installer), or just follow this link: <https://builder.blender.org/download/>
2. Unzip to C:\blender\2.83.0 (which has a folder called 2.83)
3. Open the python console within blender, and check the python version 
   - e.g. 3.7.4
4. Delete the python folder and all its contents (C:\blender\2.83.0\2.83\python)
5. Install Anaconda, and open anaconda prompt with admin privileges
6. conda create -n blender2830 python=3.7.4 ptvsd flask requests
   - install the same version as blender's python
   - env name is dictated by the main folder name (C:\blender\2.83.0)
   - ptvsd, flask and requests are required for remote debugging with VSCode
7. conda activate blender2830
8. Install VSCode
9. Add these settings in VSCode (to your workspace) - Modify this example
   -  "settings": {
         "terminal.integrated.env.windows": {
            "PATH": "C:\\blender\\2.83.0;C:\\Users\\Praneeth\\.conda\\envs\\blender2830;C:\\Users\\Praneeth\\.conda\\envs\\blender2830\\Library\\mingw-w64\\bin;C:\\Users\\Praneeth\\.conda\\envs\\blender2830\\Library\\usr\\bin;C:\\Users\\Praneeth\\.conda\\envs\\blender2830\\Library\\bin;C:\\Users\\Praneeth\\.conda\\envs\\blender2830\\Scripts;C:\\Users\\Praneeth\\.conda\\envs\\blender2830\\bin;C:\\ProgramData\\Anaconda3\\condabin;*OTHER THINGS IN YOUR PATH*,
         },
         "python.pythonPath": "C:\\Users\\Praneeth\\.conda\\envs\\blender2830\\python.exe",
      },
10. Call blender from the command line. The idea is to pass an extra argument while launching blender to set the path the python we want to use. 
    - blender.exe --env-system-python 'C:\Users\Praneeth\.conda\envs\blender2830'
11. If this works, you're good to go! Install packages using conda, and you should be able to import them in the blender console. Keep going to set up debugging.
12. Install Blender Development add-on for VSCode.
13. *Modify* the add-on's source code. The add-on launches blender with a custom-written script to enable debugging. We need the add-on to pass an additional --env-system-python argument. 
    - Locate the blender_executable.js file in the add-on install folder.
    - C:\Users\Praneeth\.vscode\extensions\jacqueslucke.blender-development-0.0.12\out\blender_executable.js
    - Modify the getBlenderLaunchArgs function
    - return ['--env-system-python', 'C:\\Users\\Praneeth\\.conda\\envs\\blender2830', '--python', paths_1.launchPath];
    - Within the function testIfPathIsBlender, in the if-else clause contained within the Promise, change the if condition to if (false)
    - This is so it does not throw 'A simple check to test...'
    - (There is probably a much more elegant way to do this)
    - Restart VSCode (for some reason it took 2 re-starts for me)
14. Troubleshooting:
    - A useful tip is to check if you're able to find the correct python, pip, conda and blender commands from your command prompt.
    - Use 'where blender' in the windows command prompt inside VSCode
    - Result: C:\blender\2.83.0\blender.exe
    - where python
    - C:\Users\Praneeth\.conda\envs\blender2830\python.exe
    - where conda
    - C:\ProgramData\Anaconda3\condabin\conda.bat


### Using this software

1. Clone the repository to your workspace (e.g. D:\Workspace\blenderPython)
2. Install additional requirements using the _requirements.yml file
   - In the terminal, navigate to the workspace folder, activate your blender anaconda environment and update it from _requirements.yml
   - conda activate blender2830
   - conda env update --file _requirements.yml
3. Run python _requirementsCheck.py in the terminal. It will:
   1. Check if blender, and the correct python executables are visible to the terminal
   2. Make a startup file in blender's startup directory
   3. Update _requirements.yml file (e.g. with your installs)
4. From VSCode's command palette, use the command Blender: start
   - Some of this can be automated using the multicommand add-on for VSCode


### Development workflow

1. Start VSCode
2. sync VSCode settings (automated this using the extension)
3. git pull
4. Check requirements using shift+f6 (blender --python
   _requirementsCheck.py)
5. Start blender using VSCode extension
   - automated 3, 4, and 5 using the multi-command extension
6. Import this software into the python console within blender using 'from bpn_init import *'. This will work if _requirementsCheck.py completed successfully.
7. Run scripts (blender extension, add shortcut f6) and develop!
8. During development, update documentation, notes and readme.md
9. git Commit and push
10. Sync VSCode settings (automated this using the extension setting)


### Current workflow

1. Start VSCode
2. Press shift+f6 to start a sesstion (multicommand automation)
3. Start coding! Use f6 to run scripts


## Folder structure

### _auth: Authentication

This folder contains authentication keys for interfacing with
applications. Don't commit this when working with multiple people.

### _dev: Developer notes

Notes for development and learning during the course of the project.
_requirements_topLevel.txt is meant to help with python's package
management. It is a good idea to add this to source control when
developing with multiple people, but this will eventually disappear from
distribution.

### _temp: Temporary folder

Local cache for storing intermediate data generated by the software.

### apps

Applications that use the main package bpn, and supporting package pntools. See License.

### bpn

This folder contains the core scripts for using 
core module has wrappers around blender objects, divided into three types:
1) Thing - class that initializes all wrappers
2) Object, Mesh, Collection, GreasePencil - wrappers around bpy.data.(*)
3) MeshObject, GreasePencilObject - Initialize object + data
   - Each of these classes have analogs in the new module (mesh, pencil)
   - The user should only need to interact with core classes through functions in the new module
utils.get is the dispatcher that automatically creates objects from the appropriate classes in the core module.

names are very important in bpn. We use names to insulate bpn from bpy. That means, bpn tries very hard not to keep a copy of things from bpy. Instead, it tries to get the appropriate information from bpy when needed. names determine the interaction between bpy and bpn.

*args are for the 'new' function to create a new blender data instance
*kwargs are for initializing that instance inside bpy.data.(type).(instance)

Objects and lights need to pass one argument through *args. I did not set it to have the flexibility of initializing empty objects with Nonetype.
Classes inherited from Object also send *args up to Thing class (e.g. MeshObject, and GreasePencilObject)
Rest of them ONLY send kwargs for initialization.

Modules vef, trf and env currently do not depend on any other files within bpn.
env requires blender and therefore, will stay within bpn, but the other two can become their own packages that bpn uses. Perhaps move them to pntools?

### pntools

General python tools that were developed with this proejct, but can generalize beyond this project.

### bpn_init.py

The purpose is to bring bpn's functionality into blender's python console with one command. At the blender console, type `from bpn_init import *`
