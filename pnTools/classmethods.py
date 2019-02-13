import numpy as np

def properties(self):
    """Print all the properties in this class."""
    #pylint:disable=expression-not-assigned
    [print((k, type(getattr(self, k)), np.shape(getattr(self, k)))) for k in dir(self) if '_' not in k and 'method' not in k]
