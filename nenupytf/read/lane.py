#! /usr/bin/python3
# -*- coding: utf-8 -*-


__author__ = ['Alan Loh']
__copyright__ = 'Copyright 2019, nenupytf'
__credits__ = ['Alan Loh']
__maintainer__ = 'Alan Loh'
__email__ = 'alan.loh@obspm.fr'
__status__ = 'Production'
__all__ = [
    'Lane'
    ]


import os.path as path
import numpy as np

from nenupytf.other import header_struct


# ============================================================= #
# --------------------------- Lane ---------------------------- #
# ============================================================= #
class Lane(object):
    """
    """
    def __init__(self, spectrum):
        self.sfile = spectrum
        self.dtype = None
        self.memdata = None


    @property
    def sfile(self):
        return self._sfile
    @sfile.setter
    def sfile(self, s):
        if not isinstance(s, str):
            raise TypeError(
                'String expected.'
                )
        self._sfile = path.abspath(s)
        if not path.isfile(self._sfile):
            raise FileNotFoundError(
                'File {} not found'.format(self._sfile)
                )

        self._load()
        self._parse_tf()
        return


    def _load(self):
        """ Open the .spectra file in memmap mode.
            Store it in the `memdata` attribute.
        """
        with open(self.sfile, 'rb') as rf:
            hd_struct = np.dtype(header_struct)
            header = np.frombuffer(
                rf.read(hd_struct.itemsize),
                count=1,
                dtype=hd_struct,
                )[0]

        for key in header:
            setattr(self, key.lower(), header[key])

        beamlet_struct = np.dtype(
            [('lane', 'int32'),
            ('beam', 'int32'),
            ('channel', 'int32'),
            ('fft0', 'float32', (self.nffte, self.fftlen, 2)),
            ('fft1', 'float32', (self.nffte, self.fftlen, 2))]
            )
        
        block_struct = header_struct +\
            [('data', beamlet_struct, (self.nbchan))]
        
        self.dtype = np.dtype(block_struct)
        
        itemsize = self.dtype.itemsize
        with open(self.sfile, 'rb') as rf:
            tmp = np.memmap(rf, dtype='int8', mode='r')
        n_blocks = tmp.size * tmp.itemsize // (itemsize)
        data = tmp[: n_blocks * itemsize].view(self.dtype)

        self.memdata = data
        return


    def _parse_tf(self):
        """ Once the file is open wia memmap, go through ir
            and store information for each time, frequency,
            beam index and lane index.
        """
        print(self.timestamp)
        return
# ============================================================= #

        
    
