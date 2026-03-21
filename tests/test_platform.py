from pygitgo.utils.platform_utils import get_platform

def test_get_platform_on_windows(mocker):
    mocker.patch('platform.system', return_value='Windows')

    result = get_platform()
    assert result == 'windows'


def  test_get_platform_on_mac(mocker):
    mocker.patch('platform.system', return_value='Darwin')

    result = get_platform()
    assert result == 'macos'


def  test_get_platform_on_linux(mocker):
    mocker.patch('platform.system', return_value='Linux')
    mocker.patch('pygitgo.utils.platform_utils.is_termux', return_value=False)

    result = get_platform()
    assert result == 'linux'


def  test_get_platform_on_termux(mocker):
    mocker.patch('platform.system', return_value='Linux')
    mocker.patch('pygitgo.utils.platform_utils.is_termux', return_value=True)
    
    result = get_platform()
    assert result == 'termux'