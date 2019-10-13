#! /usr/bin/python3
# -*- coding: utf-8 -*-


__author__ = ['Alan Loh']
__copyright__ = 'Copyright 2019, nenupytf'
__credits__ = ['Alan Loh']
__maintainer__ = 'Alan Loh'
__email__ = 'alan.loh@obspm.fr'
__status__ = 'Production'
__all__ = [
    'max_bsn',
    'allowed_stokes',
    'header_struct'
    ]


# Maximal block sequence number
max_bsn = 200e6 / 1024.

# Stokes parameters that are allowed
allowed_stokes = [
    'i',
    'q',
    'u',
    'v',
    'fracv'
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
