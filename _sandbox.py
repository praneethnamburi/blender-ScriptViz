"""
Sandbox. Not involving blender.

Mode 1:
Type code here, and press Ctrl+Enter (python.datascience.runFileInteractive)
This opens an ipython session and evaluates the code there.
In the current setup, I'm initiating the kernel from blender's python.

Mode 2:
To debug this code, simply insert breakpoint(s) and press f5 (make sure you don't have cells - #%%)

CAUTION: Use these modes only when debugger for blender is not active!
"""

import os
os.chdir('D:\\Workspace\\blenderPython')

class DummyClass:
    def __init__(self, var):
        self._var = var
    
    @property
    def var(self):
        return self._var
        
class DummyChildClass(DummyClass):
    @DummyClass.var.setter #pylint: disable=no-member
    def var(self, new_var):
        self._var = new_var

d = DummyClass(1)
d2 = DummyChildClass(2)
