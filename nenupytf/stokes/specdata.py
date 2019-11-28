#! /usr/bin/python3
# -*- coding: utf-8 -*-


"""
    ********
    SpecData
    ********

    Test de docstring
"""


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

    def __init__(self, data, time, freq, **kwargs):
        self.time = time
        self.freq = freq
        self.data = data
        self.meta = kwargs


    def __repr__(self):
        return self.data.__repr__()


    def __and__(self, other):
        """ Concatenate two SpecData object in frequency
        """
        if not isinstance(other, SpecData):
            raise TypeError(
                'Trying to concatenate something else than SpecData'
                )
        if 'stokes' in self.meta.keys():
            if self.meta['stokes'] != other.meta['stokes']:
                raise ValueError(
                    'Inconsistent Stokes parameters'
                    )

        if self.freq.max() < other.freq.min():
            new_data = np.hstack((self.data, other.data))
            new_time = self.time
            new_freq = np.concatenate((self.freq, other.freq))
        else:
            new_data = np.hstack((other.data, self.data))
            new_time = self.time
            new_freq = np.concatenate((other.freq, self.freq))

        return SpecData(
            data=new_data,
            time=new_time,
            freq=new_freq,
            stokes=self.meta['stokes']
            )


    def __or__(self, other):
        """ Concatenate two SpecData in time
        """
        if not isinstance(other, SpecData):
            raise TypeError(
                'Trying to concatenate something else than SpecData'
                )
        if 'stokes' in self.meta.keys():
            if self.meta['stokes'] != other.meta['stokes']:
                raise ValueError(
                    'Inconsistent Stokes parameters'
                    )

        if self.time.max() < other.time.min():
            new_data = np.vstack((self.data, other.data))
            new_time = Time(np.concatenate((self.time, other.time)))
            new_freq = self.freq
        else:
            new_data = np.vstack((other.data, self.data))
            new_time = Time(np.concatenate((self.time, other.time)))
            new_freq = self.freq

        return SpecData(
            data=new_data,
            time=new_time,
            freq=new_freq,
            stokes=self.meta['stokes']
            )


    def __add__(self, other):
        """ Add two SpecData
        """
        if isinstance(other, SpecData):
            self._check_conformity(other)
            add = other.amp
        else:
            self._check_value(other)
            add = other 

        return SpecData(
            data=self.amp + add,
            time=self.time,
            freq=self.freq,
            stokes=self.meta['stokes']
            )


    def __sub__(self, other):
        """ Subtract two SpecData
        """
        if isinstance(other, SpecData):
            self._check_conformity(other)
            sub = other.amp
        else:
            self._check_value(other)
            sub = other 

        return SpecData(
            data=self.amp - sub,
            time=self.time,
            freq=self.freq,
            stokes=self.meta['stokes']
            )


    def __mul__(self, other):
        """ Multiply two SpecData
        """
        if isinstance(other, SpecData):
            self._check_conformity(other)
            mul = other.amp
        else:
            self._check_value(other)
            mul = other 

        return SpecData(
            data=self.amp * mul,
            time=self.time,
            freq=self.freq,
            stokes=self.meta['stokes']
            )


    def __truediv__(self, other):
        """ Divide two SpecData
        """
        if isinstance(other, SpecData):
            self._check_conformity(other)
            div = other.amp
        else:
            self._check_value(other)
            div = other 

        return SpecData(
            data=self.amp / div,
            time=self.time,
            freq=self.freq,
            stokes=self.meta['stokes']
            )


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
    def fmean(self, freq1=None, freq2=None, method='mean'):
        """ Average over the frequency.
            
            Parameters
            ----------
            freq1 : float
                Lower frequency bound in MHz.

            freq2 : float
                Upper frequency bound in MHz.

            method : str
                Method used to average (either 'mean' or 'median')

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

        average = np.mean(data, axis=1)\
            if method == 'mean'\
            else np.median(data, axis=1)

        return SpecData(
            data=np.expand_dims(average, axis=1),
            time=self.time.copy(),
            freq=np.expand_dims(np.mean(self.freq[fmask]), axis=0),
            stokes=self.meta['stokes']
            )


    def frebin(self, bins):
        """
        """
        bins = int(bins)

        slices = np.linspace(
            0,
            self.freq.size,
            bins + 1,
            True
        ).astype(np.int)
        counts = np.diff(slices)
        return SpecData(
            data=np.expand_dims(np.add.reduceat(self.amp, slices[:-1]) / counts, axis=0),
            time=self.time.copy(),
            freq=np.add.reduceat(self.freq, slices[:-1]) / counts,
            stokes=self.meta['stokes']
            )


    def tmean(self, t1=None, t2=None, method='mean',):
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
        average = np.mean(self.data[tmask, :], axis=0)\
            if method == 'mean'\
            else np.median(self.data[tmask, :], axis=0)
        return SpecData(
            data=np.expand_dims(average, axis=0),
            time=Time(np.array([tmasked[0] + dt/2.])),
            freq=self.freq.copy(),
            stokes=self.meta['stokes']
            )


    def background(self):
        """ Compute the median background
        """
        specf = self.fmean(method='median')
        spect = self.tmean(method='median')
        bkg = np.ones(self.amp.shape)
        bkg *= specf.amp[:, np.newaxis] * spect.amp[np.newaxis, :]
        return SpecData(
            data=bkg,
            time=self.time.copy(),
            freq=self.freq.copy(),
            stokes=self.meta['stokes']
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


    def bg_remove(self):
        """
        """
        bg = self.background()
        return SpecData(
            data=self.amp,
            time=self.time,
            freq=self.freq,
            stokes=self.meta['stokes']
            ) - bg


    # --------------------------------------------------------- #
    # ----------------------- Internal ------------------------ #
    def _check_conformity(self, other):
        """ Checks that other if of same type, same time, 
            frequency ans Stokes parameters than self
        """
        if self.meta['stokes'] != other.meta['stokes']:
            raise ValueError(
                'Different Stokes parameters'
                )

        if self.amp.shape != other.amp.shape:
            raise ValueError(
                'SpecData objects do not have the same dimensions'
                )

        if self.time != other.time:
            raise ValueError(
                'Not the same times'
                )

        if self.freq != other.freq:
            raise ValueError(
                'Not the same frequencies'
                )

        return


    def _check_value(self, other):
        """ Checks that other can be operated with self if
            other is not a SpecData object
        """
        if isinstance(other, np.ndarray):
            if other.shape != self.amp.shape:
                raise ValueError(
                    'Shape mismatch'
                )
        elif isinstance(other, (int, float)):
            pass
        else:
            raise Exception(
                'Operation unknown with {}'.format(type(other))
            )
        return
# ============================================================= #


