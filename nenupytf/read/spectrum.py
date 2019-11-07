#! /usr/bin/python3
# -*- coding: utf-8 -*-


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
from nenupytf.other import to_unix


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
    def select(self, stokes='I', **kwargs):
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
            spec : `~.stokes.SpecData`
                The selected data are returned via a `SpecData`
                instance, with a set of methods and attributes
                to easily get times and amplitudes in various
                units as well as some basic dynamic spectrum
                analysis tools.

            Examples
            --------
            ::
                # Load the module
                from nenupytf.read import Spectrum
                
                # Creates an instance for the observation stored
                # in a given repository  
                s = Spectrum('/path/to/observation/')
                
                # Display main informations
                s.info()

                # Data selection
                spec = s.select(
                    freq=[35, 40],
                    time=['2019-11-04T12:15:55.0000000', '2019-11-04T12:15:57.0000000'], 
                    beam=0
                )

                # Plot the data
                from nenupytf.display import plotdb
                plotdb(spec)

        """
        self._parameters(**kwargs)

        mask = self._bmask * self._fmask * self._tmask

        for f in self.desctab[mask]['file']:
            l = Lane(f)
            
            if not 'spec' in locals():
                spec = l.select(
                    stokes=stokes,
                    time=[to_unix(t).isot for t in self.time],
                    freq=self.freq,
                    beam=self.beam
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
                    beam=self.beam
                )
            
            del l
        return spec


    def average(self):
        """
        """
        return


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
