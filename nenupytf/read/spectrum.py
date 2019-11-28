#! /usr/bin/python3
# -*- coding: utf-8 -*-


"""
    ********
    Spectrum
    ********

    Test de docstring
"""


__author__ = ['Alan Loh']
__copyright__ = 'Copyright 2019, nenupytf'
__credits__ = ['Alan Loh']
__maintainer__ = 'Alan Loh'
__email__ = 'alan.loh@obspm.fr'
__status__ = 'Production'
__all__ = [
    'Spectrum'
    ]


from nenupytf.read import ObsRepo, Lane
from nenupytf.stokes import SpecData
from nenupytf.other import to_unix, ProgressBar

import numpy as np


# ============================================================= #
# ------------------------- Spectrum -------------------------- #
# ============================================================= #
class Spectrum(ObsRepo):
    """
    """

    def __init__(self, directory):
        super().__init__(repo=directory)
        self.beam = None
        self.freq = None
        self.time = None


    # --------------------------------------------------------- #
    # --------------------- Getter/Setter --------------------- #
    @property
    def beam(self):
        return self._beam
    @beam.setter
    def beam(self, b):
        if b is None:
            b = self.desctab['beam'][0]
        self._beam = b
        self._bmask = (self.desctab['beam'] == b)
        return


    @property
    def time(self):
        """ Time range selection.

            This attribute can be set either directly or via
            specific keyword arguments in :func:`select()` and
            :func:`average()`.

            :setter: Length-2 list defining the selected time
                range: `[time_min, time_max]` where `time_min`
                and `time_max` are in ISO/ISOT formats
            
            :getter: Time range
            
            :type: list

            :Example:
            
            >>> from nenupytf.read import Spectrum
            >>> s = Spectrum('/path/to/observation/')
            >>> s.time = ['2019-10-03 14:30:00', '2019-10-03 18:31:01.34']
        """
        return self._time.copy()
    @time.setter
    def time(self, t):
        tmin = self.desctab['tmin']
        tmax = self.desctab['tmax']
        if t is None:
            t = [
                    tmin.min(),
                    tmax.max()
                ]
        else:
            t = [to_unix(ti).unix for ti in t]
        if len(t) != 2:
            raise IndexError(
                'time should be a length 2 list'
                )
        self._time = t
        self._tmask = ((tmin <= t[0]) * (t[0] <= tmax)) +\
            ((t[0] <= tmin) * (tmin <= t[1]))
        return


    @property
    def freq(self):
        return self._freq.copy()
    @freq.setter
    def freq(self, f):
        fmin = self.desctab['fmin']
        fmax = self.desctab['fmax']
        if f is None:
            f = [
                    fmin.min(),
                    fmax.max()
                ]
        if len(f) != 2:
            raise IndexError(
                'freq should be a length 2 list'
                )
        self._freq = f
        self._fmask = ((fmin <= f[0]) * (f[0] <= fmax)) +\
            ((f[0] <= fmin) * (fmin <= f[1]))
        return


    # --------------------------------------------------------- #
    # ------------------------ Methods ------------------------ #
    def select(self, stokes='I', bp_corr=True, **kwargs):
        """ Select among the data stored in the directory according
            to a time range, a frequency range and a beam index
            and return them converted in the chosen Stokes parameter.
            NenuFAR-TF data can be spread over several lane files.
            This will select the data nonetheless and concatenate
            what is needed to ouptut a single `SpecData` object.

            This may be usefull to call for `.info()` method prior
            to select the data in order to know the time and 
            frequency boundaries of the observation as well as 
            recorded beam indices.

            Parameters
            ----------
            stokes : {'I', 'Q', 'U', 'V', 'fracV'}, optional, default: 'I'
                Stokes parameter value to convert raw data to.
            bp_corr : bool or int, optional, default: `True
                Compute the bandpass correction.
                `False`: do not compute any correction
                `True``: compute the correction with Kaiser coefficients
                `'median'`: compute a medianed correction
                `'fft'`: correct the bandpass using FFT

            Other Parameters
            ----------------
            **kwargs
                Data selection can be applied on three parameters,
                namely `freq`, `time` and `beam`.
                - freq : list, optional, default: [fmin, fmax]
                    Frequency range in MHz passed as a lenght-2
                    list.
                - time : list, optional, default: [tmin, tmax]
                    Time range in ISOT or ISO format passed as
                    a length-2 list.
                - beam : int, optional, default: 0
                    Beam index.

            Returns
            -------
            spec : :py:class:`.SpecData`
                The selected data are returned via a `SpecData`
                instance, with a set of methods and attributes
                to easily get times and amplitudes in various
                units as well as some basic dynamic spectrum
                analysis tools.

            Examples
            --------
                Load the module
                >>> from nenupytf.read import Spectrum
                
                Creates an instance for the observation stored
                in a given repository  
                >>> s = Spectrum('/path/to/observation/')
                
                Display main informations
                >>> s.info()

                Data selection
                >>> spec = s.select(
                        freq=[35, 40],
                        time=['2019-11-04T12:15:55.0000000', '2019-11-04T12:15:57.0000000'], 
                        beam=0
                    )

                Plot the data
                >>> from nenupytf.display import plotdb
                >>> plotdb(spec)

        """
        self._parameters(**kwargs)

        mask = self._bmask * self._fmask * self._tmask
        if all(~mask):
            raise ValueError(
                'Empty selection, check parameter ranges'
            )

        for f in self.desctab[mask]['file']:
            l = Lane(f)
            
            if not 'spec' in locals():
                spec = l.select(
                    stokes=stokes,
                    time=[to_unix(t).isot for t in self.time],
                    freq=self.freq,
                    beam=self.beam,
                    bp_corr=bp_corr
                )

            else:
                # We assume here that the time is the same,
                # only frequency is spread over different lanes.
                # This will concatenate spectra from different
                # lanes:
                spec = spec & l.select(
                    stokes=stokes,
                    time=[to_unix(t).isot for t in self.time],
                    freq=self.freq,
                    beam=self.beam,
                    bp_corr=bp_corr
                )

            del l
        return spec


    def average(self, stokes='I', df=1, dt=1, bp_corr=True, **kwargs):
        """ Average in time and frequency *NenuFAR/UnDySPuTeD* high
            rate time-frequency data.

            :param stokes: Stokes parameter value to convert raw data to
            :param df: Frequency resolution in MHz on which
                the averaging is performed
            :param dt: Time resolution in seconds on which
                the average is performed
            :param bp_corr: Compute the bandpass correction
            
            :type stokes: str
            :type df: int, float
            :type dt: int, float
            :type bp_corr: bool
            
            :returns: `SpecData` object, embedding the stackev averaged spectra
            :rtype: :class:`.SpecData`

            :Example:
            
            >>> from nenupytf.read import Spectrum
            >>> s = Spectrum('/path/to/observation/')
            >>> spec = s.average(
                    time=['2019-10-03 14:30:00', '2019-10-03 18:31:01.34'],
                    freq=[34.5, 40],
                    dt=0.01,
                    df=0.5,
                    stokes='I'
                )

            .. note:: can be useful to emphasize
                important feature
            .. seealso:: :func:`select()` :class:`.SpecData`
            .. warning:: This may take a significant time to process
                depending on the time and frequency ranges and the
                required time and frequency resolution
        """
        self._parameters(**kwargs)

        # Keep track of inputs parameters
        beam = self.beam
        freq = self.freq.copy()
        time = self.time.copy()
        
        start, stop = time

        # # No predefined array
        # bar = ProgressBar(
        #     valmax=(stop-start)/dt,
        #     title='Averaging...')
        # while start <= stop:
        #     if not 'spec' in locals():
        #         spec = self.select(
        #             stokes=stokes,
        #             time=[start, start+dt],
        #             freq=freq,
        #             beam=beam
        #         ).tmean().frebin((freq[1]-freq[0])/df)
        #     else:
        #         spec = spec | self.select(
        #             stokes=stokes,
        #             time=[start, start+dt],
        #             freq=freq,
        #             beam=beam
        #         ).tmean().frebin((freq[1]-freq[0])/df)
        #     start += dt
        #     bar.update()

        # Predefined array
        ntimes = int(np.ceil((stop - start)/dt))
        nfreqs = int((freq[1]-freq[0])/df)
        avg_data = np.zeros(
            (ntimes, nfreqs)
        )
        avg_time = np.zeros(ntimes)
        avg_freq = np.zeros(nfreqs)
        i = 0
        bar = ProgressBar(
            valmax=ntimes,
            title='Averaging...')
        while start < stop - dt:
            tmp_spec = self.select(
                stokes=stokes,
                time=[start, start+dt],
                freq=freq,
                beam=beam,
                bp_corr=bp_corr,
            ).tmean().frebin((freq[1]-freq[0])/df)
            avg_data[i, :] = tmp_spec.amp
            avg_time[i] = start + dt/2
            avg_freq = tmp_spec.freq
            i += 1
            start += dt
            bar.update()
        spec = SpecData(
            data=avg_data,
            time=to_unix(avg_time),
            freq=avg_freq,
            stokes=stokes
            )

        return spec


    # --------------------------------------------------------- #
    # ----------------------- Internal ------------------------ #
    def _parameters(self, **kwargs):
        """ Read the selection parameters
        """
        for key, value in kwargs.items():
            if key == 'beam':
                self.beam = value
            if key == 'freq':
                self.freq = value
            if key == 'time':
                self.time = value
        return
# ============================================================= #
