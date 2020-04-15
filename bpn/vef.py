"""
Collection of functions that output vertices, edges and faces.
"""

import numpy as np

def ngon(n=3, r=1, th_off_deg='auto'):
    """
    n-sided polygon inscribed in a circle of radius r.
    th_off_deg theta offset in degrees.
    """
    if th_off_deg == 'auto':
        th_off_deg = ((n-2)*180/n)%90 if n%2 == 1 else 360/(2*n)
    theta = np.linspace(0, 2*np.pi, n, False) + np.radians(th_off_deg)
    v = [(r*np.cos(θ), r*np.sin(θ), 0) for θ in theta]
    e = [(i, (i+1)%n) for i in np.arange(0, n)]
    f = [tuple(np.arange(0, n))]

    if n == 2:
        e.pop(-1)
        f = []
    return v, e, f

def xyz2vef(x, y, z):
    """
    Convert 1-D arrays x, y, z into vertices and edges
    """
    n = len(x)
    assert len(y) == n
    assert len(z) == n
    v = [(xv, yv, zv) for xv, yv, zv in zip(x, y, z)]
    e = [(i, i+1) for i in np.arange(0, n-1)]
    f = []
    return v, e, f
