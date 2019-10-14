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


from astropy.time import Time
import os.path as path
import numpy as np

# from nenupytf.other import header_struct, max_bsn
max_bsn = 200e6 / 1024.
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
        idx : int

        freq_min : float
            Minimal observed frequency in MHz
        freq_max : float
            Maximal observed frequency in MHz
        time_min
        time_max

        TO CHECK... :
        timestamp : int
            Timestamp
        blockseqnumber : int
        fftlen : int
            Number of frequencies within each channel
        nfft2int : int
        fftovlp : int
        apodisation : int
        nffte : int
        nbchan : int
            Number of frequency channels
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


    @property
    def freq_min(self):
        return np.min(self._frequencies)


    @property
    def freq_max(self):
        return np.max(self._frequencies)


    @property
    def time_min(self):
        return Time(
            self._timestamps[0],
            format='unix',
            precision=7
            )


    @property
    def time_max(self):
        return Time(
            self._timestamps[-1],
            format='unix',
            precision=7
            )


    def select(self, time=None, freq=None, beam=None):
        """
        """
        time = self._check_time(time)
        freq = self._check_frequency(freq)
        beam = self._check_beam(beam)
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

        for key in [h[0] for h in header_struct]:
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
        datacube = self.memdata['data']
        self._ntb, self._nfb = datacube['lane'].shape
        self._timestamps = self.memdata['TIMESTAMP']
        self._beams = datacube['beam']
        self._channels = datacube['channel']
        self._frequencies = self._channels[0] * max_bsn * 1e-6
        return


    def _check_time(self, time):
        """
        """
        if time is None:
            time = [self._timestamps[0], self._timestamps[-1]]            
        else:
            if not isinstance(time, (list, np.ndarray)):
                raise TypeError(
                    '`time` should be an array.'
                    )
            if not len(time) == 2:
                raise IndexError(
                    '`time` should be a length 2 array.'
                    )
            t0_unix = Time(time[0], precision=7).unix
            t1_unix = Time(time[1], precision=7).unix
            if t0_unix < self._timestamps[0]:
                raise ValueError(
                    'Out of range time selection.'
                    )
            if t1_unix > self._timestamps[-1]:
                raise ValueError(
                    'Out of range time selection.'
                    )

        return time


    def _check_frequency(self, freq):
        """
        """
        return freq


    def _check_beam(self, beam):
        """
        """
        return beam
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



