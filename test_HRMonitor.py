import pytest
import os.path

test_dir = 'test_data/'


@pytest.mark.skip(reason="plotting library")
def test_plotting():
    from hrmonitor import HRMonitor
    hr = HRMonitor(get_test_file(1))
    hr.plot_data()


@pytest.mark.skip(reason="helper function")
def get_test_file(index):
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


if __name__ == '__main__':
    test_plotting()
