import pytest
import os.path

test_dir = 'test_data/'


@pytest.mark.skip(reason="plotting library")
def test_plotting():
    """Tests plotting functionality of HRMonitor
    """

    from hrmonitor import HRMonitor
    hr = HRMonitor(get_test_file(1))
    hr.plot_data()


@pytest.mark.skip(reason="helper function")
def get_test_file(index):
    """Provides path to files such as test_data2.csv or test_data6.csv
    
    :param index: number of the file to retrieve
    :return: path for file of the format test_data<number>.csv
    """

    return os.path.join(test_dir,
                        'test_data{}.csv'.format(index))


def test_init():
    """Basic test to see if calling the constructor works
    """
    from hrmonitor import HRMonitor
    HRMonitor(get_test_file(1))


def test_file_not_found():
    """Test for checking how the class handles files that do not exist
    """
    with pytest.raises(FileNotFoundError):
        from hrmonitor import HRMonitor
        HRMonitor('./file-that-does-not-exist.csv')


def test_filetype():
    """Test for checking if the class correctly identifies unsupported file types
    """
    from hrmonitor import HRMonitor
    unsupported_filetypes = ['', '.', '.json', '.not-a-real-file-type']
    for f in unsupported_filetypes:
        with pytest.raises(ValueError):
            HRMonitor('fake-file' + f)


def test_json():
    """Checks if json file is created and has correct values
    """
    from hrmonitor import HRMonitor
    from json import dumps, load

    input_path = os.path.join(test_dir, 'sample.csv')
    json_path = os.path.join(test_dir, 'sample.json')

    if(os.path.isfile(json_path)):
        os.remove(json_path)
    assert not os.path.isfile(json_path)
    HRMonitor(input_path)
    assert os.path.isfile(json_path)

    json_values = dict({
        "peak_interval": 6.0,
        "mean_hr_bpm": 10.0,
        "voltage_extremes": [0.0, 0.9],
        "duration": 5.0,
        "num_beats": 0,
        "beats": []
    })

    # make sure that the json values are the same
    with open(json_path, 'r') as f:
        json_compare = load(f)
        assert json_values == json_compare


# testing for attributes
def test_voltage_extremes():
    """Checks if voltage extremes are correctly calculated
    """
    from hrmonitor import HRMonitor
    hr = HRMonitor(os.path.join(test_dir, 'sample.csv'))
    assert(hr.voltage_extremes == (0.0, 0.9))


def test_duration():
    """Checks if duration is calculated correctly
    """
    from hrmonitor import HRMonitor
    hr = HRMonitor(os.path.join(test_dir, 'sample.csv'))
    assert(hr.duration == 5)


def test_basic_files():
    """Test to see if all basic files in test_data/ can be processed (tests 1-27)
    """
    from hrmonitor import HRMonitor
    for i in range(27):
        HRMonitor(get_test_file(i + 1))


def test_fixable_files(caplog):
    """Test to see if all files with invalid inputs (tests 28-31) are handled correctly (invalid values detected and interpolated, without throwing exceptions)
    """
    from hrmonitor import HRMonitor
    for i in range(27, 31):
        HRMonitor(get_test_file(i + 1))
        assert 'Invalid values encountered' in caplog.text
        caplog.clear()


def test_outside_range(caplog):
    """Test if files with inputs outside the normal range are noted in the logs (test_data32.csv)
    """
    from hrmonitor import HRMonitor
    HRMonitor(get_test_file(32))
    assert 'Voltage values outside of typical range' in caplog.text


def test_broken_files(caplog):
    """Tests files with possible issues
    """
    from hrmonitor import HRMonitor

    # empty file
    with pytest.raises(ValueError):
        HRMonitor(os.path.join(test_dir, 'broken1.csv'))
    assert 'No data values present' in caplog.text
    caplog.clear()

    # file with more than 2 elements per line
    with pytest.raises(ValueError):
        HRMonitor(os.path.join(test_dir, 'broken2.csv'))
    assert 'Too many values on line 2' in caplog.text
    caplog.clear()

    # files that cannot be repaired via interpolation
    for i in range(3):
        with pytest.raises(RuntimeError):
            HRMonitor(os.path.join(test_dir, 'broken_int{}.csv'.format(i)))
        assert 'Interpolated repair failed for line {}'.format(i + 1) in caplog.text
