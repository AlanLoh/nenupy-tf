#! /usr/bin/python3
# -*- coding: utf-8 -*-


__author__ = ['Alan Loh']
__copyright__ = 'Copyright 2019, nenupytf'
__credits__ = ['Alan Loh']
__maintainer__ = 'Alan Loh'
__email__ = 'alan.loh@obspm.fr'
__status__ = 'Production'
__all__ = [
    'NenuStokes',
    'LaneDSpec',
    'Stokes_I',
    'Stokes_Q',
    'Stokes_U',
    'Stokes_V',
    'CrossXX',
    'CrossYY'
    ]


import numpy as np

from nenupytf.other import allowed_stokes, compute_bandpass


# ============================================================= #
# ------------------------ NenuStokes ------------------------- #
# ============================================================= #
class NenuStokes(object):
    """
    """
    def __init__(self, data, stokes, nffte, fftlen, bp_corr=True):
        self.data = data
        self.stokes = stokes
        self.nffte = nffte
        self.fftlen = fftlen
        self.ntblocks = None
        self.nfblocks = None
        self.sel_slice = None
        self.bp_corr = bp_corr


    def __getitem__(self, slice_val):
        self.sel_slice = slice_val
        
        if self.stokes == 'i':
            data = Stokes_I(self.data)[slice_val]
        elif self.stokes == 'q':
            data = Stokes_Q(self.data)[slice_val]
        elif self.stokes == 'u':
            data = Stokes_U(self.data)[slice_val]
        elif self.stokes == 'v':
            data = Stokes_V(self.data)[slice_val]
        elif self.stokes == 'fracv':
            stokes_i = Stokes_I(self.data)[slice_val]
            stokes_v = Stokes_V(self.data)[slice_val]
            data = stokes_v/stokes_i
        elif self.stokes == 'xx':
            data = CrossXX(self.data)[slice_val]
        elif self.stokes == 'yy':
            data = CrossYY(self.data)[slice_val]
        elif self.stokes == 'argxy':
            re = Stokes_U(self.data)[slice_val]
            im = Stokes_V(self.data)[slice_val]
            data = np.abs( re + 1j * im)
        elif self.stokes == 'phasexy':
            re = Stokes_U(self.data)[slice_val]
            im = Stokes_V(self.data)[slice_val]
            data = np.angle( re + 1j * im)

        return self.correct(
            data=data,
            bandpass=self.bp_corr
            )


    @property
    def sel_slice(self):
        return self._sel_slice
    @sel_slice.setter
    def sel_slice(self, s):
        if s is None:
            return
        if len(s) != 2:
            raise ValueError(
                '2D slice expected.'
                )
        self.ntblocks = s[0].stop - s[0].start
        self.nfblocks = s[1].stop - s[1].start
        self._sel_slice = s
        return

    @property
    def stokes(self):
        return self._stokes
    @stokes.setter
    def stokes(self, s):
        if not isinstance(s, str):
            raise TypeError('String expected.')
        self._stokes = s.lower()
        if self._stokes not in allowed_stokes:
            raise ValueError('Wrong Stokes parameter.')


    def correct(self, data, bandpass=True):
        """ Transfom the data into a 2D array of time-frquency
            Invert the halves of each beamlet
            Correct for bandpass
        """
        # Make a 2D array
        data = np.swapaxes(data, 1, 2)
        n_times = self.ntblocks * self.nffte
        n_freqs = self.nfblocks * self.fftlen

        # Invert the halves of the beamlet
        if self.fftlen % 2. != 0.0:
            raise ValueError('Problem with fftlen value!')
        data = data.reshape(
            (
                n_times,
                int(n_freqs/self.fftlen),
                2,
                int(self.fftlen/2)
            )
        )
        data = data[:, :, ::-1, :].reshape((n_times, n_freqs))

        # Bandpass correction
        if bandpass:

            if bandpass == 'median': 
                spectrum = np.median(data, axis=0)
                folded = spectrum.reshape(
                    (int(spectrum.size / self.fftlen), self.fftlen)
                    )
                broadband = np.median(folded, axis=1)
                broadband = np.repeat(broadband, self.fftlen)
                return data / spectrum * broadband

            elif bandpass == 'fft':
                from scipy.signal import find_peaks
                bp_fft = np.fft.fft(data)
                # Find peaks
                avg_fft = np.mean(np.abs(bp_fft), axis=0)
                p_idx, meta = find_peaks(
                    x=avg_fft,
                    height=np.median(avg_fft) * 2.
                )
                # Put to zero peaks and neighbouring slices
                p_idx = np.concatenate(
                    (p_idx, p_idx + 1, p_idx - 1)
                )
                bp_fft[:, p_idx] = 0.
                return np.abs(np.fft.ifft(bp_fft))

            else:
                bp = compute_bandpass(self.fftlen)
                data = data.reshape(
                    (
                        n_times,
                        int(n_freqs/bp.size),
                        bp.size
                    )
                )
                data *= bp[np.newaxis, np.newaxis]
                return data.reshape((n_times, n_freqs))

        else:
            return data
