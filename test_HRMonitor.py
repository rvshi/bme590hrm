import pytest
import os.path

test_dir = 'test_data/'
log_file = 'hrmonitor.log'


@pytest.mark.skip(reason="plotting library")
def test_plotting():
    from hrmonitor import HRMonitor
    hr = HRMonitor(get_test_file(1))
    hr.plot_data()


@pytest.mark.skip(reason="helper function")
def get_test_file(index):
    return os.path.join(test_dir,
                        'test_data{}.csv'.format(index))


@pytest.mark.skip(reason="helper function")
def check_log_file(search_str):
    with open(log_file) as f:
        return search_str in f.read()


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


def test_fixable_files():
    """Test to see if all files with invalid inputs (tests 28-31) are handled correctly (invalid values detected and interpolated, without throwing exceptions)
    """
    from hrmonitor import HRMonitor
    for i in range(27, 31):
        HRMonitor(get_test_file(i + 1))
        assert check_log_file('Invalid values encountered')


def test_outside_range():
    """Test if files with inputs outside the normal range are noted in the logs (test_data32.csv)
    """
    from hrmonitor import HRMonitor
    HRMonitor(get_test_file(32))
    assert check_log_file('Voltage values outside of typical range')


def test_broken_files():
    """Tests files with possible issues
    """
    from hrmonitor import HRMonitor

    # empty file
    with pytest.raises(ValueError):
        HRMonitor(os.path.join(test_dir, 'broken1.csv'))
    assert check_log_file('No data values present')

    # file with more than 2 elements per line
    with pytest.raises(ValueError):
        HRMonitor(os.path.join(test_dir, 'broken2.csv'))
    assert check_log_file('Too many values on line 2')

    # files that cannot be repaired via interpolation
    for i in range(3):
        with pytest.raises(RuntimeError):
            HRMonitor(os.path.join(test_dir, 'broken_int{}.csv'.format(i)))
        assert check_log_file('Interpolated repair failed for line {}'.format(i + 1))
