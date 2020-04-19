"""
Simplify package synchronization across multiple development machines.

Purpose:
This code makes it easier to manage packages across machines when
developing with blender. It is also very useful for installing your
project with all the dependecies on a new machine, or when you wish to
start with a new release of blender.

Strategy:
This code collects the currently installed package listing, and the
listing given in _requirements.txt. It compares these two listings, and
invokes a series of pip commands in the terminal for package management.

Use as script:
Yes. This file is NOT meant to be imported as a module. Please supply
this script as an input to the blender executable when launching it from
the command line.
>>> blender --python ${thisFileName}.py --python ${otherStartScript}.py

Testing:
1. Run the above command. The terminal should show a summary of version
   changes, new installs and uninstalls (even if nothing changed).
2. Modify the version number and/or add/remove an entry to the
   _requirements.txt file and use this script.
3. Install a new package using pip and invoke this script. If you didn't
   update _requirements.txt, you should receive a request for
   uninstalling the package you just installed. If you choose not to
   uninstall, then check that _requirements.txt lists the new package(s)
   once this script finishes running.

! Caution:
1. USE this only with the correct python install! My use case is limited
   to using this script with blender only!
2. This file requires a _requirements.txt file. If you don't have one,
   generate it using pip freeze > _requirements.txt.
3. This code assumes that your blender folder has the word 'blender' in
   it when it tries to validate the pip it finds

Tips:
1. Use the VSCode extension 'run in terminal' to send this file as an
   argument to blender along with the file you wish to load at startup.
   Here is my addition to keybindings.json in VSCode:
   "key": "f6",
   "command": "runInTerminal.run",
   "args": {
       "cmd": "blender --python _requirementsCheck.py --python ${file}",
       "match": ".*"
    },
    Then use f6 to start using your script after checking for package
    harmony!
2. [recommended!] If you are using Jacques Lucke's Blender Development
   add-on in VSCode to debug, then map f6 to blender: run script. Map
   the requirements checker to shift+f6. Run the requirements checker
   periodically (manually). The manual part is not ideal at the moment.
3. When you install a package on a given machine using pip, update the
   _requirements.txt file so that the next time requirements are
   checked, the code will not bug you asking if you wish to uninstall
   some packages. Note that this will only happen once because this
   script will update _requirements.txt file every time it runs
   successfully, so if it does happen, just say no.
4. It is a good idea to keep track of the "top-level" packages that you
   use when developing a package. I do this by having a text file called
   _requirements_topLevel.txt in a folder called _dev. This is important
   because _requriements.txt can quickly become unreadable, and simply
   used as a project management tool.
5. If you just did pip install -r _requirements.txt, version changes and
   new installs are OK, but uninstalls won't work!
6. It is a VERY good idea to use version control to keep track of
   _requirements.txt. Try to indicate in someway that you changed this
   file in the commit message. I use for _requirements - added pkgname.
"""

import os
import sys
from pathlib import Path

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
if THIS_DIR not in sys.path:
    sys.path.append(THIS_DIR)

import pntools as pn

def writeBlenderStartupFile(fName_full):
    """
    Generate a startup file that adds development directory (current directory) to the system path
    """
    pathToAppend = str(THIS_DIR).replace('\\', '\\\\')
    try:
        f = open(fName_full, 'w')
        f.write("import sys\n")
        f.write("import os\n")
        f.write("path = '" + pathToAppend + "'\n")
        f.write("if path not in sys.path and path[0].lower()+path[1:] not in sys.path:\n")
        f.write("   sys.path.append(path)\n")
    finally:
        f.close()

def getPkgNameVer(pkgs):
    """
    Takes a string list describing pinned packages e.g. numpy==1.15.0
    Returns the package names and versions as separate string lists numpy and 1.15.0
    """
    pkgNames = [m[0] for m in [k.split('==') for k in pkgs]]
    pkgVers = [m[1] for m in [k.split('==') for k in pkgs]]
    return pkgNames, pkgVers

def listDiff(lstA, lstB):
    """
    Return a logical of size lstA
    For each element in lstA, return true if it is not in lstB
    Therefore, its like lstA-lstB
    It returns the elements of lstA that are not in lstB
    """
    lstDiffBool = []  # logical
    for a in lstA:
        lstDiffBool.append(not a in lstB)
    lstDiff = [k for i, k in enumerate(lstA) if lstDiffBool[i]]
    return lstDiff, lstDiffBool

def main():
    print('Checking if Blender exists:')
    blenderPath = pn.locate_command('blender')
    if not blenderPath:
        return

    print('Checking for the correct python:')
    pythonPath = pn.locate_command('python', 'blender')
    pythonPath = pn.locate_command('python3.7m', 'blender') if not pythonPath else pythonPath
    if not pythonPath:
        return

    print('(over)writing blender startup file:')
    blenderBaseDir = str(Path(blenderPath).parents[0])
    dirs = next(os.walk(blenderBaseDir))[1]
    blenderVersionDirName = [o for o in dirs if o.replace('.', '', 1).isdigit()]
    if not blenderVersionDirName:
        return
    assert len(blenderVersionDirName) == 1
    blenderStartupPath = pn.ospath(str(os.path.join(blenderBaseDir, blenderVersionDirName[0], 'scripts', 'startup')))
    if not blenderStartupPath:
        return
    writeBlenderStartupFile(os.path.join(blenderStartupPath, 'pnStartup.py'))

    # Anaconda-specific things
    # conda env create -f _requirements.yml
    # To do this, use 
    # conda list --revisions
    # conda install --rev <rev number>
    # defaultEnvName = 'blender'+str(Path(blenderPath).parents[0]).split(os.sep)[-1].replace('.', '')
    # os.system('conda activate ' + defaultEnvName)
    # os.system('conda env update --file _requirements.yml')
    os.system('conda env export > _requirements.yml')

if __name__ == '__main__' or __name__ == '<run_path>':
    main()
