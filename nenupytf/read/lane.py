#! /usr/bin/python3
# -*- coding: utf-8 -*-


__author__ = ['Alan Loh']
__copyright__ = 'Copyright 2019, nenupytf'
__credits__ = ['Alan Loh']
__maintainer__ = 'Alan Loh'
__email__ = 'alan.loh@obspm.fr'
__status__ = 'Production'
__all__ = [
    'Lane',
    'LaneSpectrum'
    ]


import os.path as path
import numpy as np

from nenupytf.other import header_struct


# ============================================================= #
# --------------------------- Lane ---------------------------- #
# ============================================================= #
class Lane(object):
    """ Class to properly handle opening of one '*.spectra' file
        for a specific lane.

        Parameters
        ----------
        spectrum : str
            Complete path towards a '*.spectra' file

        Attributes
        ----------
        memdata : `numpy.memmap`
            Memory map obejct containing the decoded binary data
        lane : int
            Land index corresponding to the file
        sfile : str
            Absolute path towards the '*.spectra' file
    """

    def __init__(self, spectrum):
        self._dtype = None
        self.memdata = None
        self.lane = None
        self.sfile = spectrum


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

        fname = path.basename(self._sfile)
        self.lane = int(
            fname.split('_')[-1].replace('.spectra', '')
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
        
        self._dtype = np.dtype(block_struct)
        
        itemsize = self._dtype.itemsize
        with open(self.sfile, 'rb') as rf:
            tmp = np.memmap(rf, dtype='int8', mode='r')
        n_blocks = tmp.size * tmp.itemsize // (itemsize)
        data = tmp[: n_blocks * itemsize].view(self._dtype)

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

        
# ============================================================= #
# ----------------------- LaneSpectrum ------------------------ #
# ============================================================= #
class LaneSpectrum(Lane):
    """
    """

    def __init__(self, spectrum):
        super().__init__(spectrum=spectrum)
# ============================================================= #



