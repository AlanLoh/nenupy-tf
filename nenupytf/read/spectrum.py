#! /usr/bin/python3
# -*- coding: utf-8 -*-


"""
    ********
    Spectrum
    ********


    The :mod:`.read` module contains two main object classes,
    namely :class:`.Lane` and :class:`.Spectrum`.
    Both are aiming at easy data selection from *NenuFAR/UnDySPuTeD*
    binary files, which are created one for each lane of the backend,
    depending on the observation setup.
    
    The former is working at the lowest file level, hence handling 
    *NenuFAR/UnDySPuTeD* files independently from one another.

    :class:`.Spectrum` is a higher level object class, able to work on
    different files from a given observation. Therefore, if for example,
    a particular observed beam is spread over two lane files (each one
    covering half of the frequency bandwidth), a full frequency selection
    would return data gathered from those two files.
    To do so, :class:`.Spectrum` first determine which files are 
    encompassing the data selection and then calls for :class:`.Lane`
    to perform the refined selection.

    
    **Initialization**
    
    The :class:`.Spectrum` object needs to be provided with a path to
    an observation directory, for e.g., ``'/path/to/observation'``, by
    default the current directory is used.

    >>> from nenupytf.read import Spectrum
    >>> spectrum = Spectrum('/path/to/observation') 


    **Data selection**

    High-rate time-frequency data can be selected among different
    parameters (handled as attributes of the class :class:`.Spectrum`),
    namely: :attr:`Spectrum.beam`, :attr:`Spectrum.time` and
    :attr:`Spectrum.freq`. These attributes can also be set while
    they are passed as keyword arguments in :func:`Spectrum.select`
    and :func:`Spectrum.average`.

    Observation parameters can be quickly displayed to ease the
    parameter selection thanks to :func:`.info`:

    >>> spectrum.info()

    * :attr:`Spectrum.beam` defines the selected beam index.
    * :attr:`Spectrum.time` defines the selection time range.
    * :attr:`Spectrum.freq` defines the selection frequency range.


    **Polyphase filter correction**
    
    Reconstructed sub-bands may not display a flat bandpass due
    to polyphase filter response. It may be usefull to correct
    for this effect and reduce dynamic spectra artefacts.

    Several correction options are available, set by user at the 
    :func:`Spectrum.select` and :func:`Spectrum.average` function
    levels with the :attr:`bp_corr` keyword. By default, this
    keyword is set to ``bp_corr=True`` to apply a precomputed
    correction. The default option is pretty fast to apply and is
    convenient in most situations although it may leave smal 
    artefacts at the sub-band edges. Same kind of artefacts
    are present if ``bp_corr='fft'``, however the computation
    time is increased as the sub-band bandpasses are corrected
    within the Fourier domain. ``bp_corr='median'`` correction
    allows for most reduced aretfacts. However, the latter may
    significantly alter the signal if the dynamic spectrum is not
    relatively smooth, use with caution! 
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
    """ :class:`Spectrum` is the class designed to work with
        several lane files from the *UnDySPuTeD* backend. Once 
        instanciated, a `Spectrum` object has a view of all file
        informations within the :attr:`directory`. This means 
        that a selection may involve several lane files to search
        for data, regardless of the lane index.

        :param directory: Directory where observation files are
            stored
        :type directory: str, optional

        :Example:
        >>> from nenupytf.read import Spectrum
        >>> s = Spectrum('/path/to/observation/')
    """

    def __init__(self, directory=''):
        super().__init__(repo=directory)
        self.beam = None
        self.freq = None
        self.time = None


    # --------------------------------------------------------- #
    # --------------------- Getter/Setter --------------------- #
    @property
    def beam(self):
        """ Beam selection.

            This attribute can be set either directly or via
            specific keyword arguments in :func:`select()` and
            :func:`average()`.

            Default value is `0`.
            
            :setter: Beam index
            
            :getter: Beam index
            
            :type: int

            :Example:
            
            >>> from nenupytf.read import Spectrum
            >>> s = Spectrum('/path/to/observation/')
            >>> s.beam = 1
        """
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

            Default value is `[obs_tmin, obs_tmax]`

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
        """ Frequency range selection.
            
            This attribute can be set either directly or via
            specific keyword arguments in :func:`select()` and
            :func:`average()`.

            Default value is `[obs_fmin, obs_fmax]`

            :setter: Length-2 list defining the selected frequency
                range: `[freq_min, freq_max]` where `freq_min`
                and `freq_max` are in MHz
            
            :getter: Frequency range
            
            :type: list

            :Example:
            
            >>> from nenupytf.read import Spectrum
            >>> s = Spectrum('/path/to/observation/')
            >>> s.freq = [54, 66]
        """
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
        r""" Select among the data stored in the directory 
            according to a :attr:`Spectrum.time` range, a
            :attr:`Spectrum.freq` range and a 
            :attr:`Spectrum.beam` index and return them converted
            in the chosen Stokes parameter. NenuFAR-TF data can
            be spread over several lane files. This will select
            the data nonetheless and concatenate what is needed
            to ouptut a single :class:`.SpecData` object.

            This may be usefull to call for :func:`ObsRepo.info()`
            method prior to select the data in order to know the
            time and frequency boundaries of the observation as
            well as recorded beam indices.

            :param stokes:
                Stokes parameter value to convert raw data to,
                allowed values are `{'I', 'Q', 'U', 'V', 'fracV',
                'XX', 'YY'}`, defaults to `'I'`
            :type stokes: str, optional
            :param bp_corr:
                Compute the bandpass correction, defaults to
                `True`, possible values are 

                * `False`: do not compute any correction
                * `True`: compute the correction with Kaiser
                coefficients
                * `'median'`: compute a medianed correction
                * `'fft'`: correct the bandpass using FFT

            :type bp_corr: bool, str, optional
            :param \**kwargs:
                See below for keyword arguments:
            :param freq:
                Frequency range in MHz passed as a lenght-2 list.
            :type freq: list, optional
            :param time:
                Time range in ISOT or ISO format passed as a
                length-2 list.
            :type time: list, optional
            :param beam:
                Beam index.
            :type beam: int, optional

            :returns: `SpecData` object, embedding the stacked
                averaged spectra
            :rtype: :class:`.SpecData`

            :Example:
            
            >>> from nenupytf.read import Spectrum
            >>> s = Spectrum('/path/to/observation/')
            >>> spec = s.select(
                    time=['2019-10-03 14:30:00', '2019-10-03 14:30:10.34'],
                    freq=[34.5, 40],
                    stokes='I'
                )

            .. seealso:: :func:`average()` :class:`.SpecData`
            .. warning:: This may take a significant time to
                process depending on the time and frequency
                ranges.
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


    def average(
            self,
            stokes='I',
            df=1.,
            dt=1.,
            bp_corr=True,
            **kwargs
        ):
        r""" Average in time and frequency *NenuFAR/UnDySPuTeD*
            high rate time-frequency data.

            Data are read by time blocks of size `dt` before
            averaging by computing the mean over time. Then, the
            spectrum is rebinned to a reconstructed frequency
            axis with spaces around `df`.

            :param stokes:
                Stokes parameter value to convert raw data to,
                allowed values are `{'I', 'Q', 'U', 'V', 'fracV',
                'XX', 'YY'}`, defaults to `'I'`
            :type stokes: str, optional
            :param df:
                Frequency resolution in MHz on which the
                averaging is performed, defaults to `1.`
            :type df: int, float, optional
            :param dt:
                Time resolution in seconds on which the average
                is performed, defaults to `1.`
            :type dt: int, float, optional
            :param bp_corr:
                Compute the bandpass correction, defaults to
                `True`, possible values are 

                * `False`: do not compute any correction
                * `True`: compute the correction with Kaiser
                    coefficients
                * `'median'`: compute a medianed correction
                * `'fft'`: correct the bandpass using FFT

            :type bp_corr: bool, str, optional
            :param \**kwargs:
                See below for keyword arguments:
            :param freq:
                Frequency range in MHz passed as a lenght-2 list.
            :type freq: list, optional
            :param time:
                Time range in ISOT or ISO format passed as a
                length-2 list.
            :type time: list, optional
            :param beam:
                Beam index.
            :type beam: int, optional

            :returns: `SpecData` object, embedding the stacked
                averaged spectra
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

            .. seealso:: :func:`select()` :class:`.SpecData`
            .. warning:: This may take a significant time to
                process depending on the time and frequency
                ranges and the required time and frequency
                resolution.
        """
        self._parameters(**kwargs)

        # Keep track of inputs parameters
        beam = self.beam
        freq = self.freq.copy()
        time = self.time.copy()
        
        start, stop = time

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
