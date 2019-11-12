#! /usr/bin/python3
# -*- coding: utf-8 -*-


__author__ = ['Alan Loh']
__copyright__ = 'Copyright 2019, nenupytf'
__credits__ = ['Alan Loh']
__maintainer__ = 'Alan Loh'
__email__ = 'alan.loh@obspm.fr'
__status__ = 'Production'
__all__ = [
    'gain_jumps',
    ]


import numpy as np

from nenupytf.stokes import SpecData


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

