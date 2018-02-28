"""Heart Rate Monitor Module
"""
import os.path
import json
import numpy as np
from matplotlib import pyplot as plt
from scipy import signal
import logging

logging.basicConfig(filename='hrmonitor.log',
                    filemode='w',
                    level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger(__name__)


class HRMonitor:
    """Class for processing ECG data into heart rate parameters
    """

    def __init__(self, file_path, time_units=1):
        """Reads in ECG data from given csv file and processes it into various attributes
        
        :param file_path: file path to csv file
        :param time_units: units of time for data (relative to seconds), default is seconds, e.g. for milliseconds, time_units would be 0.001
        """
        # extract data from .csv file and cast to float
        dh = DataHandler(file_path)
        float_data = [[float(s) for s in entry] for entry in dh.data]
        self.path = dh.path

        # transpose data and get time/voltage lists
        self.data = np.array(float_data).T
        self.time = self.data[0]
        self.voltage = self.data[1]
        
        # determine calculated attributes
        self.perform_autocorrel()

        # self.voltage_extremes = self.get_voltage_extremes()
        # self.beats = self.locate_beats()
        # self.num_beats = self.beats.size
        # self.duration = self.get_duration()
        # self.duration_in_min = (self.duration * time_units) / 60
        # self.mean_hr_bpm = self.num_beats / self.duration_in_min
        
        self.export_JSON('{}.json'.format(self.path))

    def perform_autocorrel(self):
        raw_corrl = np.correlate(self.voltage, self.voltage, mode='full')
        correl = raw_corrl[raw_corrl.size // 2:]
        
        plt.figure(figsize=(12, 3))  # wide figure
        plt.plot(correl, 'b-')
        plt.show()

    def locate_beats(self):
        """Locates the heart beats in the signal using the QRS (Pan-Tompkins) algorithm
        
        :return: numpy array with approximate locations of beats
        """
        
        # bandpass filter (5-12 Hz passband)
        b, a = signal.butter(6, [0.1, 0.8], btype='bandpass')
        filtered_data = signal.lfilter(b, a, self.voltage)

        # squaring the data
        squared_data = np.square(filtered_data)

        # locate beats
        peaks = signal.find_peaks_cwt(
            squared_data, np.arange(1, 5))

        plt.figure(figsize=(12, 3))  # wide figure
        plt.plot(self.time[peaks], self.voltage[peaks], 'ro')
        plt.plot(self.time, squared_data, 'b-')
        plt.show()

        return self.time[peaks]

    def get_voltage_extremes(self):
        """Gets the min and max of the voltage signal
        
        :return: tuple of the (min, max) for voltage
        """
        logger.info('Calculating voltage extremes.')
        extremes = (min(self.voltage), max(self.voltage))
        logger.info('Voltage extremes are {}.'.format(extremes))
        return extremes
    
    def get_duration(self):
        """Calculates the time duration of the ECG signal
        
        :return: difference between the first and last time value
        """
        logger.info('Calculating duration.')
        duration = self.time[-1] - self.time[0]
        logger.info('Duration of signal is {}.'.format(duration))
        return duration

    def plot_data(self):
        """Plots ECG data and calculated attributes
        """
        plt.figure(figsize=(12, 3))  # wide figure
        plt.plot(self.time, self.voltage)
        plt.xlabel('Time')
        plt.ylabel('Voltage')
        plt.title('ECG Voltage Data')
        logger.info('Plotting data.')
        plt.savefig('{}.png'.format(self.path),
                    bbox_inches='tight',
                    dpi=200)

    def export_JSON(self, file_path):
        """Exports calculated attributes to a json file
        
        :param file_path: json file path to export to
        """
        # first, create a dict with the attributes
        dict_with_data = {
            'mean_hr_bpm': self.mean_hr_bpm,
            'voltage_extremes': self.voltage_extremes,
            'duration': self.duration,
            'num_beats': self.num_beats,
            'beats': self.beats.tolist(),
        }

        # convert dict to json, and write it to file
        logger.info('Saving data to JSON file.')
        json_with_data = json.dumps(dict_with_data, sort_keys=False)
        with open(file_path, 'w') as f:
            f.write(json_with_data)
        
        logger.info('Data saved to {}.'.format(file_path))


class DataHandler:
    """Class for importing and packaging data
    """

    def __init__(self, file_path):
        """Reads in arbitrary data files
        
        :param file_path: file path to data file
        """
        self.data = None
        self.path = self.remove_file_type(file_path)
        
        file_type = self.get_file_type(file_path)
        if file_type == '.csv':
            self.data = self.csvReader(file_path)
        else:
            raise ValueError('File type is unsupported')

    def csvReader(self, file_path):
        """Reads in a .csv file into a list of lists
        
        :param file_path: file path to .csv file
        :return dictionary of data values
        """
        data = []
        logger.info('Reading data from {}.'.format(file_path))
        with open(file_path) as f:
            for line in f:
                raw_string = line.strip()
                data.append(raw_string.split(','))

        logger.info('Finished reading data from {}.'.format(file_path))
        return data

    def remove_file_type(self, file_path):
        """Removes the file extension from a path, useful for saving in same location with different file type
        
        :param file_path: path to file
        :return: path to file without the extension
        """
        return os.path.splitext(file_path)[0]

    def get_file_type(self, file_path):
        """Extracts the file extension from a path
        
        :param file_path: path to file
        :return: extension of file (with the dot)
        """
        return os.path.splitext(file_path)[1]
