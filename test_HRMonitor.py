import pytest

test_files_path = 'test_data/'


@pytest.mark.skip(reason="helper function")
def get_test_file(index):
    return test_files_path + 'test_data' + str(index) + '.csv'


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


if __name__ == '__main__':
    test_init()
