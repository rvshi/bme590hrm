# HRMonitor

## Heart Rate Monitor Post-Processing

[![Build Status](https://travis-ci.org/rvshi/bme590hrm.svg?branch=master)](https://travis-ci.org/rvshi/bme590hrm) [![Documentation Status](https://readthedocs.org/projects/hrmonitor/badge/?version=latest)](https://hrmonitor.readthedocs.io/en/latest/?badge=latest)


__Developed By:__ Harvey Shi (@rvshi)

__Course:__ Duke BME 590-05 Medical Software Design (Spring 2018)

## Overview

This project defines a Python 3 class, `HRMonitor`, for processing ECG data.
- In order to parse the data, a custom `DataHandler` class is used, to allow further extensibility in the future.
- After being parsed, the data is analyzed internally by the module to determine useful attributes such as heart rate or duration of signal.
- For more detailed information on the individual class methods, see the [documentation website](https://hrmonitor.readthedocs.io/en/latest/?badge=latest).
## Usage

- First, you want to [set up a Python virtual environment](https://docs.python.org/3/tutorial/venv.html) and install the packages in `requirements.txt`.
- Next, you can import the `HRmonitor` class from `hrmonitor.py` and start using this module in your code.
- Here is a basic example of usage, which you can run from the root directory of this repo:

```python
from hrmonitor import HRMonitor
hr = HRMonitor('./test_data/test_data1.csv')
hr.plot_data()
```
- Some important notes
    - Input ECG data should be in `.csv` format.
    - Only two float values should be present on each line of the `.csv`, in this order: `time, voltage`.
    - The units for time should be specified by setting the `time_units` argument in the HRMonitor constructor function.
        - The default units is seconds.
        - `time_units` is a float representing the new unit of time in terms of seconds.
        - For example, if the units were milliseconds, you would specify this as:
    - Example ECG files can be found in the `test_data/` directory.
 
```python
HRMonitor('./file.csv', time_units = 0.001)
```

## Features
- Calculates several class attributes from the data:
  - `time`: numpy vector of the time data
  - `voltage`: numpy vector of the voltage data
  - `peak_interval`: interval between peaks in seconds, as estimated via autocorrelation of the signal
  - `mean_hr_bpm`: average heart rate (in bpm) over the signal
  - `voltage_extremes`: tuple of the (min, max) of the voltage data
  - `duration`: total length of the signal in seconds
  - `beats`: numpy array with the approximate time locations of heart beats via peak detection following a bandpass filter
  - `num_beats`: estimated number of beats in the data, taken as the length of `beats`
- Exports some calculated attributes as a JSON file with the same name as the input `.csv`.
    - `time` and `voltage` are not exported since they are already in archival format
- Can be used to generate plots of the data using the `plot_data()` method.

## Other notes
The current module has only been tested with Python 3.6.4 on MacOS 10.13
