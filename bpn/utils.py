"""
Utility functions
"""
import os
import sys
import numpy as np

import bpy # pylint: disable=import-error

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

import pntools as pn

def apply_matrix(vert, mat):
    """
    Apply matrix transformation to a set of vertices.
    """
    mat = np.array(mat) # mat in blender is of Matrix type, and I'm using numpy 2d arrays everywhere.
    v4 = np.concatenate((vert, np.ones([np.shape(vert)[0], 1])), axis=1)
    return (mat@v4.T).T[:, 0:3]

class CoordSystem:
    """
    Coordinate frame defined by origin and unit vectors.
    Unit vectors are given in 'world' coordinates, where origin in zero, and matrix is eye(4)
    """
    def __init__(self, **kwargs):
        if 'm' in kwargs:
            kwargs['m'] = np.array(kwargs['m'])
            assert np.shape(kwargs['m']) in ((3, 3), [4, 4])
            i = kwargs['m'][0:3, 0]
            j = kwargs['m'][0:3, 1]
            k = kwargs['m'][0:3, 2]
            if np.shape(kwargs['m']) == (4, 4):
                origin = kwargs['m'][0:3, 3]
        # if conflicting input is given, individual assignments over-ride matrix assignment
        if 'origin' in kwargs:
            origin = kwargs['origin']
        if 'center' in kwargs:
            origin = kwargs['center']
        if 'i' in kwargs:
            i = kwargs['i']
            assert len(i) == 3
            i = np.array(i)/np.linalg.norm(i)
        if 'j' in kwargs:
            j = kwargs['j']
            assert len(j) == 3
            j = np.array(j)/np.linalg.norm(j)
        if 'k' in kwargs:
            k = kwargs['k']
            assert len(k) == 3
            k = np.array(k)/np.linalg.norm(k)
        
        if 'origin' not in locals():
            origin = np.zeros(3) 
        
        self.m = np.array([\
            [i[0], j[0], k[0], origin[0]],\
            [i[1], j[1], k[1], origin[1]],\
            [i[2], j[2], k[2], origin[2]],\
            [0, 0, 0, 1]\
            ])

    @property
    def origin(self):
        """Origin of the coordinate system."""
        return self.m[0:3, 3]
    
    @origin.setter
    def origin(self, new_origin):
        assert len(new_origin) == 3
        self.m[0:3, 3] = new_origin
    
    center = origin

    def apply_transform(self, coord, tfmat):
        """Apply transform in current coordinate frame."""
        assert np.shape(coord)[1] == 3
        if np.shape(tfmat) == (3, 3):
            tmp = np.eye(4)
            tmp[0:3, 0:3] = tfmat
            tfmat = tmp
        assert np.shape(tfmat) == (4, 4)
        return apply_matrix(coord, self.m@tfmat@np.linalg.inv(self.m))


def normal2tfmat(n):
    """
    Given a direction vector, create a transformation matrix that transforms a shape in the XY plane to the direction of the normal by first rotating along Y axis, and then along X axis.
    n is a 3-element 1-D numpy array
    """
    n = np.array(n)
    assert len(n) == 3
    n = n/np.linalg.norm(n)
    nx = n[0]
    ny = n[1]
    nz = n[2]
    d = np.sqrt(1-nx**2)
    m = np.array([\
        [d, 0, nx],\
        [-nx*ny/d, nz/d, ny],\
        [-nx*nz/d, -ny/d, nz]\
        ])
    return m

def twisttf(θ):
    """Twist transform is simply a rotation transform around Z."""
    m = np.array([\
        [np.cos(θ), -np.sin(θ), 0],\
        [np.sin(θ), np.cos(θ), 0],\
        [0, 0, 1]\
        ])
    return m

def scaletf(s):
    """Construct a scale transformation matrix from a 3-element s."""
    if isinstance(s, (int, float)):
        s = np.array((1, 1, 1))*float(s)
    s = np.array(s)
    m = np.array([\
        [s[0], 0, 0],\
        [0, s[1], 0],\
        [0, 0, s[2]]\
        ])
    return m

def new_name(name, curr_names):
    """
    Blender-style name conflict resolution.

    Appends .001 if name is in curr_names
    If name+'.001' exists, then returns name+'.002' and so on

    Example:
        obj_name = new_name(obj_name, [o.name for o in bpy.data.objects])
    """
    i = 0
    tmp_name = name
    while tmp_name in curr_names:
        i += 1
        tmp_name = name + '.{:03d}'.format(i)
    return tmp_name

def clean_names(name, kwargs, kwargs_def=None):
    """
    Use this for name cleanup!
    Splits keyword arguments into names as used by the bpn module, and other keyword arguments to be used by the function.
    
    This has a similar purpose to pntools.clean_kwargs (in terms of splitting up keyword arguments, and ensuring defaults).
    In addition, it implements some name checking int he blender-environment.
    In the future, we can extend this functionality to include scene names, etc. simply by adding to default arguments.
    Usage:
        def mydrawingfunc(name=None, **kwargs):
            kwargs_names, kwargs_forthisfunc = clean_names(name, kwargs, defaultsformydrawingfunc)
    See:
        Draw class in bpn.turtle
        torus function in bpn.new
    """
    if isinstance(name, str):
        kwargs['msh_name'] = name if 'msh_name' not in kwargs else kwargs['msh_name']
        kwargs['obj_name'] = name if 'obj_name' not in kwargs else kwargs['obj_name']

    kwargs_defdef = {
        'msh_name' : 'new_msh', 
        'obj_name' : 'new_obj',
        'coll_name': 'Collection',
        'priority_obj': 'new',
        'priority_msh': 'current',
    }
    if not kwargs_def:
        kwargs_def = {}

    kwargs_def, _ = pn.clean_kwargs(kwargs_def, kwargs_defdef)
    kwargs_names, kwargs_other = pn.clean_kwargs(kwargs, kwargs_def)
    
    # what to do if 'obj_name' and/or 'msh_name' already exist in the blender workspace
    if kwargs_names['priority_obj'] == 'new':
        kwargs_names['obj_name'] = new_name(kwargs_names['obj_name'], [o.name for o in bpy.data.objects])
    
    if kwargs_names['priority_msh'] == 'new':
        kwargs_names['msh_name'] = new_name(kwargs_names['msh_name'], [m.name for m in bpy.data.meshes])

    return kwargs_names, kwargs_other
