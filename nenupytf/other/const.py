#! /usr/bin/python3
# -*- coding: utf-8 -*-


"""
    *****
    const
    *****
"""


__author__ = ['Alan Loh']
__copyright__ = 'Copyright 2019, nenupytf'
__credits__ = ['Alan Loh']
__maintainer__ = 'Alan Loh'
__email__ = 'alan.loh@obspm.fr'
__status__ = 'Production'
__all__ = [
    'max_bsn',
    'allowed_stokes',
    'header_struct',
    'bst_exts',
    'compute_bandpass'
    ]


from os.path import realpath, dirname, join
import numpy as np
from functools import lru_cache


# Maximal block sequence number
max_bsn = 200e6 / 1024.

# Stokes parameters that are allowed
allowed_stokes = [
    'i',
    'q',
    'u',
    'v',
    'fracv',
    'xx',
    'yy',
    'argxy',
    'phasexy'
    ]

# Structure of header for each lane file
header_struct = [
    ('idx', 'uint64'),
    ('TIMESTAMP', 'uint64'),
    ('BLOCKSEQNUMBER', 'uint64'),
    ('fftlen', 'int32'),
    ('nfft2int', 'int32'),
    ('fftovlp', 'int32'),
    ('apodisation', 'int32'),
    ('nffte', 'int32'),
    ('nbchan', 'int32')
    ]

# BST extensions, name and HDU index
bst_exts = [
        ('intsr', 1),
        ('obs', 2),
        ('anabeam', 3),
        ('beam', 4),
        ('pointing_ab', 5),
        ('pointing_b', 6)
    ]

# Bandpass coefficients
@lru_cache(maxsize=1) # keep the output in cache
def compute_bandpass(fftlen):
    """ Compute the bandpass for a beamlet in order to correct
        for the shape.
        (from Cedric Viou)
    """
    module = dirname(realpath(__file__))
    kaiser_file = join(module, 'bandpass_coeffs.dat')

    kaiser = np.loadtxt(kaiser_file)

    n_tap = 16
    over_sampling = fftlen // n_tap
    n_fft = over_sampling * kaiser.size

    g_high_res = np.fft.fft(kaiser, n_fft)
    mid = fftlen // 2
    middle = np.r_[g_high_res[-mid:], g_high_res[:mid]]
    right = g_high_res[mid:mid + fftlen]
    left = g_high_res[-mid - fftlen:-mid]

    g = 2**25/np.sqrt(np.abs(middle)**2 + np.abs(left)**2 + np.abs(right)**2)
    return g**2.


