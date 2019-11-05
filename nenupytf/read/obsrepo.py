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
        self.desc = {}
        self.spectra = None
        self.lanes = None
        self.files = None
        self.repo = repo


    # --------------------------------------------------------- #
    # --------------------- Getter/Setter --------------------- #
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
        if not path.isdir(self._repo):
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
        return


    @property
    def lanes(self):
        return self._lanes
    @lanes.setter
    def lanes(self, l):
        self._lanes = l
        if l is None:
            return
        for la, fi in zip(l, self.files):
            s = Lane(spectrum=fi)
            self.desc[str(la)] = {
                'tmin': s.time_min,
                'tmax': s.time_max,
                'fmin': s.freq_min,
                'fmax': s.freq_max,
                'beam': np.unique(s._beams),
                'file': fi
            }
            del s
        return
    

    @property
    def desctab(self):
        """ Numpy array of description,
            usefull for masking purposes...
        """
        max_len = 0
        desc_list = []
        for k, v in self.desc.items():
            if len(v['file']) > max_len:
                max_len = len(v['file'])
            for b in v['beam']:
                desc_list.append(
                    (
                        int(k),
                        b,
                        v['tmin'].unix,
                        v['tmax'].unix,
                        v['fmin'],
                        v['fmax'],
                        v['file'])
                )

        dtype = [
            ('lane', 'u4'),
            ('beam', 'u4'),
            ('tmin', 'f8'),
            ('tmax', 'f8'),
            ('fmin', 'f8'),
            ('fmax', 'f8'),
            ('file', 'U{}'.format(max_len))
            ]

        d = np.array(
            desc_list,
            dtype=dtype
        )
        return d


    # --------------------------------------------------------- #
    # ------------------------ Methods ------------------------ #
    def info(self):
        """ Display the informations regarding the observation
        """
        for l, desc in self.desc.items():
            print('\n--------------- nenupytf ---------------')
            print('Info on {}'.format(desc['file']))
            print('Lane: {}'.format(l))
            print('Time: {} -- {}'.format(
                desc['tmin'].isot,
                desc['tmax'].isot
                ))
            print('Frequency: {} -- {} MHz'.format(
                desc['fmin'],
                desc['fmax']
                ))
            print('Beams: {}'.format(desc['beam']))
            print('----------------------------------------\n')
        return


    # --------------------------------------------------------- #
    # ----------------------- Internal ------------------------ #
    def _find_spectra(self):
        """ Find all the .spectra files within the repo
        """
        search = path.join(self._repo, '*.spectra')
        self.files = np.array(glob(search))
        
        if self.files.size == 0:
            raise FileNotFoundError(
                'No .spectra files found!'
                )

        self.lanes = np.array([
            int(
                f.split('_')[-1].replace('.spectra', '')
                ) for f in self.files
            ],
            dtype=int)
        
        return
# ============================================================= #


