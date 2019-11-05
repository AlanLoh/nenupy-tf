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
        """
        """
        self._parameters(**kwargs)
        mask = self._bmask * self._fmask * self._tmask
        for f in self.desctab[mask]['file']:
            l = Lane(f)
            # spec = l.select(
            #         stokes=stokes,
            #         time=[to_unix(t).isot for t in self.time],
            #         freq=self.freq,
            #         beam=self.beam
            # )
            if not 'spec' in locals():
                spec = l.select(
                    stokes=stokes,
                    time=[to_unix(t).isot for t in self.time],
                    freq=self.freq,
                    beam=self.beam
                )
            else:
                spec += l.select(
                    stokes=stokes,
                    time=[to_unix(t).isot for t in self.time],
                    freq=self.freq,
                    beam=self.beam
                )
            del l
        return spec


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
