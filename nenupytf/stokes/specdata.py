#! /usr/bin/python3
# -*- coding: utf-8 -*-


__author__ = ['Alan Loh']
__copyright__ = 'Copyright 2019, nenupytf'
__credits__ = ['Alan Loh']
__maintainer__ = 'Alan Loh'
__email__ = 'alan.loh@obspm.fr'
__status__ = 'Production'
__all__ = [
    'SpecData',
    ]


from astropy.time import Time
import numpy as np


# ============================================================= #
# ------------------------- SpecData -------------------------- #
# ============================================================= #
class SpecData(object):
    """ A class to handle dynamic spectrum data
    """

    def __init__(self, data, time, freq):
        self.time = time
        self.freq = freq
        self.data = data


    def __repr__(self):
        return self.data.__repr__()


    # --------------------------------------------------------- #
    # --------------------- Getter/Setter --------------------- #
    @property
    def data(self):
        return self._data
    @data.setter
    def data(self, d):
        ts, fs = d.shape
        assert self.time.size == ts,\
            'time axis inconsistent'
        assert self.freq.size == fs,\
            'frequency axis inconsistent'
        self._data = d
        return


    @property
    def time(self):
        return self._time
    @time.setter
    def time(self, t):
        if not isinstance(t, Time):
            raise TypeError('Time object expected')
        self._time = t
        return


    @property
    def mjd(self):
        """ Return MJD dates
        """
        return self.time.mjd


    @property
    def jd(self):
        """ Return JD dates
        """
        return self.time.jd


    @property
    def amp(self):
        """ Linear amplitude of the data
        """
        return self.data.squeeze()

    
    @property
    def db(self):
        """ Convert the amplitude in decibels
        """
        return 10 * np.log10(self.data.squeeze())


    # --------------------------------------------------------- #
    # ------------------------ Methods ------------------------ #
    def fmean(self, freq1=None, freq2=None, method='mean', clean=False):
        """ Average over the frequency.
            
            Parameters
            ----------

            freq1 : float
                Lower frequency bound in MHz.

            freq2 : float
                Upper frequency bound in MHz.

            method : str
                Method used to average (either 'mean' or 'median')

            clean : bool
                Apply a cleaning before averaging

            Returns
            -------

            averaged_data : SpecData
                A new `SpecData` instance containging the averaged quantities.
        """
        if freq1 is None:
            freq1 = self.freq.min()
        else:
            freq1 *= u.MHz
        if freq2 is None:
            freq2 = self.freq.max()
        else:
            freq2 *= u.MHz
        fmask = (self.freq >= freq1) & (self.freq <= freq2)
        
        data = self.data[:, fmask]
        if clean:
            # Find out the noisiest profiles
            sigmas = np.std(data, axis=0)
            max_sig = np.percentile(sigmas, 90, axis=1)
            data = data[:, np.newaxis, sigmas < max_sig]

            # Smoothin' the time profiles
            from scipy.signal import savgol_filter
            tf = np.zeros(data.shape)
            for j in range(sigmas[sigmas < max_sig].size):
                tf[:, i, j] = savgol_filter(data[:, j], 201, 1)

            # Rescale everything not to bias the mean
            data = tf - (np.median(tf, axis=0) - np.median(tf))

        average = np.mean(data, axis=2)\
            if method == 'mean'\
            else np.median(data, axis=2)

        return SpecData(
            data=np.expand_dims(average, axis=1),
            time=self.time.copy(),
            freq=np.expand_dims(np.mean(self.freq[fmask]), axis=0)
            )


    def tmean(self, t1=None, t2=None):
        """ Average over the time.
            
            Parameters
            ----------

            t1 : str
                Lower time bound in ISO/ISOT format.

            t2 : str
                Upper time bound in ISO/ISOT format.

            Returns
            -------

            averaged_data : SpecData
                A new `SpecData` instance containging the averaged quantities.
        """
        if t1 is None:
            t1 = self.time[0]
        else:
            t1 = np.datetime64(t1)
        if t2 is None:
            t2 = self.time[-1]
        else:
            t2 = np.datetime64(t2)
        tmask = (self.time >= t1) & (self.time <= t2)
        tmasked = self.time[tmask]
        dt = (tmasked[-1] - tmasked[0])
        mean = np.mean(self.data[tmask, :, :], axis=0)
        return SpecData(
            data=np.expand_dims(mean, axis=0),
            time=np.array([tmasked[0] + dt/2.]),
            freq=self.freq.copy()
            )


    def filter(self, kernel=7):
        """ Remove the spikes

            Parameters
            ----------

            kernel : array_like
                A scalar or an N-length list giving the size 
                of the median filter window in each dimension. 
                Elements of kernel_size should be odd. 
                If kernel_size is a scalar, then this scalar is 
                used as the size in each dimension. Default size 
                is 3 for each dimension.
        """
        from scipy.signal import medfilt
        if (self.data.shape[1] == 1) and (not isinstance(kernel, list)):
            kernel = [kernel, 1]
        filtered_data = np.zeros(self.data.shape)
        tf = medfilt(self.data[:, :], kernel)
        filtered_data[:, :] = tf
        return SpecData(
            data=filtered_data,
            time=self.time.copy(),
            freq=self.freq.copy()
            )


    def bg_remove(self, kernel=11, sigma=3):
        """ Remove the background

            Parameters
            ----------

            kernel : array_like
                A scalar or an N-length list giving the size 
                of the median filter window in each dimension. 
                Elements of kernel_size should be odd. 
                If kernel_size is a scalar, then this scalar is 
                used as the size in each dimension. Default size 
                is 3 for each dimension.
        """
        from scipy.signal import medfilt
        if (self.data.shape[1] == 1) and (not isinstance(kernel, list)):
            kernel = [kernel, 1]
        filtered_data = np.zeros(self.data.shape)

        tf = medfilt(self.data[:, :], kernel)
        sig = np.std(self.data[:, :])
        bad = (np.abs(self.data[:, :] - tf) / sig) > sigma
        tf[~bad] = self.data[:, :].copy()[~bad]
        filtered_data[:, :] = tf

        return SpecData(
            data=filtered_data,
            time=self.time.copy(),
            freq=self.freq.copy(),
            polar=self.polar.copy())
# ============================================================= #


