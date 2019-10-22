# **nenupytf**

[![nenupy](https://img.shields.io/pypi/v/nenupytf.svg)](
    https://pypi.python.org/pypi/nenupytf)

<p align="center">
<img src="./Logo-NenuFAR-noir.svg" width="20%">
</p>

Python3 package to read and analyze [*NenuFAR*](https://nenufar.obs-nancay.fr/en/astronomer/) Time-Frequency data from *UnDySPuTeD*.

## Installation
`nenupytf` can be installed via `pip`, the recommended tool for installing Python packages:
```
pip install nenupytf
```
Keep you up-to-date with the latest release and get the newest functionalities by regularly updating the package:  
```
pip install nenupytf --upgrade
```

## Quickstart

### Observation informations
Prior to diving within the large data volume, one can quickly get a summary of the observation content with the command:
```
nenupytf-info --obs /path/to/observation_directory/
```
The output would look something like:
```
--------------- nenupytf ---------------
Info on /path/to/observation_directory/OBS_XXX_XXX_0.spectra
Lane: 0
Time: 2019-10-13T07:20:55.0000000 -- 2019-10-13T07:25:54.4404020
Frequency: 39.0625 -- 76.5625 MHz
Beams: [0]
----------------------------------------
```
displaying for each lane, the time and frequency range as well as the beam indices.

On can also display these informations on individual files by printing the instance of a `Lane` object:
```python
from nenupytf.read import Lane
l = Lane('OBS_XXX_XXX_0.spectra')
print(l)
```

### Selecting data
To select data from a specific file:
```python
from nenupytf.read import Lane
l = Lane('OBS_XXX_XXX_0.spectra')
time_select = ['2019-10-13 07:25:50.4404020', '2019-10-13 07:25:54.4404020']
freq_select = [50, 54.97]
spec = l.select(time=time_select, freq=freq_select, beam=0, stokes='I')
```
The `select()` methods, returns a `SpecData` object, storing the time (in `astropy.time.Time` format), the frequency in MHz, and the Dynamic Spectrum (which is a 2D array). Besides, a `SpecData` object enables several cleaning or analysis methods specific to dynamic spectra.

Averaging on time and frequency may allow to see a full picture of the data. However it may take some time to process!
```python
from nenupytf.read import Lane
l = Lane('OBS_XXX_XXX_0.spectra')
spec = l.average()
```
Of course, one can specify every parameter such as in the `select()` method. Besides, `average()` accepts `df` and `dt`, respectively the time bin (in seconds) and the frequency bin (in MHz):
```python
from nenupytf.read import Lane
l = Lane('OBS_XXX_XXX_0.spectra')
time_select = ['2019-10-13 07:25:50.4404020', '2019-10-13 08:00:00.000']
freq_select = [30, 60]
t, f, d = l.average(df=2, dt=3, time=time_select, freq=freq_select, beam=0, stokes='I')
```


### Command-line plot
To display a plot of the selection, simply run:
```
nenupytf-plot --obs /path/to/observation_directory/ --lane 0 --time 2019-10-13T07:25:50.4404020 2019-10-13T07:25:54.4404020 --freq 50 54.97 --stokes I
```