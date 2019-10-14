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


from nenupytf.read import ObsRepo


# ============================================================= #
# ------------------------- Spectrum -------------------------- #
# ============================================================= #
class Spectrum(ObsRepo):
    """
    """

    def __init__(self, directory):
        super().__init__(repo=directory)


    def select(self, **kwargs):
        """
        """
        for lane, lspectrum in zip(self.lanes, self.spectra):
            ...
        self._parameters(kwargs)
        return


    def _parameters(self, **kwargs):
        """ Read the selection parameters
        """
        self.selbeam = kwargs.get('beam', 0)
        t_default = []
        self.selfreq = kwargs.get('time', t_default)
        f_default = []
        self.seltime = kwargs.get('frequency', f_default)
        return
# ============================================================= #
