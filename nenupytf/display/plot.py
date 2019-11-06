#! /usr/bin/python3
# -*- coding: utf-8 -*-


__author__ = ['Alan Loh']
__copyright__ = 'Copyright 2019, nenupytf'
__credits__ = ['Alan Loh']
__maintainer__ = 'Alan Loh'
__email__ = 'alan.loh@obspm.fr'
__status__ = 'Production'
__all__ = [
    'plot',
    'plotdb'
    ]


import matplotlib.pyplot as plt
import numpy as np
 

def plot(specdata, savefile=None):
    """
    """
    pcm = plt.pcolormesh(
        (specdata.time - specdata.time[0]).sec,
        specdata.freq,
        specdata.amp.T,
        vmin=np.percentile(specdata.amp, 5),
        vmax=np.percentile(specdata.amp, 95),
        cmap='YlGnBu_r')
    
    cbar = plt.colorbar(pcm)
    
    cbar.set_label('Stokes {} (amp)'.format(specdata.meta['stokes']))
    plt.ylabel('Frequency (MHz)')
    plt.xlabel('Time (sec since {})'.format(specdata.time[0].isot))
    
    if savefile is None:
        plt.show()
    else:
        plt.savefig(savefile)
    return


def plotdb(specdata, savefile=None):
    """
    """
    pcm = plt.pcolormesh(
        (specdata.time - specdata.time[0]).sec,
        specdata.freq,
        specdata.db.T,
        vmin=np.percentile(specdata.db, 5),
        vmax=np.percentile(specdata.db, 95),
        cmap='YlGnBu_r')
    
    cbar = plt.colorbar(pcm)
    
    cbar.set_label('Stokes {} (dB)'.format(specdata.meta['stokes']))
    plt.ylabel('Frequency (MHz)')
    plt.xlabel('Time (sec since {})'.format(specdata.time[0].isot))
    
    if savefile is None:
        plt.show()
    else:
        plt.savefig(savefile)
    return

