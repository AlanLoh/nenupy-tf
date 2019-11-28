#! /usr/bin/python3
# -*- coding: utf-8 -*-


"""
    ****
    Lane
    ****

    Test de docstring
"""


__author__ = ['Alan Loh']
__copyright__ = 'Copyright 2019, nenupytf'
__credits__ = ['Alan Loh']
__maintainer__ = 'Alan Loh'
__email__ = 'alan.loh@obspm.fr'
__status__ = 'Production'
__all__ = [
    'Lane'
    ]


from astropy.time import Time
import os.path as path
from os import getpid
import psutil
import numpy as np
import warnings

from nenupytf.other import header_struct, max_bsn
from nenupytf.stokes import NenuStokes, SpecData
from nenupytf.other import idx_of, to_unix, rebin1d, ProgressBar


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
        time_min : `astropy.time.Time`
            Minimal observed time
        time_max : `astropy.time.Time`
            maximal observed time

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


    def __str__(self):
        lane = 'Lane {}: '.format(self.lane)
        freq = 'freq=[{}, {}] MHz, '.format(
            self.freq_min,
            self.freq_max
            )
        time = 'time=[{}, {}], '.format(
            self.time_min.isot,
            self.time_max.isot
            )
        beam = 'beams={}'.format(
            np.unique(self._beams)
            )
        return lane + freq + time + beam


    # --------------------------------------------------------- #
    # --------------------- Getter/Setter --------------------- #
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
                Length-2 list of time in ISO/ISOT or unix.

            Returns
            -------
            time : list
                length-2 list of unix timestamps
        """
        return self._time
    @time.setter
    def time(self, t):
        if t is None:
            t = [self.time_min.unix, self.time_max.unix]            
        else:
            if not isinstance(t, (list, np.ndarray)):
                raise TypeError(
                    '`time` should be an array.'
                    )
            if not len(t) == 2:
                raise IndexError(
                    '`time` should be a length 2 array.'
                    )
            
            if isinstance(t[0], str) & isinstance(t[1], str):
                t0_unix = Time(t[0], precision=7).unix
                t1_unix = Time(t[1], precision=7).unix
            else:
                # Assume unix time
                t0_unix = t[0]
                t1_unix = t[1]

            if t0_unix < self.time_min.unix:
                warnings.warn(
                    'Out of range time selection, default values adopted.'
                )
                t0_unix = self.time_min.unix
            if t1_unix > self.time_max.unix:
                warnings.warn(
                    'Out of range time selection, default values adopted.'
                )
                t1_unix = self.time_max.unix
            if t1_unix < t0_unix:
                raise ValueError(
                    'Stop time < Start time'
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

            Returns
            -------
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
                warnings.warn(
                    'Out of range freq selection, default values adopted.'
                )
                f[0] = self.freq_min
            if f[1] > self.freq_max:
                warnings.warn(
                    'Out of range freq selection, default values adopted.'
                )
                f[1] = self.freq_max
            if f[1] < f[0]:
                raise ValueError(
                    'Max freq < Min freq'
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
        if not isinstance(b, (int, np.integer)):
            raise TypeError(
                '`beam` is expected to be an integer.'
                ) 
        if b not in self._beams:
            raise ValueError(
                'Out of range beam selection.'
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
        df = (1.0 / 5.12e-6) * 1e-6
        return np.max(self.frequencies) + df


    @property
    def time_min(self):
        """ Minimal observed time.
            `astropy.Time` object
        """
        return to_unix(self._timestamps[0])


    @property
    def time_max(self):
        """ Maximal observed time.
            `astropy.Time` object
        """
        times_per_block = self.nffte * self.fftlen * self.nfft2int
        sec_dt_block = 5.12e-6 * times_per_block
        return to_unix(self._timestamps[-1] + sec_dt_block)


    # --------------------------------------------------------- #
    # ------------------------ Methods ------------------------ #
    def select(self, stokes='I', time=None, freq=None, beam=None, bp_corr=True):
        """ Select data within a lane file.
            If the selection appears to be too big regarding
            available memory, an error should be raised.
            However as rough estimate, try to avoid time range
            of more than 15 min and/or frequency range of more
            than 10 MHz...

            Parameters
            ----------
            time : list
                Length-2 list of time range (ISO or ISOT format)
                e.g.:
                `time=['2019-03-20T11:59:00.0', '2019-03-20T12:20:00.0']`
                Default: `None` whole time range selection.
            stokes : str
                Stokes parameter required (I, Q, U, V, fracV)
                Default: `'I'`
            freq : list
                Length-2 list of frequency range (in MHz)
                e.g.:
                `freq=[30, 35]`
                Default: `None` whole frequency range selection.
            beam : int
                Beam index, refer to observation setup to see the
                details of the different observed beams.
                Default: `None` consider index 0.
            bp_corr : bool or int, optional, default: `True
                Compute the bandpass correction.
                `False`: do not compute any correction
                `True``: compute the correction with Kaiser coefficients
                `'median'`: compute a medianed correction
                `'fft'`: correct the bandpass using FFT

            Returns
            -------
            spec : `SpecData`
                SpecData object containing the time, the frequency and the data

        """
        self.beam = beam
        self.time = time
        self.freq = freq

        if self.time[1] - self.time[0] < self.dt:
            raise ValueError(
                'Time interval selected < {} sec'.format(self.dt)
            )
        if self.freq[1] - self.freq[0] < self.df:
            raise ValueError(
                'Frequency interval selected < {} MHz'.format(self.df)
            )
        
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

        self._check_memory(
            nt=tmax_idx + 1 - tmin_idx,
            nf=fmax_idx + 1 - fmin_idx
            )

        times = self._get_time(
            id_min=tmin_idx,
            id_max=tmax_idx + 1
            )
        t_mask = (times >= to_unix(self.time[0])) &\
            (times < to_unix(self.time[1]))
        
        freqs = self._get_freq(
            id_min=fmin_idx,
            id_max=fmax_idx + 1
            )
        f_mask = (freqs >= self.freq[0]) &\
            (freqs < self.freq[1])
        
        spectrum = NenuStokes(
            data=self.memdata['data'],
            stokes=stokes,
            nffte=self.nffte,
            fftlen=self.fftlen,
            bp_corr=bp_corr
            )[
            tmin_idx:tmax_idx + 1,
            fmin_idx:fmax_idx + 1,
            ]

        return SpecData(
            data=spectrum[t_mask, :][:, f_mask],
            time=times[t_mask],
            freq=freqs[f_mask],
            stokes=stokes
            )


    def average(self, stokes='I', time=None, freq=None, beam=None, dt=None, df=None):
        """ Average a dynamic spectrum in time and frequency

            Parameters
            ----------
            time : list
                Length-2 list of time range (ISO or ISOT format)
                e.g.:
                `time=['2019-03-20T11:59:00.0', '2019-03-20T12:20:00.0']`
                Default: `None` whole time range selection.
            stokes : str
                Stokes parameter required (I, Q, U, V, fracV)
                Default: `'I'`
            freq : list
                Length-2 list of frequency range (in MHz)
                e.g.:
                `freq=[30, 35]`
                Default: `None` whole frequency range selection.
            beam : int
                Beam index, refer to observation setup to see the
                details of the different observed beams.
                Default: `None` consider index 0.
            dt : float
                Time steps in seconds
            df : float
                Frequency steps in MHz

            Returns
            -------
            spec : `SpecData`
                SpecData object containing the time, the frequency and the data
        """
        self.beam = beam
        self.time = time
        self.freq = freq
        time_min, time_max = self.time
        freq_min, freq_max = self.freq
        if dt is None:
            dt = (time_max - time_min) / 1000
        if df is None:
            df = (freq_max - freq_min) / 500

        # Prepare the final array
        nt = int((time_max - time_min) // dt)
        nf = int((freq_max - freq_min) // df)
        available_memory = psutil.virtual_memory().available
        avg_data_size = nt * nf * np.dtype(np.float32).itemsize
        if avg_data_size > available_memory:
            raise MemoryError(
                'Try to increase dt and/or df'
                )
        averaged_data = np.zeros((nt, nf), dtype='float32')
        averaged_time = np.zeros(nt)#, dtype='float32')
        averaged_freq = np.zeros(nf)#, dtype='float32')
       
        # Loop over the time and seelct corresponding data
        bar = ProgressBar(valmax=nt, title='Averaging spectra...')
        for i in range(nt):
            spec = self.select(
                stokes=stokes,
                time=[time_min + i*dt, time_min + (i + 1)*dt],
                freq=freq,
                beam=beam
                )
            # Averaging data in time
            d = np.squeeze(np.mean(spec.data, axis=0))
            averaged_time[i] = to_unix(np.mean(spec.time.unix)).unix
            # Averaging in frequency
            d = rebin1d(d, nf)
            if i == 0:
                averaged_freq[:] = rebin1d(spec.freq, nf)
            # Storing into final array
            averaged_data[i, :] = d
            bar.update()
            
        # return averaged_time, averaged_freq, averaged_data
        return SpecData(
            data=averaged_data,
            time=to_unix(averaged_time),
            freq=averaged_freq,
            stokes=stokes
            )


    # --------------------------------------------------------- #
    # ----------------------- Internal ------------------------ #
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
        self.dt = 5.12e-6 * self.fftlen * self.nfft2int
        self.block_dt = self.dt * self.nffte # sec
        self.df = (1.0 / 5.12e-6 / self.fftlen) * 1e-6

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
        """ Once the file is open wia memmap, go through it
            and store information for each time, frequency,
            beam index and lane index.
        """
        datacube = self.memdata['data']
        self._ntb, self._nfb = datacube['lane'].shape
        self._timestamps = np.arange(self._ntb, dtype='float64')
        self._timestamps *= self.block_dt
        self._timestamps += self.memdata['TIMESTAMP'][0]
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


    def _get_time(self, id_min, id_max):
        """ Recover the time for a given block selection

            Parameters
            ----------
            id_min : int
                Index of starting time block
            id_max : int
                Index of ending time block

            Returns
            -------
            time : `astropy.Time`
                Time object array
        """
        n_times = (id_max - id_min) * self.nffte
        t = np.arange(n_times, dtype='float64')
        dt = t * self.dt,
        dt += self._timestamps[id_min]
        return to_unix(np.squeeze(dt))


    def _get_freq(self, id_min, id_max):
        """ Recover the frequency for a given block selection

            Parameters
            ----------
            id_min : int
                Index of starting frequency block
            id_max : int
                Index of ending frequency block

            Returns
            -------
            frequency : `np.ndarray`
                Array of frequencies in MHz
        """
        beam_shift = np.searchsorted(self._beams, self.beam)
        id_max -= beam_shift
        id_min -= beam_shift
        f = np.tile(np.arange(self.fftlen, dtype='float64'), (id_max - id_min))
        f *= self.df
        f += np.repeat(self.frequencies[id_min:id_max], self.fftlen)
        return f


    def _check_memory(self, nt, nf):
        """ Check that the requested data selection does not
            exceed the available memory. 
        """
        vm = psutil.virtual_memory()
        mem_gb = vm.available / (1024**3)

        n_elements = nt * self.nffte * nf * self.fftlen
        fftn_size = n_elements * 4 * np.dtype(np.float32).itemsize
        meta_size = n_elements * 3 * np.dtype(np.int32).itemsize
        sel_gb = (fftn_size + meta_size) / (1024**3)

        if sel_gb > mem_gb * 0.9:
            raise MemoryError(
                'Try to reduce the selection range'
                )
        return
# ============================================================= #


