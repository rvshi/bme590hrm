"""Heart Rate Monitor Module
"""
import os.path
import json
import numpy as np
from matplotlib import pyplot as plt
import time


class HRMonitor:
    """Class for processing ECG data into heart rate parameters
    """

    def __init__(self, file_path):
        """Reads in ECG data from csv file and processes it
        
        :param file_path: file path to csv file
        """
        # extract data from .csv file and cast to float
        dh = DataHandler(file_path)
        float_data = [[float(s) for s in entry] for entry in dh.data]
        self.path = dh.path

        # transpose data and get time/voltage lists
        self.data = np.array(float_data).T.tolist()
        self.time = self.data[0]
        self.voltage = self.data[1]
        
        # determine calculated attributes
        self.mean_hr_bpm = 2
        self.voltage_extremes = self.get_voltage_extremes()
        self.duration = self.get_duration()
        self.num_beats = 5
        self.beats = 2

        self.export_JSON('{}.json'.format(self.path))

    def get_voltage_extremes(self):
        return(min(self.voltage), max(self.voltage))
    
    def get_duration(self):
        return self.time[-1] - self.time[0]

    def plot_data(self):
        """Plots ECG data and calculated attributes
        """
        plt.plot(self.time, self.voltage)
        plt.xlabel('Time')
        plt.ylabel('Voltage')
        plt.title('ECG Voltage Data')
        plt.savefig('{}.svg'.format(self.path), bbox_inches='tight')

    def export_JSON(self, file_path):
        dict_with_data = {
            'mean_hr_bpm': self.mean_hr_bpm,
            'voltage_extremes': self.voltage_extremes,
            'duration': self.duration,
            'num_beats': self.num_beats,
            'beats': self.beats,
        }

        # convert dict to json, and write it to file
        json_with_data = json.dumps(dict_with_data, sort_keys=False)
        with open(file_path, 'w') as f:
            f.write(json_with_data)


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
        with open(file_path) as f:
            for line in f:
                raw_string = line.strip()
                data.append(raw_string.split(','))

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
