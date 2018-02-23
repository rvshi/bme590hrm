import pytest


test_files_path = 'test_data/'


@pytest.mark.skip(reason="helper function")
def get_test_file(index):
    return test_files_path + 'test_data' + str(index) + '.csv'


def test_init():
    from hrmonitor import HRMonitor
    HRMonitor(get_test_file(1))


if __name__ == '__main__':
    test_init()