# ============================================================= #


# ============================================================= #
# ------------------------- LaneDSpec ------------------------- #
# ============================================================= #
class LaneDSpec(object):
    """
    """

    def __init__(self, data):
        self.fft0 = None
        self.fft1 = None
        self.mem_data = data


    @property
    def mem_data(self):
        return self._mem_data
    @mem_data.setter
    def mem_data(self, d):
        """ NenuFAR TF read data.
        """
        if not isinstance(d, np.memmap):
            raise TypeError('Expecting a numpy.memmap object.')
        
        ffts = ['fft0', 'fft1']
        if not all([fft in d.dtype.names for fft in ffts]):
            raise ValueError('Wrong level of data.')

        self._get_parameters(d)

        self._mem_data = d
        return


    def _get_parameters(self, data):
        """
        """
        self.fft0 = data['fft0']
        self.fft1 = data['fft1']
        return
# ============================================================= #


# ============================================================= #
# ------------------------- Stokes_I -------------------------- #
# ============================================================= #
class Stokes_I(LaneDSpec):
    """
    """

    def __init__(self, data):
        super().__init__(data=data)


    def __getitem__(self, slice_val):
        selection = np.sum(self.fft0[slice_val], axis=4)
        return selection
# ============================================================= #


# ============================================================= #
# ------------------------- Stokes_Q -------------------------- #
# ============================================================= #
class Stokes_Q(LaneDSpec):
    """
    """

    def __init__(self, data):
        super().__init__(data=data)


    def __getitem__(self, slice_val):
        selection = self.fft0[slice_val]
        selection = selection[..., 0] - selection[..., 1]
        return selection
# ============================================================= #


# ============================================================= #
# ------------------------- Stokes_U -------------------------- #
# ============================================================= #
class Stokes_U(LaneDSpec):
    """
    """

    def __init__(self, data):
        super().__init__(data=data)


    def __getitem__(self, slice_val):
        selection = self.fft1[slice_val]
        selection = selection[..., 0] * 2
        return selection
# ============================================================= #


# ============================================================= #
# ------------------------- Stokes_V -------------------------- #
# ============================================================= #
class Stokes_V(LaneDSpec):
    """
    """

    def __init__(self, data):
        super().__init__(data=data)


    def __getitem__(self, slice_val):
        selection = self.fft1[slice_val]
        selection = selection[..., 1] * (-2)
        return selection
# ============================================================= #


# ============================================================= #
# -------------------------- CrossXX -------------------------- #
# ============================================================= #
class CrossXX(LaneDSpec):
    """
    """

    def __init__(self, data):
        super().__init__(data=data)


    def __getitem__(self, slice_val):
        selection = self.fft0[slice_val]
        return selection[..., 0] * 2
# ============================================================= #


# ============================================================= #
# -------------------------- CrossYY -------------------------- #
# ============================================================= #
class CrossYY(LaneDSpec):
    """
    """

    def __init__(self, data):
        super().__init__(data=data)


    def __getitem__(self, slice_val):
        selection = self.fft0[slice_val]
        return selection[..., 1] * 2
# ============================================================= #

