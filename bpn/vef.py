"""
Collection of functions that output vertices, edges and faces.
"""

import numpy as np

def ngon(n=3, r=1, th_off_deg=0):
    """
    n-sided polygon inscribed in a circle of radius r.
    th_off_deg theta offset in degrees.
    """
    theta = np.linspace(0, 2*np.pi, n, False) + np.radians(th_off_deg)
    v = [(r*np.cos(θ), r*np.sin(θ), 0) for θ in theta]
    f = [tuple(np.arange(0, n))]
    e = [(i, (i+1)%n) for i in np.arange(0, n)]
    return v, e, f
    