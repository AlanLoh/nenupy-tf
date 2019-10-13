#! /usr/bin/python3
# -*- coding: utf-8 -*-


__author__ = ['Alan Loh']
__copyright__ = 'Copyright 2019, nenupytf'
__credits__ = ['Alan Loh']
__maintainer__ = 'Alan Loh'
__email__ = 'alan.loh@obspm.fr'
__status__ = 'Production'
__all__ = [
    'ObsRepo'
    ]


import os.path as path
from glob import glob
import numpy as np

from nenupytf.read import Lane


# ============================================================= #
# -------------------------- ObsRepo -------------------------- #
# ============================================================= #
class ObsRepo(object):
    """ Class to handle a NenuFAR-TF repository.
        Once the path of the repository is given,
        it automatically search for the '*.spectra' files and
        sort the corresponding attributes with respect to the
        lane index.

        Parameters
        ----------
        repo : str
            Repository where observation files are stored.

        Attributes
        ----------
        spectra : `numpy.array`
            Array of `Lane` objects (each `Lane` is an object
            embedding memmap views of the .spectra files)
        lanes : `numpy.array`
            Array of lane indices used during the observation
        files : `numpy.array`
            Array of .spectra files that lies in the repository
    """

    def __init__(self, repo):
        self.spectra = None
        self.lanes = None
        self.files = None
        self.repo = repo


    @property
    def repo(self):
        return self._repo
    @repo.setter
    def repo(self, r):
        if not isinstance(r, str):
            raise TypeError(
                'String expected.'
                )
        self._repo = path.abspath(r)
        if not isdir(self._repo):
            raise NotADirectoryError(
                'Unable to locate {}'.format(self._repo)
                )
        self._find_spectra()
        return


    @property
    def files(self):
        return self._files
    @files.setter
    def files(self, f):
        self._files = f
        if not (f is None):
            self.spectra = np.array([
                Lane(spectrum=fi) for fi in f
                ])
        return
    

    def _find_spectra(self):
        """ Find all the .spectra files within the repo
        """
        search = join(self._repo, '*.spectra')
        self.files = np.array(glob(search))
        
        if self.spectra.size == 0:
            raise FileNotFoundError(
                'No .spectra files found!'
                )

        self.lanes = np.array([
            int(
                f.split('_')[-1].replace('.spectra', '')
                ) for f in self.files
            ])
        
        return
# ============================================================= #


