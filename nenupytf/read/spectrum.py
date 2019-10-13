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

# ============================================================= #
