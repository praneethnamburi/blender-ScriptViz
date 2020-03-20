"""
Utility functions
"""

import numpy as np
import bmesh # pylint: disable=import-error

def apply_matrix(vert, mat):
    """
    Apply matrix transformation to a set of vertices.
    """
    v4 = np.concatenate((vert, np.ones([np.shape(vert)[0], 1])), axis=1)
    return np.matmul(mat, v4.T).T[:, 0:3]
 
def geom2vef(geom):
    """
    Split geometry into vertex, edge, and faces. Important when using bmesh.
    """
    v = [ele for ele in geom if isinstance(ele, bmesh.types.BMVert)]
    e = [ele for ele in geom if isinstance(ele, bmesh.types.BMEdge)]
    f = [ele for ele in geom if isinstance(ele, bmesh.types.BMFace)]
    return v, e, f
