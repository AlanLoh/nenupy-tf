#! /usr/bin/python3
# -*- coding: utf-8 -*-


__author__ = ['Alan Loh']
__copyright__ = 'Copyright 2019, nenupytf'
__credits__ = ['Alan Loh']
__maintainer__ = 'Alan Loh'
__email__ = 'alan.loh@obspm.fr'
__status__ = 'Production'
__all__ = [
    'idx_of'
    ]


def idx_of(array, value, order='low'):
    """ Find the index of value in array.
        
        Parameters
        ----------
        array : np.ndarray
            Array upon which to search for indices.
        value : float
            Value to find the index for.
        order : str
            Could be 'low' or 'high'.
            Let's say array[2] < value < array[3].
            If 'low', the result will be `2`.
            If 'high', the result will be `3`.
    """
    if not order in ['low', 'high']:
        raise ValueError(
            '`order` should only be low or high.'
            )
    diff = array - value
    if order == 'low':
        # If value lower than anything, return index 0
        if not np.any(array <= value):
            return 0
        # else, return the low value index
        else:
            return np.argwhere(
                diff == diff[diff <= 0.].max()
                )[0, 0]
    elif order == 'high':
        # If value greater than anything, return the last index
        if not np.any(array >= value):
            return array.size - 1
        # else, return the high index value
        else:
            return np.argwhere(
                diff == diff[diff >= 0.].min()
                )[0, 0]


