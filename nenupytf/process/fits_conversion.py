#! /usr/bin/python3
# -*- coding: utf-8 -*-


"""
    ***************
    fits_conversion
    ***************
"""


__author__ = ['Alan Loh']
__copyright__ = 'Copyright 2019, nenupytf'
__credits__ = ['Alan Loh']
__maintainer__ = 'Alan Loh'
__email__ = 'alan.loh@obspm.fr'
__status__ = 'Production'
__all__ = [
    'get_bst_metadata',
    'to_fits'
    ]


from astropy.io import fits
from os.path import isdir, basename, join, abspath
from glob import glob

from nenupytf.other import bst_exts
from nenupytf.stokes import SpecData


# ============================================================= #
# --------------------- get_bst_metadata ---------------------- #
# ============================================================= #
def get_bst_metadata(tfrepo):
    """ In order to understand a TF observation, one must refer
        to the corresponding BST file where all relevant meta-data
        are stored.
        This method searches for the corresponding BST file,
        assuming the path to the BST repository is the same as the
        one containing TF data but for the 'nenufar' key intstead
        of 'nenufar-tf'. This is how data are stored in nancep.

        Parameters
        ----------
        tfrepo : str
            Absolute or relative path of the TF data. 

        Returns
        -------
        metadata : dict
            Dictionnary of metadata as they are stored in the 
            BST fits file.
    """
    tfrepo = abspath(tfrepo)
    if not isdir(tfrepo):
        raise NotADirectoryError(
            'Unable to locate {}'.format(tfrepo)
            )

    # Find the corresponding BST file
    bstrepo = tfrepo.replace('nenufar-tf', 'nenufar')
    bstfiles = glob(join(bstrepo, '*BST.fits'))
    if len(bstfiles) == 0:
        raise FileNotFoundError(
            'Unable to find a BST file in {}'.format(bstrepo)
            )
    elif len(bstfiles) > 1:
        raise IndexError(
            'Too many BST files in {}'.format(bstrepo)
            )
    else:
        bst = bstfiles[0]

    # Retrieve all metadata from the BST file
    metadata = {
        e[0]: fits.getdata(bst, ext=e[1]) for e in bst_exts
    }
    metadata['header'] = fits.getheader(bst)

    return metadata


# ============================================================= #
# -------------------------- to_fits -------------------------- #
# ============================================================= #
def to_fits(specdata):
    """
    """
    if not isinstance(specdata, SpecData):
        raise TypeError(
            'Not a SpecData object'
            )

    return

