#! /usr/bin/python3
# -*- coding: utf-8 -*-


"""
    ********
    analysis
    ********

    Test de docstring
"""


__author__ = ['Alan Loh']
__copyright__ = 'Copyright 2019, nenupytf'
__credits__ = ['Alan Loh']
__maintainer__ = 'Alan Loh'
__email__ = 'alan.loh@obspm.fr'
__status__ = 'Production'
__all__ = [
    'switch_shape',
    'find_switches',
    'gain_jumps',
    ]


import numpy as np
from scipy.optimize import curve_fit

from nenupytf.stokes import SpecData


# ============================================================= #
# ------------------------ switch_shape ----------------------- #
# ============================================================= #
def switch_shape(x, y):
    """ Each time an analog pointing happens, the switch commuters
        may have a variable degraded response that we need to
        correct for.
        This function aims at fitting such a profile in order to
        correct for this effect.

        Parameters
        ----------
        x : `np.ndarray`
            Time converted in float (MJD or JD)
        y : `np.ndarray`
            Profile we want to fit in dB.

        Returns
        -------
        shape : `np.ndarray`
            The fitted profile in dB, same dimensions as `x` and `y`
    """
    def switch_fit(x, a, b, c, d):
        """ Exponential growth to a plateau
        """
        return a*(1 - np.exp(-b*x + c)) + d
    errors = np.repeat(
        np.std(y)/10,
        y.size)
    errors[0] *= 1e-1
    p_opt, p_cov = curve_fit(
        switch_fit,
        x - x[0],
        switches[t_mask],
        sigma=errors
    )
    a, b, c, d = p_opt
    return switch_fit(x - x[0], a, b, c, d)


# ============================================================= #
# ----------------------- find_switches ----------------------- #
# ============================================================= #
def find_switches(x, y):
    return


# ============================================================= #
# ------------------------ gain_jumps ------------------------- #
# ============================================================= #
def gain_jumps(spec):
    """
    """
    if not isinstance(spec, SpecData):
        raise TypeError(
            'This method works with a SpecData object'
            )
    medf = np.median(spec.amp, axis=1)



