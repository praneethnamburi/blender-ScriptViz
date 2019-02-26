# Issa lab meeting 2019.02.27

## Instructions to prepare

1. - Download blender: (get the 2.80 beta, and get the zip file, NOT a binary installer), or just follow this link: <https://builder.blender.org/download/>
   - Unzip into ~/blender, OR C:\blender

2. - Download and install VSCode <https://code.visualstudio.com/download>
   - In VSCode, Install the blender development extension (which will also install the python and c/c++ extensions)

3. - Download and install nodejs <https://nodejs.org/en/download/>

4. - Clone (preferred!)/download the repository: <https://github.com/issalab/praneethTutorial.git>
I will refer to this folder in the next steps as DEV_ROOT (this is actually everything I've been developing in the last month, you'll use the modules during the tutorial)
   - Download the authentication tokens (I will send them to you separately for security reasons) into a sub-folder called _auth inside DEV_ROOT.
   - Create an empty folder called _temp in DEV_ROOT

## We will aim to learn:

1) Blender basics.
2) Basics of developing in VSCode.
3) Discuss how to set up a workflow for development across machines, developers and users.
4) Coding for blender 101.
5) Using the bpn module.
6) Functional programming in python.
7) Using decorators to turn a class into a database of class instances.

### Section 1. Blender basics

- Window management: windows, screens, areas, spaces
- Explore blender data organization in the console

### Section 2. Basics of developing in VSCode

- Command palette
- Settings
- Keyboard shortcuts
- Built-in terminal
- Debugging for python
- Debugging

Exercises:

1. Open the pnTutorial project in VSCode
2. Change the font size of text
3. Attach F6 keyboard shortcut to the command blender.runScript
4. Snippets: Create a snippet for importing commonly used modules.
5. Find the paths for blender, python, node and git executables (where/which)
    - Use the keyboard shortcut to toggle the terminal
6. Attach shift+F6 to run the command python test1.py
7. Run blender from the terminal.
8. Run blender using the blender extension.

### Section 3. Workflow setup

Exercise:

- Install packages using the _requirementsCheck.py script

### Section 4. Coding in blender

Exercises:

1. (Msh) Add a cube to the scene. Double its size programatically.
   - (Msh part 2) Matrix multiplication
2. (Props) Console, then VSCode. Query the objects in the scene.
3. (ReportDelta) Functional programming in python.
4. Functional programming part 2 - Turn a class into a database of class instances.
5. Load marmoset atlas meshes into blender.
6. Visualize behavior data in blender.
