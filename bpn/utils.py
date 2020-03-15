"""
Utility functions
"""

import numpy as np

def apply_matrix(vert, mat):
    """
    Apply matrix transformation to a set of vertices.
    """
    v4 = np.concatenate((vert, np.ones([np.shape(vert)[0], 1])), axis=1)
    return np.matmul(mat, v4.T).T[:, 0:3]
 