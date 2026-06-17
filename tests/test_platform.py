from pygitgo.utils.platform import get_platform


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
    mocker.patch('pygitgo.utils.platform.is_termux', return_value=False)

    result = get_platform()
    assert result == 'linux'


def  test_get_platform_on_termux(mocker):
    mocker.patch('platform.system', return_value='Linux')
    mocker.patch('pygitgo.utils.platform.is_termux', return_value=True)
    
    result = get_platform()
    assert result == 'termux'


def test_open_url_browser(mocker):
    mocker.patch("pygitgo.utils.platform.is_termux", return_value=False)
    mock_open = mocker.patch("webbrowser.open", return_value=True)
    mocker.patch("pygitgo.utils.platform.info")

    from pygitgo.utils.platform import open_url
    open_url("https://example.com")
    mock_open.assert_called_once_with("https://example.com")


def test_open_url_termux(mocker):
    mocker.patch("pygitgo.utils.platform.is_termux", return_value=True)
    mocker.patch("shutil.which", return_value="/usr/bin/termux-open")
    mock_run = mocker.patch("subprocess.run")
    mocker.patch("pygitgo.utils.platform.info")

    from pygitgo.utils.platform import open_url
    open_url("https://example.com")
    mock_run.assert_called_once_with(["termux-open", "https://example.com"], check=False)


def test_open_url_failure(mocker):
    mocker.patch("pygitgo.utils.platform.is_termux", return_value=False)
    mocker.patch("webbrowser.open", side_effect=Exception("browser error"))
    mock_warning = mocker.patch("pygitgo.utils.platform.warning")
    mocker.patch("pygitgo.utils.platform.info")

    from pygitgo.utils.platform import open_url
    open_url("https://example.com")
    mock_warning.assert_called_once_with("Could not open browser automatically.")
