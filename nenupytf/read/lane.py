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

from nenupytf.other import header_struct, max_bsn
from nenupytf.stokes import NenuStokes
from nenupytf.other import idx_of
# max_bsn = 200e6 / 1024.
# header_struct = [
#     ('idx', 'uint64'),
#     ('TIMESTAMP', 'uint64'),
#     ('BLOCKSEQNUMBER', 'uint64'),
#     ('fftlen', 'int32'),
#     ('nfft2int', 'int32'),
#     ('fftovlp', 'int32'),
#     ('apodisation', 'int32'),
#     ('nffte', 'int32'),
#     ('nbchan', 'int32')
#     ]
# def idx_of(array, value, order='low'):
#     """ Find the index of value in array.

#         REDO THIS METHOD ITS TOOOOOO FUCKIN SLOW
        
#         Parameters
#         ----------
#         array : np.ndarray
#             Array upon which to search for indices.
#         value : float
#             Value to find the index for.
#         order : str
#             Could be 'low' or 'high'.
#             Let's say array[2] < value < array[3].
#             If 'low', the result will be `2`.
#             If 'high', the result will be `3`.
#     """
#     if not order in ['low', 'high']:
#         raise ValueError(
#             '`order` should only be low or high.'
#             )
#     diff = array - value
#     if order == 'low':
#         # If value lower than anything, return index 0
#         if not np.any(array <= value):
#             return 0
#         # else, return the low value index
#         else:
#             return np.argwhere(
#                 diff == diff[diff <= 0.].max()
#                 )[0, 0]
#     elif order == 'high':
#         # If value greater than anything, return the last index
#         if not np.any(array >= value):
#             return array.size - 1
#         # else, return the high index value
#         else:
#             return np.argwhere(
#                 diff == diff[diff >= 0.].min()
#                 )[0, 0]

# l = Lane('SUN_TRACKING_20191011_100036_2.spectra')
# d = l.select(time=['2019-10-11T10:00:55.0000000', '2019-10-11T10:01:05.0000000'], freq=[30, 32])


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

        self.beam = None
        self.time = None
        self.freq = None


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
    def time(self):
        """ Selected time range

            Parameters
            ----------
            time : list
                Length-2 list of time in ISO/ISOT.
        """
        return self._time
    @time.setter
    def time(self, t):
        if t is None:
            t = [self._timestamps[0], self._timestamps[-1]]            
        else:
            if not isinstance(t, (list, np.ndarray)):
                raise TypeError(
                    '`time` should be an array.'
                    )
            if not len(t) == 2:
                raise IndexError(
                    '`time` should be a length 2 array.'
                    )
            t0_unix = Time(t[0], precision=7).unix
            t1_unix = Time(t[1], precision=7).unix
            if t0_unix < self._timestamps[0]:
                raise ValueError(
                    'Out of range time selection.'
                    )
            if t1_unix > self._timestamps[-1]:
                raise ValueError(
                    'Out of range time selection.'
                    )
            t = [t0_unix, t1_unix]

        self._time = t
        return


    @property
    def freq(self):
        """ Selected frequency range in MHz.

            Parameters
            ----------
            freq : list
                Length-2 list of frequencies
        """
        return self._freq
    @freq.setter
    def freq(self, f):
        if f is None:
            f = [self.freq_min, self.freq_max]
        else:
            if not isinstance(f, (list, np.ndarray)):
                raise TypeError(
                    '`freq` should be an array.'
                    )
            if not len(f) == 2:
                raise IndexError(
                    '`freq` should be a length 2 array.'
                    )
            if f[0] < self.freq_min:
                raise ValueError(
                    'Out of range time selection.'
                    )
            if f[1] > self.freq_max:
                raise ValueError(
                    'Out of range time selection.'
                    )

        self._freq = f
        return


    @property
    def beam(self):
        """ Selected beam index.

            Parameters
            ----------
            beam : int
                Selected beam index
        """
        return self._beam
    @beam.setter
    def beam(self, b):
        if b is None:
            b = self._beams[0]
        if not isinstance(b, np.integer):
            raise TypeError(
                '`beam` is expected to be an integer.'
                ) 
        self._beam = b
        return


    @property
    def frequencies(self):
        """ Array of frequencies in MHz corresponding
            to the selected beam.
        """
        channels = self._channels[self._beams == self.beam]
        return channels * max_bsn * 1e-6


    @property
    def freq_min(self):
        """ Minimal observed frequency in MHz
        """
        return np.min(self.frequencies)


    @property
    def freq_max(self):
        """ Maximal observed frequency in MHz
        """
        return np.max(self.frequencies)


    @property
    def time_min(self):
        """ Minimal observed time.
            `astropy.Time` object
        """
        return Time(
            self._timestamps[0],
            format='unix',
            precision=7
            )


    @property
    def time_max(self):
        """ Maximal observed time.
            `astropy.Time` object
        """
        return Time(
            self._timestamps[-1],
            format='unix',
            precision=7
            )


    def select(self, stokes='I', time=None, freq=None, beam=None):
        """
        """
        self.beam = beam
        self.time = time
        self.freq = freq
        
        tmin_idx = self._t2bidx(
            time=self.time[0],
            order='low'
            )
        tmax_idx = self._t2bidx(
            time=self.time[1],
            order='high'
            )
        fmin_idx = self._f2bidx(
            frequency=self.freq[0],
            order='low'
            )
        fmax_idx = self._f2bidx(
            frequency=self.freq[1],
            order='high'
            )
        return NenuStokes(
            data=self.memdata['data'],
            stokes=stokes,
            nffte=self.nffte,
            fftlen=self.fftlen
            )[
            tmin_idx:tmax_idx + 1,
            fmin_idx:fmax_idx + 1,
            ]


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
        self._timestamps = np.array(self.memdata['TIMESTAMP'])
        # We here assume that the same information
        # is repeated at each time block
        self._beams = datacube['beam'][0]
        self._channels = datacube['channel'][0]
        return


    def _t2bidx(self, time, order='low'):
        """ Time to block index

            Parameter
            ---------
            time : str
                Time selection in ISO or ISOT.

            Returns
            -------
            index : dict
                Dictionnary of lanes <-> block index
        """
        indices = {}
        idx = idx_of(
            array=self._timestamps,
            value=time,
            order=order
            )
        return idx


    def _f2bidx(self, frequency, order='low'):
        """ Frequency to block index

            Parameter
            ---------
            frequency : float
                Frequency selection in MHz.

            Returns
            -------
            index : dict
                Dictionnary of lanes <-> block index
        """
        idx = idx_of(
            array=self.frequencies,
            value=frequency,
            order=order
            )
        idx += np.searchsorted(self._beams, self.beam)
        return idx
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



