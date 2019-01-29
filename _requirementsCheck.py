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
2. When you install a package on a given machine using pip, update the
   _requirements.txt file so that the next time requirements are
   checked, the code will not bug you asking if you wish to uninstall
   some packages. Note that this will only happen once because this
   script will update _requirements.txt file every time it runs
   successfully, so if it does happen, just say no.
3. It is a good idea to keep track of the "top-level" packages that you
   use when developing a package. I do this by having a text file called
   _requirements_topLevel.txt in a folder called _dev. This is important
   because _requriements.txt can quickly become unreadable, and simply
   used as a project management tool.
4. If you just did pip install -r _requirements.txt, version changes and
   new installs are OK, but uninstalls won't work!
5. It is a VERY good idea to use version control to keep track of
   _requirements.txt. Try to indicate in someway that you changed this
   file in the commit message. I use for _requirements - added pkgname.

# TODO:
1. Add checks to ensure the correct pip and python are being used!
2. Install pip automatically if it isn't already installed
3. Add exception if the file doesn't find _requirements.txt file
"""

import os
import subprocess
import sys

def getPkgNameVer(pkgs):
    """
    Takes a string list describing pinned packages e.g. numpy==1.15.0
    Returns the package names and versions as separate string lists numpy and 1.15.0
    """
    tmpDict = {}
    tmp1 = [k.split('==') for k in pkgs]
    for k in tmp1:
        tmpDict[k[0]] = k[1]
    pkgNames = list(tmpDict.keys())
    pkgVers = list(tmpDict.values())
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

if __name__ == '__main__':
    # Check for pip and check if it is the correct one
    if sys.platform == 'linux':
        queryCmd = 'which'
    elif sys.platform == 'win32':
        queryCmd = 'where'

    pathCheckRequire = 'blender'
    procPip = subprocess.Popen(queryCmd+' pipa', stdout=subprocess.PIPE, shell=True)
    pipPath = procPip.communicate()[0].decode('utf-8')
    if not pipPath:
        raise SystemExit('Did not find pip.')

    print('Found this pip: ', pipPath)
    if pathCheckRequire not in pipPath:
        raise SystemExit('Path to pip does not have ' + pathCheckRequire + ' in it!')

    # Get list of installed packages
    proc = subprocess.Popen('pip freeze', stdout=subprocess.PIPE, shell=True)
    out = proc.communicate()
    currPkgs = out[0].decode('utf-8').rstrip('\n').split('\n')
    currPkgs = [k.rstrip('\r') for k in currPkgs]  # windows compatibility
    currPkgNames, _ = getPkgNameVer(currPkgs)

    # Read from _requirements.txt if it is there
    reqPkgs = [line.rstrip('\n') for line in open(
        '_requirements.txt') if line.rstrip('\n')]  # 'if' part to discard empty lines
    reqPkgNames, _ = getPkgNameVer(reqPkgs)

    # If some packages are not listed, ask for uninstall
    extraPkgsIncVerChg = list(set(currPkgs) - set(reqPkgs))

    # Exclude version changes from this list
    _, currMinusReq = listDiff(currPkgNames, reqPkgNames)
    extraPkgs = [k for i, k in enumerate(currPkgs) if currMinusReq[i]]
    for pkgName in extraPkgs:
        thisCmd = 'pip uninstall ' + pkgName
        exCode = os.system(thisCmd)

    # which packages changed versions?
    # this has the old version number in it
    verChangePkgs = list(set(extraPkgsIncVerChg) - set(extraPkgs))

    # If there are missing packages, install them
    missingPkgs = list(set(reqPkgs) - set(currPkgs))
    for pkgName in missingPkgs:
        thisCmd = 'pip install ' + pkgName
        exCode = os.system(thisCmd)

    # summarize changes
    print('Requirements update summmary:')
    print('Version changes (shows uninstalled version):')
    print(verChangePkgs)
    print('New installs including version changes (shows installed version): ')
    print(missingPkgs)
    print('These packages were in the uninstall list: ')
    print(extraPkgs)

    # update _requirements file after install process!
    os.system('pip freeze > _requirements.txt')
