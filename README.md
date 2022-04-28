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
2. Unzip to C:\\blender\\3.0.0 (which has a folder called 3.0)
3. Open the python console within blender, and check the python version 
   - e.g. 3.9.7
4. Delete the python folder and all its contents (C:\\blender\\3.0.0\\3.0\\python)
5. Install Anaconda (NOT miniconda), and open anaconda prompt with admin privileges
   - Make sure you have "C:\\Users\\Praneeth\\anaconda3\\condabin" in the system path
   - On windows, check the Path variable in the 'System Variables' box when editing environment variables
6. Clone this repository, and the dependency to your workspace (make sure git is installed and added to your system path)
   - Navigate to your workspace in the command prompt (e.g. C:\\dev)
   - git clone https://github.com/praneethnamburi/blender-ScriptViz.git
   - git clone https://github.com/praneethnamburi/pn-utilities.git
   - cd blender-ScriptViz
7. Create an anaconda environment using the following commands:
   - conda create -n blender3 python=3.9.7 numpy scipy pandas jupyter ipython matplotlib blinker scikit-learn -y
   - conda activate blender3
   - conda install -c conda-forge pybullet multiprocess pysimplegui
   - pip install decord imageio imageio-ffmpeg ffmpeg-python pytube ahrs urdfpy pint soundfile celluloid ipympl
8.  Install VSCode and activate the environment from within VSCode's command line
9.  Call blender from the command line. The idea is to pass an extra argument while launching blender to set the path the python we want to use. 
    - C:\\blender\\3.0.0\\3.0\\blender.exe --env-system-python "C:\\Users\\Praneeth\\.conda\\envs\\blender3"
    - C:\\blender\\3.0.0\\3.0\\blender.exe --env-system-python "C:\\Users\\Praneeth\\anaconda3\\envs\\blender3"
    - Remember to use double quotes if there is a space in the path!
    - If this works, you're good to go! Rest of the steps make are meant to make your life easier in the long run.
    - You should be able to install additional packages using conda and import them in the blender console.
10. Delete/rename C:\\blender\\3.0.0\\python39.dll if you are having trouble loading numpy.
11. Recommended: Add the path to this repository to your python path. For example, create a 'paths.pth' file, open it in notepad, and type the following lines into it:
    - C:\\dev\\blender-ScritpViz
    - C:\\dev\\pn-utilities
    - Save this as C:\\Users\\Praneeth\\anaconda3\\envs\\blender3\\Lib\\site-packages\\paths.pth

### Troubleshooting:
    - A useful tip is to check if you're able to find the correct python, pip, conda and blender commands from your command prompt. Most of the issues I encountered had something to do with the correct paths.
    - Use 'where blender' in the windows command prompt inside VSCode
    - Result: C:\\blender\\3.0.0\\blender.exe
    - where python
    - C:\\Users\\Praneeth\\.conda\\envs\\blender3\\python.exe
    - where conda
    - C:\\ProgramData\\Anaconda3\\condabin\\conda.bat


### Current workflow

1. Start VSCode
2. Activatec conda environment from the terminal
   - conda activate blender3
3. Start blender
   - C:\\blender\\3.0.0\\3.0\\blender.exe --env-system-python "C:\\Users\\Praneeth\\.conda\\envs\\blender3"

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
