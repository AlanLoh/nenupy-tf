#! /usr/bin/python3
# -*- coding: utf-8 -*-


"""
    *****
    Astro
    *****

    Test de docstring
"""


__author__ = ['Alan Loh']
__copyright__ = 'Copyright 2019, nenupytf'
__credits__ = ['Alan Loh']
__maintainer__ = 'Alan Loh'
__email__ = 'alan.loh@obspm.fr'
__status__ = 'Production'
__all__ = [
    'dispersion_delay'
    ]


import astropy.units as u


# ============================================================= #
# ---------------------- dispersion_delay --------------------- #
# ============================================================= #
def dispersion_delay(f1, f2, dm):
    """ Compute the delay between two frequencies of a dispersed
        astrophysical signal with a known dispersion measure 
        :attr:`dm`.

        :param f1:
            First frequency in MHz
        :type f1: float
        :param f2:
            Second frequency in MHz
        :type f2: float
        :param dm:
            Dispersion measure in pc/cm^3
        :type dm: float

        :returns: Delay in seconds
        :rtype: `~astropy.units.quantity.Quantity`

        .. note:: :attr:`f1`, :attr:`f2` and :attr:`dm` are
            converted to `~astropy.units.quantity.Quantity`
            objects for the computation. Make sure the inputs
            values are given in the proper units.     

    """
    dm *= u.parsec / u.cm**3
    f1 *= u.MHz
    f2 *= u.MHz
    k = 2.410e-4 * u.MHz**-2 * u.cm**-3 * u.parsec * u.s**-1
    df2 = (f1**-2 - f2**-2)
    delay = dm / k * df2
    return delay