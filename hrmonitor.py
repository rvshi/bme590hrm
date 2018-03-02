"""Heart Rate Monitor Python Module
"""
import os.path
import json
import numpy as np
from matplotlib import pyplot as plt
from scipy import signal
import logging

log_file_path = 'hrmonitor.log'
logging_config = dict(
    filename=log_file_path,
    filemode='w',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p'
)
data_config = logging_config.copy()
data_config['filename'] = 'datahandler.log'


class HRMonitor:
    """Class for processing ECG data into heart rate parameters
    """

    def __init__(self, file_path, time_units=1, voltage_units=1, window_size=10):
        """Reads in ECG data from given csv file and processes it into various attributes
        
        :param file_path: file path to csv file
        :param time_units: units of time for data (relative to seconds), default is 1, e.g. for milliseconds, time_units would be 0.001
        :param voltage_units: units of voltage for data (relative to mV), default is 1, e.g. for volts, voltage_units would be 1000
        :param window size for heart rate calculation, in units of seconds (see self.get_mean_hr()), defaults to 10 seconds
        """
        # setup logging
        logging.basicConfig(**logging_config)
        self.logger = logging.getLogger(__name__)
        self.logger.info('HRMonitor initialized...')

        # extract data from .csv file and cast to float
        dh = DataHandler(file_path)
        self.data = dh.data
        self.path = dh.path

        # validate data and get time/voltage lists
        self.time_units = time_units
        self.voltage_units = voltage_units
        (self.time, self.voltage) = self.parse_data(self.data)

        # determine basic attributes
        self.voltage_extremes = self.get_voltage_extremes()
        self.duration = self.get_duration()

        # first get interval over entire signal
        (self.peak_interval, self.interval_loc) = self.get_peak_interval(self.voltage)

        # then, get the heart rate over pre-specified chunks of time
        self.mean_hr_bpm = self.get_mean_hr(window_size)

        # beat position attributes
        self.peaks = self.locate_peaks()
        self.beats = np.empty(shape=(0, 0))
        if(self.peaks.size > 0):
            self.beats = self.time[self.peaks]
        self.num_beats = self.beats.size
        
        # export data
        self.export_JSON('{}.json'.format(self.path))
        self.logger.info('HRMonitor object created.')

    @staticmethod
    def is_float(input):
        """Check if string is a float and not NaN
        
        :param input: string to check
        :return: boolean indicating if the string is a float
        """
        try:
            float(input)
        except ValueError:
            return False
        return not input == 'NaN'

    def repair_line(self, line, line_num):
        """Attempts interpolated repair of line
        
        :param line: list of elements to repair
        :param line_num: line number in file, for finding position in data
        :raises RuntimeError: if unable to perform interpolation of values
        :return: float tuple of (time, voltage) as averaged between the previous and next lines
        """

        self.logger.warn('Invalid values encountered on line {}. Attempting interpolated repair...'.format(
            line_num + 1))

        # check if previous and next lines exist and are valid
        if(line_num > 0 and line_num < len(self.data) - 1):
            prev_line = self.data[line_num - 1]
            next_line = self.data[line_num + 1]

            prev_valid = len(prev_line) == 2 and self.is_float(
                prev_line[0]) and self.is_float(prev_line[1])
            next_valid = len(next_line) == 2 and self.is_float(
                next_line[0]) and self.is_float(next_line[1])

            # if conditions are met, perform repair
            if(prev_valid and next_valid):
                time_val = (float(prev_line[0]) + float(next_line[0])) / 2
                voltage_val = (float(prev_line[1]) + float(next_line[1])) / 2

                self.logger.info('Interpolation successfully produced ({:0.3}, {:0.3}).'.format(
                    time_val, voltage_val))
                return (time_val, voltage_val)

        err_msg = 'Interpolated repair failed for line {}.'.format(
            line_num + 1)
        self.logger.error(err_msg)
        raise RuntimeError(err_msg)

    def parse_line(self, line, line_num):
        """Parses a single line into the float tuple of (time, voltage), throws exceptions as necessary
        
        :param line: list of elements to parse
        :param line_num: line number in file, for tracking exceptions
        :raises ValueError: if there are more or less than two elements per line
        :return: float tuple of (time, voltage)
        """
        if(len(line) != 2):
            err_msg = 'Too many values on line {}.'.format(line_num + 1)
            self.logger.error(err_msg)
            raise ValueError(err_msg)

        elif(any([not self.is_float(v) for v in line])):
            return(self.repair_line(line, line_num))

        return (float(line[0]), float(line[1]))

    def parse_data(self, data):
        """Validate and sanitize input data, parse valid lines as floats, also performs unit standardization
        
        :param data: list containing the input data to check
        :raises ValueError: if data is empty
        :return: tuple of numpy arrays (time [s], voltage [mV])
        """
        self.logger.info('Validating data...')
        
        if(len(data) == 0):
            err_msg = 'No data values present.'
            self.logger.error(err_msg)
            raise ValueError(err_msg)

        time = []
        voltage = []
        outside_range = False
        for i, line in enumerate(data):
            (time_val, voltage_val) = self.parse_line(line, i)
            time.append(time_val)
            voltage.append(voltage_val)

            # check if value is outside range
            if(not outside_range and abs(voltage_val) >= 300):
                outside_range = True
        
        if(outside_range):
            self.logger.warn('Voltage values outside of typical range of (-300, 300) mV.')

        self.logger.info('Data parsed. No errors found.')
        return (np.asarray(time) * self.time_units,
                np.asarray(voltage) * self.voltage_units)

    @staticmethod
    def moving_avg(data, n):
        """Calculates moving average of size n.

        Uses code from https://stackoverflow.com/questions/14313510/how-to-calculate-moving-average-using-numpy

        :param data: numpy vector to sum up
        :param n: size of moving average window, gets shrinkwrapped to size of vector
        :return: moving average for vector
        """
        n = min(n, data.size)
        cs = np.cumsum(data, dtype=float)
        cs[n:] = cs[n:] - cs[:-n]
        return cs[n - 1:] / n

    def get_peak_interval(self, data):
        """Determines interval between peaks using auto-correlation
        
        :param data: data interval to process into heart
        :return: tuple containing (interval size between ECG peaks in seconds, array index of interval location)
        """
        self.logger.info('Calculating interval between peaks...')
        # calculate autocorrelation and square the data
        raw_corrl = np.correlate(data, data, mode='full')
        correl = raw_corrl[raw_corrl.size // 2:]
        sq_cor = np.square(correl)

        # find position after first peak (DC)
        after_peak = 0
        prev = sq_cor[0]
        for i in range(sq_cor.size):
            if(sq_cor[i] <= prev):
                after_peak = i
                prev = sq_cor[i]
            else:
                break

        # find position of 2nd peak to get interval between peaks
        interval_loc = after_peak + np.argmax(sq_cor[after_peak:], axis=0)
        interval_val = self.time[interval_loc]
        self.logger.info('Interval between peaks is {}.'.format(interval_val))
        return (interval_val, interval_loc)

    def get_mean_hr(self, window_size):
        """Determines heart rate (bpm) for block chunks
        
        :param window_size: size of window to determine heart rate for
        :return: numpy vector of heart rate for each block interval
        """

        self.logger.info('Calculating mean heart rate...')
        heart_rates = []
        prev_index = 0
        prev_time = self.time[prev_index]
        for i, time in enumerate(self.time):
            if(time >= window_size + prev_time):
                (int_val, int_loc) = self.get_peak_interval(
                    self.voltage[prev_index:i])

                heart_rate = (60 / int_val).round(5)
                heart_rates.append(heart_rate)

                prev_index = i
                prev_time = time
        
        self.logger.info(
            'Heart rates determined for {} blocks'.format(len(heart_rates)))
        return np.asarray(heart_rates)

    def locate_peaks(self):
        """Locates the heart beats in the signal
        
        :return: numpy array with approximate locations of beats given as indices of the time array
        """
        self.logger.info('Locating peaks...')
        # bandpass filter (6th order Butterworth filter)
        b, a = signal.butter(6, [0.1, 0.8], btype='bandpass')
        filtered_data = signal.lfilter(b, a, self.voltage)

        # squaring the data
        sq_data = np.square(filtered_data)

        # locate beats
        beat_width = 5
        widths = np.arange(beat_width, beat_width * 2)
        peaks = signal.find_peaks_cwt(
            sq_data, widths=widths)

        if(peaks.size == 0):
            self.logger.warning('No peaks located.')
        else:
            # filter through and remove peaks that are too close to each other
            filtered_peaks = []
            num_peaks = len(peaks)
            thre_width = self.interval_loc // 4  # threshold width
            i = 0
            while i < (num_peaks - 1):
                current_peak = peaks[i]
                filtered_peaks.append(current_peak)
                i += 1
                for j in range(i, num_peaks):
                    i = j
                    if((peaks[j] - current_peak) > thre_width):
                        break
            
            peaks = np.asarray(filtered_peaks)
            self.logger.info('{} peaks located.'.format(peaks.size))

        return peaks

    def get_voltage_extremes(self):
        """Gets the min and max of the voltage signal
        
        :return: tuple of the (min, max) for voltage
        """
        self.logger.info('Calculating voltage extremes...')
        extremes = (min(self.voltage), max(self.voltage))
        self.logger.info('Voltage extremes are {}.'.format(extremes))
        return extremes
    
    def get_duration(self):
        """Calculates the time duration of the ECG signal
        
        :return: difference between the first and last time value
        """
        self.logger.info('Calculating duration...')
        duration = self.time[-1] - self.time[0]
        self.logger.info('Duration of signal is {}.'.format(duration))
        return duration

    def plot_data(self):
        """Plots ECG data and calculated attributes and saves it as a .png file with the same name as the input .csv.
        """
        self.logger.info('Plotting data...')
        plt.figure(figsize=(12, 3))  # wide figure

        # plot detected beats
        if(self.num_beats > 0):
            for beat_loc in self.beats:
                plt.axvline(x=beat_loc,
                            color='r',
                            linestyle='--')

        plt.plot(self.time, self.voltage, 'b-')
        plt.xlabel('Time [s]')
        plt.ylabel('Voltage [mV]')
        plt.title('ECG Signal')

        plt_path = '{}.png'.format(self.path)
        plt.savefig(plt_path,
                    bbox_inches='tight',
                    dpi=200)
        self.logger.info('Data plotted and saved to {}.'.format(plt_path))

    def export_JSON(self, file_path):
        """Exports calculated attributes to a json file
        
        :param file_path: json file path to export to
        """
        # first, create a dict with the attributes
        dict_with_data = {
            'peak_interval': round(self.peak_interval, 3),
            'mean_hr_bpm': self.mean_hr_bpm.tolist(),
            'voltage_extremes': self.voltage_extremes,
            'duration': self.duration,
            'num_beats': self.num_beats,
            'beats': self.beats.tolist(),
        }

        # convert dict to json, and write it to file
        self.logger.info('Saving data to JSON file...')
        json_with_data = json.dumps(dict_with_data, sort_keys=False)
        with open(file_path, 'w') as f:
            f.write(json_with_data)
        
        self.logger.info('Data saved to {}.'.format(file_path))


class DataHandler:
    """Class for importing and packaging data
    """

    def __init__(self, file_path):
        """Reads in arbitrary data files
        
        :param file_path: file path to data file
        """
        # setup logging
        logging.basicConfig(**data_config)
        self.logger = logging.getLogger(__name__)
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
        self.logger.info('Reading data from {}.'.format(file_path))
        with open(file_path) as f:
            for line in f:
                raw_string = line.strip()
                data.append(raw_string.split(','))

        self.logger.info('Finished reading data from {}.'.format(file_path))
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
