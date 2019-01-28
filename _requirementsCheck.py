"""
### This code makes it easier to manage packages across machines when developing with blender
# Use this code by typing blender --python .py in the terminal
# I have chosen to use the VSCode extension 'run in terminal' to send this file as an argument to blender along with the file I'd like to run
# blender --python .py --python ${file}
# Improve this file by adding some checks to make sure the correct pip and python are being used!
# ! USE this only with blender! If you get the wrong python install, you can mess that up big time!
# * USE blender --python .py
# ! DO NOT USE python .py unless you are sure you're referring to the correct python
### REMEMBER!! When you install a new package, update _requirements.txt!
# Do this by typing 'pip freeze > _requirements.txt' into the terminal
# You can also add the entry manually into _requirements.txt. Don't forget the double equals == There are TWO of them!
# In fact, the preferred way of adding a package (even for the first time would be to add the entry to _requirements.txt and running a blender script
# NOTE: If you just did pip install -r _requirements.txt, version changes and new installs are OK, but uninstalls won't work!
# TODO: install pip automatically if it isn't already installed
# TODO: ensure correct blender and pip executables
"""

import os
import subprocess

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
    # Package management (need to add exception handling here)
    # Get list of installed packages
    proc = subprocess.Popen('pip freeze', stdout=subprocess.PIPE, shell=True)
    out = proc.communicate()
    currPkgs = out[0].decode("utf-8").rstrip('\n').split('\n')
    currPkgs = [k.rstrip('\r') for k in currPkgs]  # windows compatibility
    currPkgNames, _ = getPkgNameVer(currPkgs)

    # Read from _requirements.txt if it is there
    reqPkgs = [line.rstrip('\n') for line in open(
        '_requirements.txt') if line.rstrip('\n')]  # the 'if' part discards empty lines
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
    # list pakcages that changed version
    print('Version changes (shows uninstalled version):')
    print(verChangePkgs)
    print('New installs including version changes (shows installed version): ')
    print(missingPkgs)
    print('These packages were uninstalled: ')
    print(extraPkgs)

    # update _requirements file after install process!
    os.system('pip freeze > _requirements.txt')
