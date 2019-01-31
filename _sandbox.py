"""
This is a sandbox. Develop code here!
"""
# Don't touch this
import os
import sys
import bpn # pylint: unused-import

if os.path.dirname(os.path.realpath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))

# add modules here

def main():
    """Actual development happens here"""
    import pnTools as my
    my.getFileName_full("C:\\blender\\2.80.0", "blender.exe")
    
    @my.OnDisk
    def dummyFunc(arg1):
        arg2 = arg1 + "blender"
        return arg2

    dummyFunc(arg1="C:\\")

if __name__ == '__main__' or __name__ == '<run_path>':
    main()